# GAIA Command Line Interface (CLI)

GAIA (Generative AI Acceleration Infrastructure & Applications) provides a command-line interface (CLI) for easy interaction with AI models and agents. The CLI allows you to query models directly, manage chat sessions, and access various utilities without writing code.

## GAIA-CLI Getting Started Guide

1. Make sure to follow the [Getting Started Guide](../README.md#getting-started-guide) to install the `gaia-cli` tool.

2. GAIA automatically configures optimal settings for Ryzen AI hardware.

3. Once installed, double click on the desktop icon **GAIA-CLI** to launch the command-line shell with the GAIA environment activated.

4. The GAIA CLI connects to the Lemonade server for AI processing. Make sure the server is running by:
   - Double-clicking the desktop shortcut, or
   - Running: `lemonade-server serve`

5. Now try the direct LLM demo in the [GAIA-CLI LLM Demo](#gaia-cli-llm-demo) section, chat demo in the [GAIA-CLI Chat Demo](#gaia-cli-chat-demo) section, or talk demo in the [GAIA-CLI Talk Demo](#gaia-cli-talk-demo) section.

## GAIA-CLI LLM Demo

The fastest way to interact with AI models is through the direct LLM command:

1. Try a simple query:
   ```bash
   gaia-cli llm "What is 1+1?"
   ```

   This will stream the response directly to your terminal. The system will automatically check for the lemonade server and provide helpful error messages if it's not running.

2. Use advanced options:
   ```bash
   # Specify model and token limit
   gaia-cli llm "Explain quantum computing in simple terms" --model llama3.2:3b --max-tokens 200

   # Disable streaming for batch processing
   gaia-cli llm "Write a short poem about AI" --no-stream
   ```

3. If you get a connection error, make sure the lemonade server is running:
   ```bash
   lemonade-server serve
   ```

## GAIA-CLI Chat Demo

1. Make sure the Lemonade server is running (see [Getting Started Guide](#gaia-cli-getting-started-guide)).

2. Begin a chat session by running:
   ```bash
   gaia-cli chat
   ```
   This opens an interactive chat interface where you can converse with the AI.

3. During the chat:
   - Type your messages and press Enter to send.
   - Type `stop` to quit the chat session.
   - Type `restart` to clear chat history (functionality coming soon).
   ```bash
   You: who are you in one sentence?
   Chaty: I'm an AI assistant designed to help you with various tasks and answer your questions.
   You: stop
   Chat session ended.
   ```

## GAIA-CLI Talk Demo

For voice-based interaction with AI models, see the [Voice Interaction Guide](./talk.md).

## Basic Usage

The CLI supports the following core commands:

```bash
gaia-cli --help
```

### Available Commands

- **`llm`**: Send direct queries to language models (fastest option, no server management required)
- **`prompt`**: Send a single message to an agent and get a response
- **`chat`**: Start an interactive text chat session with message history
- **`talk`**: Start a voice-based conversation session
- **`blender`**: Create and modify 3D scenes using the Blender agent
- **`stats`**: View model performance statistics from the most recent run
- **`test`**: Run various audio/speech tests for development and troubleshooting
- **`youtube`**: YouTube utilities for transcript downloading
- **`kill`**: Kill a process running on a specific port
- **`groundtruth`**: Generate ground truth data for RAG evaluation

### Global Options

All commands support these global options:
- `--logging-level`: Set logging verbosity [DEBUG, INFO, WARNING, ERROR, CRITICAL] (default: INFO)
- `-v, --version`: Show program's version number and exit

## LLM Command

The `llm` command provides direct access to language models:

```bash
gaia-cli llm QUERY [OPTIONS]
```

**Available options:**
- `--model`: Specify the model to use (optional, uses client default)
- `--max-tokens`: Maximum tokens to generate (default: 512)
- `--no-stream`: Disable streaming response (streaming enabled by default)

**Examples:**
```bash
# Basic query with streaming
gaia-cli llm "What is machine learning?"

# Use specific model with token limit
gaia-cli llm "Explain neural networks" --model llama3.2:3b --max-tokens 300

# Disable streaming for batch processing
gaia-cli llm "Generate a Python function to sort a list" --no-stream
```

**Requirements**: The lemonade server must be running. If not available, the command will provide clear instructions on how to start it.

## Prompt Command

Send a single prompt to a GAIA agent:

```bash
gaia-cli prompt "MESSAGE" [OPTIONS]
```

**Available options:**
- `--agent-name`: Name of the Gaia agent to use (default: "Chaty")
- `--host`: Host address for the Agent server (default: "127.0.0.1")
- `--port`: Port for the Agent server (default: 8001)
- `--model`: Model to use for the agent (default: "llama3.2:1b")
- `--max-new-tokens`: Maximum number of new tokens to generate (default: 512)
- `--stats`: Show performance statistics after generation

**Examples:**
```bash
# Basic prompt
gaia-cli prompt "What is the weather like today?"

# Use a specific agent with stats
gaia-cli prompt "Create a 3D cube" --agent-name Blender --stats

# Use different model and token limit
gaia-cli prompt "Write a story" --model llama3.2:3b --max-new-tokens 1000
```

## Chat Command

Start an interactive text conversation:

```bash
gaia-cli chat [OPTIONS]
```

**Available options:**
- `--agent-name`: Name of the Gaia agent to use (default: "Chaty")
- `--host`: Host address for the Agent server (default: "127.0.0.1")
- `--port`: Port for the Agent server (default: 8001)
- `--model`: Model to use for the agent (default: "llama3.2:1b")
- `--max-new-tokens`: Maximum number of new tokens to generate (default: 512)

**Example:**
```bash
# Start chat with default agent
gaia-cli chat

# Start chat with Blender agent
gaia-cli chat --agent-name Blender

# Use different model
gaia-cli chat --model llama3.2:3b
```

## Talk Command

Start a voice-based conversation:

```bash
gaia-cli talk [OPTIONS]
```

**Available options:**
- `--agent-name`: Name of the Gaia agent to use (default: "Chaty")
- `--host`: Host address for the Agent server (default: "127.0.0.1")
- `--port`: Port for the Agent server (default: 8001)
- `--model`: Model to use for the agent (default: "llama3.2:1b")
- `--max-new-tokens`: Maximum number of new tokens to generate (default: 512)
- `--no-tts`: Disable text-to-speech in voice chat mode
- `--audio-device-index`: Index of the audio input device to use (default: 1)
- `--whisper-model-size`: Size of the Whisper model [tiny, base, small, medium, large] (default: base)

For detailed voice interaction instructions, see the [Voice Interaction Guide](./talk.md).

## Blender Command

Create and modify 3D scenes using the Blender agent:

```bash
gaia-cli blender [OPTIONS]
```

**Available options:**
- `--model`: Model ID to use (default: "Llama-3.2-3B-Instruct-Hybrid")
- `--example`: Run a specific example (1-6), if not specified run interactive mode
- `--steps`: Maximum number of steps per query (default: 5)
- `--output-dir`: Directory to save output files (default: "output")
- `--stream`: Enable streaming mode for LLM responses
- `--stats`: Display performance statistics (default: True)
- `--query`: Custom query to run instead of examples
- `--interactive`: Enable interactive mode to continuously input queries
- `--debug-prompts`: Enable debug prompts (default: False)
- `--print-result`: Print results to console (default: False)
- `--mcp-port`: Port for the Blender MCP server (default: 9876)

**Available examples:**
1. **Clearing the scene** - Remove all objects from the scene
2. **Creating a basic cube** - Create a red cube at the center
3. **Creating a sphere with specific properties** - Blue sphere with custom position and scale
4. **Creating multiple objects** - Green cube and red sphere arrangement
5. **Creating and modifying objects** - Create and then modify a blue cylinder

**Examples:**
```bash
# Run all Blender examples in sequence
gaia-cli blender

# Run a specific example
gaia-cli blender --example 2

# Interactive Blender mode for custom 3D scene creation
gaia-cli blender --interactive

# Custom query to create specific 3D objects
gaia-cli blender --query "Create a red cube and blue sphere arranged in a line"

# Custom query with advanced scene setup
gaia-cli blender --query "Clear the scene, then create a green cylinder at (0,0,0) and a yellow cone 3 units above it"

# Enable debug mode with custom output directory
gaia-cli blender --interactive --debug-prompts --output-dir ./blender_results

# Use different model with streaming enabled
gaia-cli blender --model "custom-model" --stream --query "Create a complex 3D scene with multiple colored objects"

# Use custom MCP port
gaia-cli blender --mcp-port 9877 --query "Create a red cube"
```

**Blender Agent Capabilities:**
- **Scene Management**: Clear scenes, get scene information
- **Object Creation**: Create cubes, spheres, cylinders, cones, and torus objects
- **Material Assignment**: Set RGBA colors and materials for objects
- **Object Modification**: Modify position, rotation, and scale of existing objects
- **Interactive Planning**: Multi-step scene creation with automatic planning

**Requirements:**
- **Blender agent dependencies**: Must be installed for the command to be available
- **Lemonade server**: Must be running for AI processing (same as other CLI commands)
- **Blender MCP server**: Must be running for 3D scene communication

**MCP Server Setup:**
1. Open Blender (version 4.3+ recommended)
2. Go to `Edit > Preferences > Add-ons`
3. Click the down arrow button, then `Install...`
4. Navigate to: `src/gaia/mcp/blender_mcp_server.py`
5. Install and enable the `Simple Blender MCP` add-on
6. Open the 3D viewport sidebar (press `N` key if not visible)
7. Find the `Blender MCP` panel in the sidebar
8. Set port to `9876` and click `Start Server` (use `--mcp-port` to customize)

For detailed setup instructions with screenshots, see: `workshop/blender.ipynb`

**Note**: If either server is not running, you'll receive clear error messages with setup instructions.

## Stats Command

View performance statistics from the most recent model run:

```bash
gaia-cli stats [OPTIONS]
```

**Available options:**
- `--host`: Host address for the LLM server (default: "127.0.0.1")

## Groundtruth Command

Generate ground truth data for RAG evaluation using Claude:

```bash
gaia-cli groundtruth (-f FILE | -d DIRECTORY) [OPTIONS]
```

**Required arguments (mutually exclusive):**
- `-f, --file`: Path to a single document file to process
- `-d, --directory`: Directory containing documents to process

**Available options:**
- `-o, --output-dir`: Output directory for generated ground truth files (default: ./output/groundtruth)
- `-p, --pattern`: File pattern to match when processing directory (default: *.html)
- `-m, --model`: Claude model to use (default: claude-sonnet-4-20250514)
- `--max-tokens`: Maximum tokens for Claude responses (default: 4096)
- `--no-save-text`: Don't save extracted text for HTML files
- `--custom-prompt`: Path to a file containing a custom prompt for Claude
- `--num-samples`: Number of Q&A pairs to generate per document (default: 5)

**Examples:**
```bash
# Process a single file
gaia-cli groundtruth -f ./data/html/blender/introduction.html

# Process all HTML files in a directory
gaia-cli groundtruth -d ./data/html/blender

# Process with custom output directory and more Q&A pairs
gaia-cli groundtruth -f ./data/html/intro.html -o ./output/gt --num-samples 10

# Process PDFs with custom pattern
gaia-cli groundtruth -d ./data -p "*.pdf" -o ./output/gt

# Use custom Claude model
gaia-cli groundtruth -f ./data/doc.html -m claude-3-opus-20240229
```

## Test Commands

Run various tests for development and troubleshooting:

```bash
gaia-cli test --test-type TYPE [OPTIONS]
```

### Text-to-Speech (TTS) Tests

**Test types:**
- `tts-preprocessing`: Test TTS text preprocessing
- `tts-streaming`: Test TTS streaming playback
- `tts-audio-file`: Test TTS audio file generation

**TTS options:**
- `--test-text`: Text to use for TTS tests
- `--output-audio-file`: Output file path for TTS audio file test (default: output.wav)

**Examples:**
```bash
# Test TTS preprocessing with custom text
gaia-cli test --test-type tts-preprocessing --test-text "Hello, world!"

# Test TTS streaming
gaia-cli test --test-type tts-streaming --test-text "Testing streaming playback"

# Generate audio file
gaia-cli test --test-type tts-audio-file --test-text "Save this as audio" --output-audio-file speech.wav
```

### Automatic Speech Recognition (ASR) Tests

**Test types:**
- `asr-file-transcription`: Test ASR file transcription
- `asr-microphone`: Test ASR microphone input
- `asr-list-audio-devices`: List available audio input devices

**ASR options:**
- `--input-audio-file`: Input audio file path for file transcription test
- `--recording-duration`: Recording duration in seconds for microphone test (default: 10)
- `--audio-device-index`: Index of audio input device (default: 1)
- `--whisper-model-size`: Whisper model size [tiny, base, small, medium, large] (default: base)

**Examples:**
```bash
# Test file transcription
gaia-cli test --test-type asr-file-transcription --input-audio-file ./data/audio/test.m4a

# Test microphone for 30 seconds
gaia-cli test --test-type asr-microphone --recording-duration 30

# List audio devices
gaia-cli test --test-type asr-list-audio-devices
```

## YouTube Utilities

Download transcripts from YouTube videos:

```bash
gaia-cli youtube --download-transcript URL [--output-path PATH]
```

**Available options:**
- `--download-transcript`: YouTube URL to download transcript from
- `--output-path`: Output file path for transcript (optional, defaults to transcript_<video_id>.txt)

**Example:**
```bash
# Download YouTube transcript
gaia-cli youtube --download-transcript "https://youtube.com/watch?v=..." --output-path transcript.txt
```

## Kill Command

Terminate processes running on specific ports:

```bash
gaia-cli kill --port PORT_NUMBER
```

**Required options:**
- `--port`: Port number to kill process on

**Examples:**
```bash
# Kill process running on port 8000
gaia-cli kill --port 8000

# Kill process running on port 8001
gaia-cli kill --port 8001
```

This is useful for cleaning up lingering server processes. The command will:
- Find the process ID (PID) of any process bound to the specified port
- Forcefully terminate that process
- Provide feedback about the operation's success or failure

## Development Setup

For manual setup including creation of the virtual environment and installation of dependencies, refer to the instructions outlined [here](./dev.md). This approach is not recommended for most users and is only needed for development purposes.

## Troubleshooting

### Common Issues

**Connection Errors:**
If you get connection errors with any command, ensure the Lemonade server is running:
```bash
lemonade-server serve
```

**Model Issues:**
- Make sure you have sufficient RAM (16GB+ recommended)
- Check that your model files are properly downloaded
- Verify your Hugging Face token if prompted

**Audio Issues:**
- Use `gaia-cli test --test-type asr-list-audio-devices` to check available devices
- Verify your microphone permissions in Windows settings
- Try different audio device indices if the default doesn't work

**Performance:**
- For Hybrid mode, disable discrete GPUs in Device Manager
- Ensure NPU drivers are up to date
- Monitor system resources during model execution

For general troubleshooting, refer to the [Development Guide](./dev.md#troubleshooting) and [FAQ](./faq.md).

## License

Copyright(C) 2024-2025 Advanced Micro Devices, Inc. All rights reserved.
SPDX-License-Identifier: MIT