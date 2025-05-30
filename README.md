# Voice Server Agent

This project implements a voice agent for LiveKit, integrating speech-to-text (STT), large language model (LLM), and text-to-speech (TTS) services, with custom instructions fetched from an MCP server. The agent is designed to join LiveKit rooms, process audio, and interact with callers in real time.

## Features

- **LiveKit integration** for real-time audio/video rooms.
- **Deepgram** for Turkish speech-to-text.
- **OpenAI GPT-4.1-mini** for language understanding and response generation.
- **ElevenLabs** for Turkish text-to-speech.
- **MCP server** for dynamic agent instructions and tool calls.
- **Voice activity detection** and **turn detection** for natural conversation flow.

---

## Prerequisites

- Python 3.8+
- Access to the following APIs/services:
  - LiveKit Cloud
  - Deepgram API
  - OpenAI API
  - ElevenLabs API
  - MCP server (custom)

---

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/samkaraca/mis48b-term-project-voice-server
   cd voice-server
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

1. **Create a `.env` file in the project root:**

   Example:

   ```
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret
   LIVEKIT_URL=wss://your-livekit-server-url
   DEEPGRAM_API_KEY=your_deepgram_api_key
   OPENAI_API_KEY=your_openai_api_key
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   MCP_SERVER_URL=https://your-mcp-server-url
   ```

   - Replace the values with your actual credentials and endpoints.

---

## Running the Agent

You can run the agent in two modes:

### 1. Console Mode

Start the agent and interact with it directly in your terminal:

```bash
python agent.py console
```

- The voice AI agent will start a conversation with you on the console, allowing you to test and interact without connecting to LiveKit or telephony infrastructure.

### 2. LiveKit Worker Mode (for SIP Trunk Integration)

Start the agent as a worker for LiveKit, ready to handle real calls:

```bash
python agent.py dev
```

- This creates a worker and registers it with your LiveKit server.
- With your inbound SIP trunk configured, LiveKit will route incoming calls from your telephony operator to this worker.
- The agent will join the appropriate room and handle the call using the AI pipeline.

- Logs will be printed to the console for connection status and agent actions in both modes.

---

## Customization

- **Agent Instructions:**  
  The agent fetches its instructions dynamically from the MCP server based on the caller's number.
- **Plugins:**  
  You can swap out or configure STT, LLM, and TTS plugins in `agent.py` as needed.
- **Event Handling:**  
  The agent sends a conversation summary to the MCP server when a participant disconnects.

---

## Troubleshooting

- Ensure all API keys and URLs are correct in your `.env` file.
- Check that all required Python packages are installed.
- If you encounter import errors for `livekit` or `mcp`, ensure you have the correct versions or custom packages installed.
