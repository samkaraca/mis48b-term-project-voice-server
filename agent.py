from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions, mcp
from livekit.plugins import openai, cartesia, silero  # import plugin modules
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import json
import os

# Load environment variables from .env file
load_dotenv()

# Define our Agent behavior
class Assistant(Agent):
    def __init__(self, caller_number=None):
        # Generate dynamic instructions with caller info (if provided)
        instructions = "Sen yardımcı bir asistansın."

        print(instructions)

        # Initialize the agent with our instructions
        super().__init__(instructions=instructions)

    

# The main entrypoint for the agent job
async def entrypoint(ctx: agents.JobContext):
    # Connect to LiveKit (establishes the agent's connection to LiveKit Cloud)
    await ctx.connect()
    
    # Get caller information if available
    caller_number = None

    try:
        room_metadata = json.loads(ctx.room.metadata) if ctx.room.metadata else {}
        caller_number = room_metadata.get('caller_number', '')
    except Exception as e:
        print(f"Error loading caller info: {e}")
    
    # Create a custom assistant with caller information
    assistant = Assistant(caller_number=caller_number)

    # Set up the voice AI pipeline with STT, LLM, and TTS plugins
    session = AgentSession(
        # Speech-to-Text: using Deepgram's streaming STT (language "en-US")
        stt = openai.STT(language="tr", model="gpt-4o-transcribe"),
        # Language Model: using OpenAI GPT-4 (requires OPENAI_API_KEY)
        llm = openai.LLM(model="gpt-4.1-mini"),
        # Text-to-Speech: using Cartesia TTS with default English voice
        tts = cartesia.TTS(language="tr", voice="bb2347fe-69e9-4810-873f-ffd759fe8420"),
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
        instructions="Arayanı selamla."
    )
    # The above line prompts the LLM to generate a greeting, which is then spoken out 
    # by the TTS automatically [oai_citation:17‡docs.livekit.io](https://docs.livekit.io/agents/start/telephony/#:~:text=Call%20the%20,session.start).

# Run the agent application (in development mode by default)
if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc = entrypoint,
            agent_name = "inbound-agent"  # This name must match the dispatch rule
        )
    )