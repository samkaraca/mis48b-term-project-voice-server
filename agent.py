from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions, mcp
from livekit.plugins import openai, cartesia, silero, deepgram, elevenlabs  # import plugin modules
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.rtc.room import ConnectionState, RemoteParticipant
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

import json
import os

# Load environment variables from .env file
load_dotenv()

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

class MCPToolCaller:
    def __init__(self, server_url):
        self.server_url = server_url
        self.session = None
        self._session_task = None
        self._session_ready = asyncio.Event()

    async def initialize(self):
        self._session_task = asyncio.create_task(self._run_session())

    async def _run_session(self):
        try:
            print(f"Connecting to {self.server_url}")
            async with sse_client(self.server_url) as (read_stream, write_stream):
                print("Connected via sse_client")
                async with ClientSession(read_stream, write_stream) as session:
                    print("Initializing session")
                    await session.initialize()
                    print("Session initialized")
                    self.session = session
                    self._session_ready.set()
                    try:
                        while True:
                            await asyncio.sleep(3600)
                    except asyncio.CancelledError:
                        print("Session cancelled")
                        self.session = None
        except Exception as e:
            print(f"Error in _run_session: {e}")
            self._session_ready.set()

    async def call_tool(self, tool_name, args):
        await self._session_ready.wait()
        if not self.session:
            raise ValueError("Session not initialized or closed.")
        return await self.session.call_tool(tool_name, args)

    async def get_prompt(self, prompt_name, arguments=None):
        await self._session_ready.wait()
        if not self.session:
            raise ValueError("Session not initialized or closed.")
        return await self.session.get_prompt(prompt_name, arguments or {})

    async def close(self):
        if self._session_task:
            self._session_task.cancel()
            await self._session_task

# Define our Agent behavior
class Assistant(Agent):
    def __init__(self):
        # Initialize the agent with our instructions
        super().__init__(instructions="")

def extract_caller_number(ctx: agents.JobContext):
    room_name = ctx.room.name  # e.g., "call_+905535235961_mMAhVe4E6hTs"
    parts = room_name.split('_')
    if len(parts) >= 3:
        phone_number = parts[1]
        return phone_number
    else:
        return "+111111111111"

# The main entrypoint for the agent job
async def entrypoint(ctx: agents.JobContext):
    # Connect to LiveKit (establishes the agent's connection to LiveKit Cloud)
    await ctx.connect()

    room = ctx.room

    mcp_tool_caller = MCPToolCaller(os.getenv("MCP_SERVER_URL"))
    await mcp_tool_caller.initialize()
    mcp_prompt_response = await mcp_tool_caller.get_prompt("instructions", {"callerNumber": extract_caller_number(ctx)})
    instructions = mcp_prompt_response.messages[0].content.text
    print("[MCP] Instructions: ", instructions)

    # Create a custom assistant with caller information
    assistant = Assistant()

    # Set up the voice AI pipeline with STT, LLM, and TTS plugins
    session = AgentSession(
        # Speech-to-Text: using Deepgram's streaming STT (language "en-US")
        stt = deepgram.STT(language="tr", model="nova-2-general"),
        # Language Model: using OpenAI GPT-4 (requires OPENAI_API_KEY)
        llm = openai.LLM(model="gpt-4.1-mini"),
        # Text-to-Speech: using Cartesia TTS with default English voice
        tts = elevenlabs.TTS(language="tr", model="eleven_flash_v2_5"),
        # (Optional: you could add voice activity detection or noise cancellation here)
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        mcp_servers=[
            mcp.MCPServerHTTP(
                os.getenv("MCP_SERVER_URL")
            ),
        ]
    )

    # Start the agent session in the current LiveKit room with our Assistant agent
    await session.start(
        room = ctx.room,         # the LiveKit room the call is in
        agent = assistant,       # instance of our Assistant with caller information
        room_input_options = RoomInputOptions()  # using default audio handling
    )

    # (At this point, the agent is live in the room, listening and ready to respond)
    await session.generate_reply(
        instructions=instructions
    )

    @room.on("participant_disconnected")
    def on_participant_disconnected(_: RemoteParticipant):
        async def handle_disconnected():
            conversation = "\n".join(
                map(lambda item: f"{'kullanıcı' if item.role == 'user' else 'asistan'}: {item.content[0]}", session.history.items)
            )
            await mcp_tool_caller.call_tool(
                "send-summary-to-user",
                {"conversationText": conversation, "callerNumber": extract_caller_number(ctx)}
            )
            print("Participant disconnected")
        asyncio.create_task(handle_disconnected())

# Run the agent application (in development mode by default)
if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc = entrypoint,
            agent_name = "inbound-agent"  # This name must match the dispatch rule
        )
    )