# Copyright(C) 2024-2025 Advanced Micro Devices, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

import sys
import argparse
import time
import json
import asyncio
import queue
import logging
import subprocess
from pathlib import Path
import os

import aiohttp
from aiohttp import ClientTimeout
import requests

from gaia.logger import get_logger
from gaia.audio.audio_client import AudioClient
from gaia.version import version
from gaia.agents.Blender.agent import BlenderAgent
from gaia.mcp.blender_mcp_client import MCPClient
from gaia.llm.lemonade_client import LemonadeClient, LemonadeClientError

# Set debug level for the logger
logging.getLogger("gaia").setLevel(logging.INFO)

# Add the parent directory to sys.path to import gaia modules
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent.parent
sys.path.append(str(parent_dir))


def check_lemonade_health(host="127.0.0.1", port=8000):
    """Check if Lemonade server is running and healthy using LemonadeClient."""
    log = get_logger(__name__)

    try:
        # Create a LemonadeClient instance for health checking
        client = LemonadeClient(host=host, port=port, verbose=False, keep_alive=True)

        # Perform health check
        health_result = client.health_check()

        # Check if the response indicates the server is healthy
        if health_result.get("status") == "ok":
            log.debug(f"Lemonade server is healthy at {host}:{port}")
            return True
        else:
            log.debug(f"Lemonade server health check returned: {health_result}")
            return False

    except LemonadeClientError as e:
        log.debug(f"Lemonade health check failed: {str(e)}")
        return False
    except Exception as e:
        log.debug(f"Unexpected error during Lemonade health check: {str(e)}")
        return False


def print_lemonade_error():
    """Print informative error message when Lemonade is not running."""
    print(
        "❌ Error: Lemonade server is not running or not accessible.", file=sys.stderr
    )
    print("", file=sys.stderr)
    print("Please start the Lemonade server first by:", file=sys.stderr)
    print("  • Double-clicking the desktop shortcut, or", file=sys.stderr)
    print("  • Running: lemonade-server serve", file=sys.stderr)
    print("", file=sys.stderr)
    print(
        "The server should be accessible at http://127.0.0.1:8000/api/v1/health",
        file=sys.stderr,
    )
    print("Then try your command again.", file=sys.stderr)


def check_mcp_health(host="127.0.0.1", port=9876):
    """Check if Blender MCP server is running and accessible."""
    log = get_logger(__name__)

    try:
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            log.debug("Blender MCP server is accessible")
            return True
        else:
            log.debug(f"Failed to connect to Blender MCP server on {host}:{port}")
            return False
    except Exception as e:
        log.debug(f"Error checking MCP server: {str(e)}")
        return False


def print_mcp_error():
    """Print informative error message when Blender MCP server is not running."""
    print(
        "❌ Error: Blender MCP server is not running or not accessible.",
        file=sys.stderr,
    )
    print("", file=sys.stderr)
    print("To set up the Blender MCP server:", file=sys.stderr)
    print("", file=sys.stderr)
    print("1. Open Blender (version 4.3 or newer recommended)", file=sys.stderr)
    print("2. Go to Edit > Preferences > Add-ons", file=sys.stderr)
    print("3. Click the down arrow button, then 'Install...'", file=sys.stderr)
    print(
        "4. Navigate to: <GAIA_REPO>/src/gaia/mcp/blender_mcp_server.py",
        file=sys.stderr,
    )
    print("5. Install and enable the 'Simple Blender MCP' add-on", file=sys.stderr)
    print(
        "6. Open the 3D viewport sidebar (press 'N' key if not visible)",
        file=sys.stderr,
    )
    print("7. Find the 'Blender MCP' panel in the sidebar", file=sys.stderr)
    print("8. Set port to 9876 and click 'Start Server'", file=sys.stderr)
    print("", file=sys.stderr)
    print(
        "For detailed setup instructions, see: workshop/blender.ipynb", file=sys.stderr
    )
    print("", file=sys.stderr)
    print("Then try your Blender command again.", file=sys.stderr)


class GaiaCliClient:
    log = get_logger(__name__)

    def __init__(
        self,
        agent_name="Chaty",
        host="127.0.0.1",
        port=8001,
        model="Llama-3.2-3B-Instruct-Hybrid",
        max_tokens=512,
        whisper_model_size="base",
        audio_device_index=1,
        silence_threshold=0.5,
        show_stats=False,
        enable_tts=False,
        logging_level="INFO",
    ):
        self.log = self.__class__.log  # Use the class-level logger for instances
        # Set the logging level for this instance's logger
        self.log.setLevel(getattr(logging, logging_level))

        self.agent_name = agent_name
        self.host = host
        self.port = port
        self.llm_port = 8000
        self.agent_url = f"http://{host}:{port}"
        self.llm_url = f"http://{host}:{self.llm_port}"
        self.model = model
        self.max_tokens = max_tokens
        self.cli_mode = True  # Set this to True for CLI mode
        self.show_stats = show_stats

        # Initialize audio client for voice functionality
        self.audio_client = AudioClient(
            whisper_model_size=whisper_model_size,
            audio_device_index=audio_device_index,
            silence_threshold=silence_threshold,
            enable_tts=enable_tts,
            host=host,
            port=port,
            llm_port=self.llm_port,
            agent_name=agent_name,
            logging_level=logging_level,
        )

        self.log.debug("Gaia CLI client initialized.")
        self.log.debug(
            f"agent_name: {self.agent_name}\n host: {self.host}\n"
            f"port: {self.port}\n llm_port: {self.llm_port}\n"
            f"model: {self.model}\n max_tokens: {self.max_tokens}"
        )

    async def send_message(self, message):
        url = f"{self.agent_url}/prompt"
        data = {"prompt": message}
        try:
            async with aiohttp.ClientSession(
                timeout=ClientTimeout(total=3600)
            ) as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        async for chunk in response.content.iter_any():
                            chunk = chunk.decode("utf-8")
                            print(chunk, end="", flush=True)
                            yield chunk
                    else:
                        error_text = await response.text()
                        error_message = f"❌ Error: {response.status} - {error_text}"
                        print(error_message)
                        yield error_message
        except aiohttp.ClientError as e:
            error_message = f"❌ Error: {str(e)}"
            self.log.error(error_message)
            yield error_message

    def get_stats(self):
        url = f"{self.llm_url}/stats"
        try:
            response = requests.get(url, timeout=10)
            self.log.debug(f"{url}: {response.json()}")
            if response.status_code == 200:
                try:
                    stats = response.json()
                    self.log.debug(f"Stats received: {stats}")
                    return stats
                except json.JSONDecodeError as je:
                    self.log.error(f"Failed to parse JSON response: {response.text}")
                    self.log.error(f"JSON decode error: {str(je)}")
                    return None
            else:
                self.log.error(
                    f"Failed to get stats. Status code: {response.status_code}"
                )
                return None
        except requests.RequestException as e:
            self.log.error(f"Error while fetching stats: {str(e)}")
            return None

    async def start_voice_chat(self):
        """Start a voice-based chat session."""
        await self.audio_client.start_voice_chat(self.process_voice_input)

    async def process_voice_input(self, text):
        """Process transcribed voice input and get AI response"""
        # Create callback for stats if needed
        get_stats_callback = None
        if hasattr(self, "show_stats") and self.show_stats:
            get_stats_callback = self.get_stats

        await self.audio_client.process_voice_input(text, get_stats_callback)

    async def halt_generation(self):
        """Send a request to halt the current generation."""
        await self.audio_client.halt_generation()

    async def talk(self):
        """Voice-based chat interface"""
        self.audio_client.initialize_tts()
        await self.start_voice_chat()

    async def prompt(self, message):
        async for chunk in self.send_message(message):
            yield chunk

    def chat(
        self, message=None, model=None, max_tokens=512, system_prompt=None, stats=False
    ):
        """Chat interface using the new ChatApp - interactive if no message, single message if message provided"""
        try:
            from gaia.agents.chat.app import main as chat_main

            # Interactive mode if no message provided, single message mode if message provided
            use_interactive = message is None

            if use_interactive:
                # Interactive mode
                chat_main(
                    model=model,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                    interactive=True,
                )
            else:
                # Single message mode
                response = chat_main(
                    message=message,
                    model=model,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                    interactive=False,
                )

                # Display response directly
                print(response)

                # Show stats if requested
                if stats:
                    from gaia.agents.chat.app import ChatApp

                    app = ChatApp(system_prompt=system_prompt, model=model)
                    stats_data = app.get_stats()
                    if stats_data:
                        print(f"\n{'='*30}")
                        print("Performance Statistics:")
                        print("=" * 30)
                        for key, value in stats_data.items():
                            print(f"{key}: {value}")
                        print("=" * 30)

        except Exception as e:
            # Check if it's a connection error and provide helpful message
            self.log.error(f"Error in chat: {str(e)}")
            print(f"❌ Error: {str(e)}")
            sys.exit(1)


async def async_main(action, **kwargs):
    log = get_logger(__name__)

    # Check Lemonade health for all actions that require it
    if action in ["prompt", "chat", "talk", "stats"]:
        if not check_lemonade_health():
            print_lemonade_error()
            sys.exit(1)

    # Create client for all actions - exclude parameters that aren't constructor arguments
    client = GaiaCliClient(
        **{k: v for k, v in kwargs.items() if k not in ["message", "stats"]}
    )

    if action == "prompt":
        if not kwargs.get("message"):
            log.error("Message is required for prompt action.")
            print("❌ Error: Message is required for prompt action.")
            sys.exit(1)
        response = ""
        async for chunk in client.prompt(kwargs["message"]):
            response += chunk
        if kwargs.get("show_stats", False):
            stats = client.get_stats()
            if stats:
                return {"response": response, "stats": stats}
        return {"response": response}
    elif action == "chat":
        client.chat(
            message=kwargs.get("message"),
            model=kwargs.get("model"),
            max_tokens=kwargs.get("max_tokens", 512),
            system_prompt=kwargs.get("system_prompt"),
            stats=kwargs.get("stats", False),
        )
        return
    elif action == "talk":
        await client.talk()
        log.info("Voice chat session ended.")
        return
    elif action == "stats":
        stats = client.get_stats()
        if stats:
            return {"stats": stats}
        log.error("No stats available.")
        print("❌ Error: No stats available.")
        sys.exit(1)
    else:
        log.error(f"Unknown action specified: {action}")
        print(f"❌ Error: Unknown action specified: {action}")
        sys.exit(1)


def run_cli(action, **kwargs):
    return asyncio.run(async_main(action, **kwargs))


def main():
    # Create the main parser
    parser = argparse.ArgumentParser(
        description=f"Gaia CLI - Interact with Gaia AI agents. \n{version}",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Get logger instance
    log = get_logger(__name__)

    # Add version argument
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{version}",
        help="Show program's version number and exit",
    )

    # Create a parent parser for common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--logging-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)",
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # Core Gaia CLI commands - add parent_parser to each subcommand
    # Note: start and stop commands removed since CLI assumes Lemonade is running

    # Add prompt-specific options
    prompt_parser = subparsers.add_parser(
        "prompt", help="Send a single prompt to Gaia", parents=[parent_parser]
    )
    prompt_parser.add_argument(
        "message",
        help="Message to send to Gaia",
    )
    prompt_parser.add_argument(
        "--agent-name",
        default="Chaty",
        help="Name of the Gaia agent to use (e.g., Llm, Chaty, Joker, Clip, Rag, etc.)",
    )
    prompt_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address for the Agent server (default: 127.0.0.1)",
    )
    prompt_parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for the Agent server (default: 8001)",
    )
    prompt_parser.add_argument(
        "--model",
        default="Llama-3.2-3B-Instruct-Hybrid",
        help="Model to use for the agent (default: Llama-3.2-3B-Instruct-Hybrid)",
    )
    prompt_parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Maximum number of tokens to generate (default: 512)",
    )
    prompt_parser.add_argument(
        "--stats",
        action="store_true",
        help="Show performance statistics after generation",
    )

    chat_parser = subparsers.add_parser(
        "chat",
        help="Start interactive chat session with conversation history",
        parents=[parent_parser],
    )
    chat_parser.add_argument(
        "message",
        nargs="?",
        help="Message to send to the chatbot (defaults to interactive mode if not provided)",
    )
    chat_parser.add_argument(
        "--model",
        default="Llama-3.2-3B-Instruct-Hybrid",
        help="Model name to use (default: Llama-3.2-3B-Instruct-Hybrid)",
    )
    chat_parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Maximum tokens to generate (default: 512)",
    )
    chat_parser.add_argument("--system-prompt", help="Custom system prompt to use")

    chat_parser.add_argument(
        "--stats", action="store_true", help="Show performance statistics"
    )

    talk_parser = subparsers.add_parser(
        "talk", help="Start voice conversation with Gaia", parents=[parent_parser]
    )
    talk_parser.add_argument(
        "--agent-name",
        default="Chaty",
        help="Name of the Gaia agent to use (e.g., Llm, Chaty, Joker, Clip, Rag, etc.)",
    )
    talk_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address for the Agent server (default: 127.0.0.1)",
    )
    talk_parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for the Agent server (default: 8001)",
    )
    talk_parser.add_argument(
        "--model",
        default="Llama-3.2-3B-Instruct-Hybrid",
        help="Model to use for the agent (default: Llama-3.2-3B-Instruct-Hybrid)",
    )
    talk_parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Maximum number of tokens to generate (default: 512)",
    )
    talk_parser.add_argument(
        "--no-tts",
        action="store_true",
        help="Disable text-to-speech in voice chat mode",
    )
    talk_parser.add_argument(
        "--audio-device-index",
        type=int,
        default=1,
        help="Index of the audio input device to use",
    )
    talk_parser.add_argument(
        "--whisper-model-size",
        type=str,
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Size of the Whisper model to use (default: base)",
    )

    # Add Blender agent command
    blender_parser = subparsers.add_parser(
        "blender",
        help="Blender 3D scene creation and modification",
        parents=[parent_parser],
    )
    blender_parser.add_argument(
        "--model",
        default="Llama-3.2-3B-Instruct-Hybrid",
        help="Model ID to use (default: Llama-3.2-3B-Instruct-Hybrid)",
    )
    blender_parser.add_argument(
        "--example",
        type=int,
        choices=range(1, 7),
        help="Run a specific example (1-6), if not specified run interactive mode",
    )
    blender_parser.add_argument(
        "--steps", type=int, default=5, help="Maximum number of steps per query"
    )
    blender_parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save output files",
    )
    blender_parser.add_argument(
        "--stream", action="store_true", help="Enable streaming mode for LLM responses"
    )
    blender_parser.add_argument(
        "--stats",
        action="store_true",
        default=True,
        help="Display performance statistics",
    )
    blender_parser.add_argument(
        "--query", type=str, help="Custom query to run instead of examples"
    )
    blender_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive mode to continuously input queries",
    )
    blender_parser.add_argument(
        "--debug-prompts",
        action="store_true",
        default=False,
        help="Enable debug prompts",
    )
    blender_parser.add_argument(
        "--print-result",
        action="store_true",
        default=False,
        help="Print results to console",
    )
    blender_parser.add_argument(
        "--mcp-port",
        type=int,
        default=9876,
        help="Port for the Blender MCP server (default: 9876)",
    )

    stats_parser = subparsers.add_parser(
        "stats",
        help="Show Gaia statistics from the most recent run.",
        parents=[parent_parser],
    )
    stats_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address for the LLM server (default: 127.0.0.1)",
    )

    # Add utility commands to main parser instead of creating a separate parser
    test_parser = subparsers.add_parser(
        "test", help="Run various tests", parents=[parent_parser]
    )
    test_parser.add_argument(
        "--test-type",
        required=True,
        choices=[
            "tts-preprocessing",
            "tts-streaming",
            "tts-audio-file",
            "asr-file-transcription",
            "asr-microphone",
            "asr-list-audio-devices",
        ],
        help="Type of test to run",
    )
    test_parser.add_argument(
        "--test-text",
        help="Text to use for TTS tests",
    )
    test_parser.add_argument(
        "--input-audio-file",
        help="Input audio file path for ASR file transcription test",
    )
    test_parser.add_argument(
        "--output-audio-file",
        default="output.wav",
        help="Output file path for TTS audio file test (default: output.wav)",
    )
    test_parser.add_argument(
        "--recording-duration",
        type=int,
        default=10,
        help="Recording duration in seconds for ASR microphone test (default: 10)",
    )
    test_parser.add_argument(
        "--whisper-model-size",
        type=str,
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Size of the Whisper model to use (default: base)",
    )
    test_parser.add_argument(
        "--audio-device-index",
        type=int,
        default=1,
        help="Index of audio input device (optional)",
    )

    # Add YouTube-specific options
    yt_parser = subparsers.add_parser(
        "youtube", help="YouTube utilities", parents=[parent_parser]
    )
    yt_parser.add_argument(
        "--download-transcript",
        metavar="URL",
        help="Download transcript from a YouTube URL",
    )
    yt_parser.add_argument(
        "--output-path",
        help="Output file path for transcript (optional, default: transcript_<video_id>.txt)",
    )

    # Add new subparser for kill command
    kill_parser = subparsers.add_parser(
        "kill", help="Kill process running on specific port", parents=[parent_parser]
    )
    kill_parser.add_argument(
        "--port", type=int, required=True, help="Port number to kill process on"
    )

    # Add LLM app command
    llm_parser = subparsers.add_parser(
        "llm",
        help="Run simple LLM queries using LLMClient wrapper",
        parents=[parent_parser],
    )
    llm_parser.add_argument("query", help="The query/prompt to send to the LLM")
    llm_parser.add_argument(
        "--model", help="Model name to use (optional, uses client default)"
    )
    llm_parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
        help="Maximum tokens to generate (default: 512)",
    )
    llm_parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming the response (streaming is enabled by default)",
    )

    # Add groundtruth generation subparser
    gt_parser = subparsers.add_parser(
        "groundtruth",
        help="Generate ground truth data for various evaluation use cases",
        parents=[parent_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single file for RAG evaluation (default)
  gaia groundtruth -f ./data/html/blender/introduction.html

  # Process a transcript for summary generation
  gaia groundtruth -f ./data/transcripts/meeting.txt --use-case summarization

  # Process a transcript for Q&A generation
  gaia groundtruth -f ./data/transcripts/meeting.txt --use-case qa

  # Process an email for business email analysis
  gaia groundtruth -f ./data/emails/project_update.txt --use-case email

  # Process all HTML files in a directory for RAG
  gaia groundtruth -d ./data/html/blender

  # Process transcript files for summarization
  gaia groundtruth -d ./data/transcripts -p "*.txt" --use-case summarization

  # Process transcript files for Q&A generation
  gaia groundtruth -d ./data/transcripts -p "*.txt" --use-case qa

  # Process email files for email processing evaluation
  gaia groundtruth -d ./data/emails -p "*.txt" --use-case email

  # Process with custom output directory
  gaia groundtruth -f ./data/html/intro.html -o ./output/gt

  # Use custom Claude model
  gaia groundtruth -f ./data/doc.html -m claude-3-opus-20240229

  # Generate 10 Q&A pairs per document (RAG only)
  gaia groundtruth -d ./data/html/blender --num-samples 10
        """,
    )

    # Input source (mutually exclusive)
    gt_input_group = gt_parser.add_mutually_exclusive_group(required=True)
    gt_input_group.add_argument(
        "-f", "--file", type=str, help="Path to a single document file to process"
    )
    gt_input_group.add_argument(
        "-d",
        "--directory",
        type=str,
        help="Directory containing documents to process (results will be consolidated into a single JSON file)",
    )

    # Optional arguments for groundtruth
    gt_parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="./output/groundtruth",
        help="Output directory for generated ground truth files (default: ./output/groundtruth)",
    )
    gt_parser.add_argument(
        "-p",
        "--pattern",
        type=str,
        default="*",
        help="File pattern to match when processing directory (default: *)",
    )
    gt_parser.add_argument(
        "-u",
        "--use-case",
        type=str,
        choices=["rag", "summarization", "qa", "email"],
        default="rag",
        help="Use case for ground truth generation: 'rag' for document Q&A pairs, 'summarization' for transcript summaries, 'qa' for transcript Q&A pairs, 'email' for email processing analysis (default: rag)",
    )
    gt_parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)",
    )
    gt_parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Maximum tokens for Claude responses (default: 4096)",
    )
    gt_parser.add_argument(
        "--no-save-text",
        action="store_true",
        help="Don't save extracted text for HTML files",
    )
    gt_parser.add_argument(
        "--custom-prompt",
        type=str,
        help="Path to a file containing a custom prompt for Claude",
    )
    gt_parser.add_argument(
        "--num-samples",
        type=int,
        default=5,
        help="Number of Q&A pairs to generate per document (RAG use case only, default: 5)",
    )

    # Add new subparser for creating evaluation templates
    template_parser = subparsers.add_parser(
        "create-template",
        help="Create a template results file from ground truth data for manual RAG evaluation",
        parents=[parent_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create template from ground truth file
  gaia create-template -f ./output/groundtruth/introduction.groundtruth.json

  # Create template with custom output path
  gaia create-template -f ./output/groundtruth/doc.groundtruth.json -o ./templates/

  # Create template with custom similarity threshold
  gaia create-template -f ./output/groundtruth/doc.groundtruth.json --threshold 0.8
        """,
    )

    template_parser.add_argument(
        "-f",
        "--groundtruth-file",
        type=str,
        required=True,
        help="Path to the ground truth JSON file",
    )
    template_parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="./output/templates",
        help="Output directory for template file (default: ./output/templates)",
    )
    template_parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Similarity threshold for evaluation (default: 0.7)",
    )

    # Add new subparser for RAG evaluation
    eval_parser = subparsers.add_parser(
        "eval",
        help="Evaluate RAG system performance using results data",
        parents=[parent_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate single RAG results file
  gaia eval -f ./output/templates/introduction.template.json

  # Evaluate all JSON files in a directory
  gaia eval -d ./experiments -o ./evaluation

  # Evaluate with custom output directory
  gaia eval -f ./output/rag/results.json -o ./output/eval

  # Evaluate summarization results with separate groundtruth file
  gaia eval -f ./output/experiments/summary.experiment.json -g ./output/groundtruth/transcript.summarization.groundtruth.json

  # Evaluate directory with specific Claude model
  gaia eval -d ./experiments -m claude-3-opus-20240229

  # Evaluate and display summary only (no detailed report file)
  gaia eval -d ./experiments --summary-only
        """,
    )

    # Create mutually exclusive group for file vs directory input
    file_group = eval_parser.add_mutually_exclusive_group(required=True)
    file_group.add_argument(
        "-f",
        "--results-file",
        type=str,
        help="Path to the RAG results JSON file (template or results)",
    )
    file_group.add_argument(
        "-d",
        "--directory",
        type=str,
        help="Path to directory containing JSON experiment files to process",
    )
    eval_parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="./output/eval",
        help="Output directory for evaluation report (default: ./output/eval)",
    )
    eval_parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="claude-sonnet-4-20250514",
        help="Claude model to use for evaluation (default: claude-sonnet-4-20250514)",
    )
    eval_parser.add_argument(
        "-g",
        "--groundtruth",
        type=str,
        help="Path to ground truth file for comparison (especially useful for summarization evaluation)",
    )
    eval_parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only display summary, don't save detailed evaluation report",
    )

    # Add new subparser for generating summary reports from evaluation directories
    report_parser = subparsers.add_parser(
        "report",
        help="Generate summary report from evaluation results directory",
        parents=[parent_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report from evaluation directory
  gaia report -d ./output/eval

  # Generate report with custom output filename
  gaia report -d ./output/eval -o Model_Comparison_Report.md

  # Generate report and display summary only
  gaia report -d ./output/eval --summary-only
        """,
    )

    report_parser.add_argument(
        "-d",
        "--eval-dir",
        type=str,
        required=True,
        help="Directory containing .eval.json files to analyze",
    )
    report_parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        default="LLM_RAG_Evaluation_Report.md",
        help="Output filename for the markdown report (default: LLM_RAG_Evaluation_Report.md)",
    )
    report_parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only display summary to console, don't save report file",
    )

    # Add new subparser for launching the evaluation results visualizer
    visualize_parser = subparsers.add_parser(
        "visualize",
        help="Launch web-based evaluation results visualizer",
        parents=[parent_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch visualizer with default settings
  gaia visualize

  # Launch with custom data directories
  gaia visualize --experiments-dir ./my_experiments --evaluations-dir ./my_evaluations

  # Launch on custom port without opening browser
  gaia visualize --port 8080 --no-browser

  # Launch with specific workspace directory
  gaia visualize --workspace ./evaluation_workspace
        """,
    )

    visualize_parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to run the visualizer server on (default: 3000)",
    )
    visualize_parser.add_argument(
        "--experiments-dir",
        type=str,
        help="Directory containing experiment JSON files (default: ./experiments)",
    )
    visualize_parser.add_argument(
        "--evaluations-dir",
        type=str,
        help="Directory containing evaluation JSON files (default: ./evaluation)",
    )
    visualize_parser.add_argument(
        "--workspace",
        type=str,
        help="Base workspace directory (default: current directory)",
    )
    visualize_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser after starting server",
    )
    visualize_parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host address for the visualizer server (default: localhost)",
    )

    # Add new subparser for generating synthetic test data
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate synthetic test data for evaluation (meeting transcripts or business emails)",
        parents=[parent_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate meeting transcripts
  gaia generate --meeting-transcript -o ./output/meetings
  gaia generate --meeting-transcript -o ./output/meetings --target-tokens 3000 --count-per-type 3
  gaia generate --meeting-transcript -o ./output/meetings --meeting-types standup planning

  # Generate business emails
  gaia generate --email -o ./output/emails
  gaia generate --email -o ./output/emails --target-tokens 1500 --count-per-type 3
  gaia generate --email -o ./output/emails --email-types project_update sales_outreach
        """,
    )

    # Add new subparser for batch experiment runner
    batch_exp_parser = subparsers.add_parser(
        "batch-experiment",
        help="Run batch experiments with different LLM configurations on transcript data",
        parents=[parent_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create sample configuration file
  gaia batch-experiment --create-sample-config experiment_config.json

  # Create configuration from groundtruth metadata
  gaia batch-experiment --create-config-from-groundtruth ./output/groundtruth/meeting.qa.groundtruth.json

  # Run batch experiments on transcript directory
  gaia batch-experiment -c experiment_config.json -i ./transcripts -o ./output/experiments

  # Run batch experiments on transcript directory with custom queries from groundtruth
  gaia batch-experiment -c experiment_config.json -i ./transcripts -q ./output/groundtruth/meeting.qa.groundtruth.json -o ./output/experiments

  # Run batch experiments on single transcript file
  gaia batch-experiment -c experiment_config.json -i ./meeting_transcript.txt -o ./output/experiments

  # Run batch experiments on groundtruth file
  gaia batch-experiment -c experiment_config.json -i ./output/groundtruth/transcript.qa.groundtruth.json -o ./output/experiments

  # Run with custom delay between requests to avoid rate limiting
  gaia batch-experiment -c experiment_config.json -i ./transcripts -o ./output/experiments --delay 2.0

  # Process multiple experiment results
  gaia eval -f ./output/experiments/Claude-Sonnet-Standard.experiment.json
  gaia report -d ./output/experiments
        """,
    )

    # Add mutually exclusive group for generation type
    generate_type_group = generate_parser.add_mutually_exclusive_group(required=True)
    generate_type_group.add_argument(
        "--meeting-transcript",
        action="store_true",
        help="Generate meeting transcripts for testing transcript summarization",
    )
    generate_type_group.add_argument(
        "--email",
        action="store_true",
        help="Generate business emails for testing email processing and summarization",
    )

    # Add common arguments for generate command
    generate_parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for generated files",
    )
    generate_parser.add_argument(
        "--target-tokens",
        type=int,
        help="Target token count per generated item (default: 1000 for transcripts, 800 for emails)",
    )
    generate_parser.add_argument(
        "--count-per-type",
        type=int,
        default=1,
        help="Number items to generate per type (default: 1)",
    )
    generate_parser.add_argument(
        "--claude-model",
        type=str,
        default="claude-sonnet-4-20250514",
        help="Claude model to use for generation (default: claude-sonnet-4-20250514)",
    )

    # Add type-specific arguments
    generate_parser.add_argument(
        "--meeting-types",
        nargs="+",
        choices=[
            "standup",
            "planning",
            "client_call",
            "design_review",
            "performance_review",
            "all_hands",
            "budget_planning",
            "product_roadmap",
        ],
        help="Specific meeting types to generate (only used with --meeting-transcript, default: all types)",
    )
    generate_parser.add_argument(
        "--email-types",
        nargs="+",
        choices=[
            "project_update",
            "meeting_request",
            "customer_support",
            "sales_outreach",
            "internal_announcement",
            "technical_discussion",
            "vendor_communication",
            "performance_feedback",
        ],
        help="Specific email types to generate (only used with --email, default: all types)",
    )

    # Add arguments for batch experiment command
    batch_exp_parser.add_argument(
        "-c", "--config", type=str, help="Path to experiment configuration JSON file"
    )
    batch_exp_parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="Path to input data: transcript file, directory of transcripts, or groundtruth JSON file",
    )
    batch_exp_parser.add_argument(
        "-q",
        "--queries-source",
        type=str,
        help="Path to groundtruth JSON file to extract queries from (for QA experiments on raw transcripts)",
    )
    batch_exp_parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="./output/experiments",
        help="Output directory for experiment results (default: ./output/experiments)",
    )
    batch_exp_parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between requests to avoid rate limiting (default: 1.0)",
    )
    batch_exp_parser.add_argument(
        "--create-sample-config",
        type=str,
        help="Create a sample configuration file at the specified path",
    )
    batch_exp_parser.add_argument(
        "--create-config-from-groundtruth",
        type=str,
        help="Create configuration from groundtruth file metadata (provide groundtruth file path)",
    )

    args = parser.parse_args()

    # Check if action is specified
    if not args.action:
        log.warning("No action specified. Displaying help message.")
        parser.print_help()
        return

    # Set logging level using the GaiaLogger manager
    from gaia.logger import log_manager

    log_manager.set_level("gaia", getattr(logging, args.logging_level))

    # Handle core Gaia CLI commands
    if args.action in ["prompt", "chat", "talk", "stats"]:
        kwargs = {
            k: v for k, v in vars(args).items() if v is not None and k != "action"
        }
        log.debug(f"Executing {args.action} with parameters: {kwargs}")
        try:
            result = run_cli(args.action, **kwargs)
            if result:
                print(result)
        except Exception as e:
            log.error(f"Error executing {args.action}: {e}")
            print(f"❌ Error: {e}")
            sys.exit(1)
        return

    # Handle report generation command
    if args.action == "report":
        log.info("Generating summary report from evaluation directory")
        try:
            from gaia.eval.eval import RagEvaluator
        except ImportError as e:
            log.error(f"Failed to import RagEvaluator: {e}")
            print("❌ Error: Failed to import eval module.")
            print("The evaluation dependencies are not installed.")
            print("")
            print("To fix this, install the evaluation dependencies:")
            print("  pip install .[eval]")
            print("")
            print("This will install required packages including:")
            print("  - anthropic (for Claude AI)")
            print("  - beautifulsoup4 (for HTML processing)")
            print("  - python-dotenv (for environment variables)")
            return

        try:
            evaluator = RagEvaluator()

            # If summary_only is True, don't save the report file
            output_path = None if args.summary_only else args.output_file

            # Create output directory if it doesn't exist
            if output_path and output_path != "temp_report.md":
                output_dir = os.path.dirname(output_path)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)

            result = evaluator.generate_summary_report(
                eval_dir=args.eval_dir, output_path=output_path or "temp_report.md"
            )

            print(
                f"✅ Successfully analyzed {result['models_analyzed']} evaluation files"
            )

            if not args.summary_only:
                print(f"  Report saved to: {result['report_path']}")

            # Display key metrics summary
            models_data = result["summary_data"]
            if models_data:
                best_model = models_data[0]
                print(
                    f"  Best performing model: {best_model['name']} ({best_model['pass_rate']:.0%} pass rate)"
                )
                print(
                    f"  Overall performance range: {models_data[-1]['pass_rate']:.0%} - {best_model['pass_rate']:.0%}"
                )

                # Check if any model meets production standards
                production_ready = any(
                    m["pass_rate"] >= 0.7 and m["mean_similarity"] >= 0.7
                    for m in models_data
                )
                if production_ready:
                    print("  Status: Some models approaching production readiness")
                else:
                    print(
                        "  Status: No models meet production standards (70% pass rate + 0.7 similarity)"
                    )

            # Clean up temp file if using summary_only
            if args.summary_only and output_path is None:
                try:
                    os.remove("temp_report.md")
                except OSError:
                    pass

        except Exception as e:
            log.error(f"Error generating report: {e}")
            print(f"Error generating report: {e}")
            return

        return

    # Handle utility commands
    if args.action == "test":
        log.info(f"Running test type: {args.test_type}")
        if args.test_type.startswith("tts"):
            try:
                from gaia.audio.kokoro_tts import KokoroTTS

                tts = KokoroTTS()
                log.debug("TTS initialized successfully")
            except Exception as e:
                log.error(f"Failed to initialize TTS: {e}")
                print(f"❌ Error: Failed to initialize TTS: {e}")
                return

            test_text = (
                args.test_text
                or """
Let's play a game of trivia. I'll ask you a series of questions on a particular topic,
and you try to answer them to the best of your ability.

Here's your first question:

**Question 1:** Which American author wrote the classic novel "To Kill a Mockingbird"?

A) F. Scott Fitzgerald
B) Harper Lee
C) Jane Austen
D) J. K. Rowling
E) Edgar Allan Poe

Let me know your answer!
"""
            )

            if args.test_type == "tts-preprocessing":
                tts.test_preprocessing(test_text)
            elif args.test_type == "tts-streaming":
                tts.test_streaming_playback(test_text)
            elif args.test_type == "tts-audio-file":
                tts.test_generate_audio_file(test_text, args.output_audio_file)

        elif args.test_type.startswith("asr"):
            try:
                from gaia.audio.whisper_asr import WhisperAsr

                asr = WhisperAsr(
                    model_size=args.whisper_model_size,
                    device_index=args.audio_device_index,
                )
                log.debug("ASR initialized successfully")
            except ImportError:
                log.error(
                    "WhisperAsr not found. Please install voice support with: pip install .[talk]"
                )
                raise
            except Exception as e:
                log.error(f"Failed to initialize ASR: {e}")
                print(f"❌ Error: Failed to initialize ASR: {e}")
                return

            if args.test_type == "asr-file-transcription":
                if not args.input_audio_file:
                    print(
                        "❌ Error: --input-audio-file is required for asr-file-transcription test"
                    )
                    return
                try:
                    text = asr.transcribe_file(args.input_audio_file)
                    print("\nTranscription result:")
                    print("-" * 40)
                    print(text)
                    print("-" * 40)
                except Exception as e:
                    print(f"❌ Error transcribing file: {e}")

            elif args.test_type == "asr-microphone":
                print(f"\nRecording for {args.recording_duration} seconds...")
                print("Speak into your microphone...")

                # Setup transcription queue and start recording
                transcription_queue = queue.Queue()
                asr.transcription_queue = transcription_queue
                asr.start_recording()

                try:
                    start_time = time.time()
                    while time.time() - start_time < args.recording_duration:
                        try:
                            text = transcription_queue.get_nowait()
                            print(f"\nTranscribed: {text}")
                        except queue.Empty:
                            time.sleep(0.1)
                            remaining = args.recording_duration - int(
                                time.time() - start_time
                            )
                            print(f"\rRecording... {remaining}s remaining", end="")
                finally:
                    asr.stop_recording()
                    print("\nRecording stopped.")

            elif args.test_type == "asr-list-audio-devices":
                from gaia.audio.audio_recorder import AudioRecorder

                recorder = AudioRecorder()
                devices = recorder.list_audio_devices()
                print("\nAvailable Audio Input Devices:")
                for device in devices:
                    print(f"Index {device['index']}: {device['name']}")
                    print(f"    Max Input Channels: {device['maxInputChannels']}")
                    print(f"    Default Sample Rate: {device['defaultSampleRate']}")
                    print()
                return

        return

    # Handle utility functions
    if args.action == "youtube":
        if args.download_transcript:
            log.info(f"Downloading transcript from {args.download_transcript}")
            from llama_index.readers.youtube_transcript import YoutubeTranscriptReader

            doc = YoutubeTranscriptReader().load_data(
                ytlinks=[args.download_transcript]
            )
            output_path = args.output_path or "transcript.txt"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(doc[0].text)
            print(f"✅ Transcript downloaded to: {output_path}")
            return

    # Handle kill command
    if args.action == "kill":
        log.info(f"Attempting to kill process on port {args.port}")
        result = kill_process_by_port(args.port)
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
        return

    # Handle LLM command
    if args.action == "llm":
        try:
            # Fast import and execution - health check happens in LLMClient
            from gaia.agents.Llm.app import main as llm

            response = llm(
                query=args.query,
                model=args.model,
                max_tokens=args.max_tokens,
                stream=not getattr(args, "no_stream", False),
            )

            # Only print if streaming is disabled (response wasn't already printed during streaming)
            if getattr(args, "no_stream", False):
                print("\n" + "=" * 50)
                print("LLM Response:")
                print("=" * 50)
                print(response)
                print("=" * 50)
            return
        except Exception as e:
            # Check if it's a connection error and provide helpful message
            error_msg = str(e).lower()
            if (
                "connection" in error_msg
                or "refused" in error_msg
                or "timeout" in error_msg
            ):
                print_lemonade_error()
            else:
                print(f"❌ Error: {str(e)}")
            return

    # Handle groundtruth generation
    if args.action == "groundtruth":
        log.info("Starting ground truth generation")
        try:
            from gaia.eval.groundtruth import GroundTruthGenerator, UseCase
        except ImportError as e:
            log.error(f"Failed to import GroundTruthGenerator: {e}")
            print("❌ Error: Failed to import groundtruth module.")
            print("The evaluation dependencies are not installed.")
            print("")
            print("To fix this, install the evaluation dependencies:")
            print("  pip install .[eval]")
            print("")
            print("This will install required packages including:")
            print("  - anthropic (for Claude AI)")
            print("  - beautifulsoup4 (for HTML processing)")
            print("  - python-dotenv (for environment variables)")
            return

        # Initialize generator
        try:
            generator = GroundTruthGenerator(
                model=args.model, max_tokens=args.max_tokens
            )
        except Exception as e:
            log.error(f"Error initializing generator: {e}")
            print(f"Error initializing generator: {e}")
            return

        # Load custom prompt if provided
        custom_prompt = None
        if args.custom_prompt:
            try:
                with open(args.custom_prompt, "r", encoding="utf-8") as f:
                    custom_prompt = f.read().strip()
                print(f"Using custom prompt from: {args.custom_prompt}")
            except Exception as e:
                log.error(f"Error loading custom prompt: {e}")
                print(f"Error loading custom prompt: {e}")
                return

        save_text = not args.no_save_text

        # Convert use case string to enum
        use_case = UseCase(args.use_case)

        try:
            if args.file:
                # Process single file
                print(
                    f"Processing single file: {args.file} (use case: {use_case.value})"
                )
                result = generator.generate(
                    file_path=args.file,
                    use_case=use_case,
                    prompt=custom_prompt,
                    save_text=save_text,
                    output_dir=args.output_dir,
                    num_samples=args.num_samples,
                )
                print("✅ Successfully generated ground truth data")
                print(f"  Output: {args.output_dir}")
                usage = result["metadata"]["usage"]
                cost = result["metadata"]["cost"]
                print(
                    f"  Token usage: {usage['input_tokens']:,} input + {usage['output_tokens']:,} output = {usage['total_tokens']:,} total"
                )
                print(
                    f"  Cost: ${cost['input_cost']:.4f} input + ${cost['output_cost']:.4f} output = ${cost['total_cost']:.4f} total"
                )

                # Different output based on use case
                if use_case == UseCase.RAG:
                    qa_pairs_count = len(result["analysis"]["qa_pairs"])
                    print(
                        f"  Q&A pairs: {qa_pairs_count} (${cost['total_cost']/qa_pairs_count:.4f} per pair)"
                    )
                elif use_case == UseCase.SUMMARIZATION:
                    summary_count = len(result["analysis"]["summaries"])
                    print(
                        f"  Summary types generated: {summary_count} different formats"
                    )
                    print(
                        f"  Evaluation criteria: {len(result['analysis']['evaluation_criteria'])} categories"
                    )
                elif use_case == UseCase.QA:
                    qa_count = len(result["analysis"]["qa_pairs"])
                    print(f"  Q&A pairs generated: {qa_count} questions")
                    print(
                        f"  Evaluation criteria: {len(result['analysis']['evaluation_criteria'])} categories"
                    )

            elif args.directory:
                # Process directory
                print(
                    f"Processing directory: {args.directory} (use case: {use_case.value})"
                )
                print(f"File pattern: {args.pattern}")
                consolidated_data = generator.generate_batch(
                    input_dir=args.directory,
                    file_pattern=args.pattern,
                    use_case=use_case,
                    prompt=custom_prompt,
                    save_text=save_text,
                    output_dir=args.output_dir,
                    num_samples=args.num_samples,
                )

                if consolidated_data:
                    # Extract totals from consolidated metadata
                    total_usage = consolidated_data["metadata"]["total_usage"]
                    total_cost = consolidated_data["metadata"]["total_cost"]
                    files_processed = consolidated_data["metadata"]["consolidated_from"]

                    print(f"✅ Successfully processed {files_processed} files")
                    print(
                        f"  Output: {args.output_dir}/consolidated_{use_case.value}_groundtruth.json"
                    )
                    print(
                        f"  Total token usage: {total_usage['input_tokens']:,} input + {total_usage['output_tokens']:,} output = {total_usage['total_tokens']:,} total"
                    )
                    print(
                        f"  Total cost: ${total_cost['input_cost']:.4f} input + ${total_cost['output_cost']:.4f} output = ${total_cost['total_cost']:.4f} total"
                    )
                    print(
                        f"  Average cost per file: ${total_cost['total_cost']/files_processed:.4f}"
                    )

                    # Different summary stats based on use case
                    analysis = consolidated_data["analysis"]
                    if use_case == UseCase.RAG:
                        # For RAG, count total Q&A pairs across all documents
                        total_pairs = 0
                        if "qa_pairs" in analysis:
                            total_pairs = len(analysis["qa_pairs"])
                        print(f"  Total Q&A pairs: {total_pairs}")
                        if total_pairs > 0:
                            print(
                                f"  Average cost per Q&A pair: ${total_cost['total_cost']/total_pairs:.4f}"
                            )
                    elif use_case == UseCase.SUMMARIZATION:
                        summaries_count = len(analysis.get("summaries", {}))
                        print(
                            f"  Generated {files_processed} comprehensive transcript summaries"
                        )
                        print(
                            f"  Consolidated into single file with {summaries_count} transcript summaries"
                        )
                    elif use_case == UseCase.QA:
                        # For QA, count total Q&A pairs across all transcripts
                        total_qa_pairs = 0
                        if "qa_pairs" in analysis:
                            total_qa_pairs = len(analysis["qa_pairs"])
                        print(
                            f"  Generated {files_processed} transcript Q&A evaluations"
                        )
                        print(f"  Total Q&A pairs: {total_qa_pairs}")
                        if total_qa_pairs > 0:
                            print(
                                f"  Average cost per Q&A pair: ${total_cost['total_cost']/total_qa_pairs:.4f}"
                            )
                else:
                    print("No files were processed successfully")
                    return

        except Exception as e:
            log.error(f"Error during groundtruth processing: {e}")
            print(f"❌ Error during processing: {e}")
            return

        return

    # Handle template creation
    if args.action == "create-template":
        log.info("Creating template results file")
        try:
            from gaia.eval.eval import RagEvaluator
        except ImportError as e:
            log.error(f"Failed to import RagEvaluator: {e}")
            print("❌ Error: Failed to import eval module.")
            print("The evaluation dependencies are not installed.")
            print("")
            print("To fix this, install the evaluation dependencies:")
            print("  pip install .[eval]")
            print("")
            print("This will install required packages including:")
            print("  - anthropic (for Claude AI)")
            print("  - beautifulsoup4 (for HTML processing)")
            print("  - python-dotenv (for environment variables)")
            return

        try:
            evaluator = RagEvaluator()
            template_path = evaluator.create_template(
                groundtruth_file=args.groundtruth_file,
                output_dir=args.output_dir,
                similarity_threshold=args.threshold,
            )
            print("✅ Successfully created template file")
            print(f"  Template: {template_path}")
            print(
                "  Instructions: Fill in the 'response' fields with your RAG system outputs"
            )
            print("  Then run: gaia eval <template_file> to evaluate performance")

        except Exception as e:
            log.error(f"Error creating template: {e}")
            print(f"❌ Error creating template: {e}")
            return

        return

    # Handle RAG evaluation
    if args.action == "eval":
        log.info("Evaluating RAG system performance")
        try:
            from gaia.eval.eval import RagEvaluator
        except ImportError as e:
            log.error(f"Failed to import RagEvaluator: {e}")
            print("❌ Error: Failed to import eval module.")
            print("The evaluation dependencies are not installed.")
            print("")
            print("To fix this, install the evaluation dependencies:")
            print("  pip install .[eval]")
            print("")
            print("This will install required packages including:")
            print("  - anthropic (for Claude AI)")
            print("  - beautifulsoup4 (for HTML processing)")
            print("  - python-dotenv (for environment variables)")
            return

        try:
            evaluator = RagEvaluator(model=args.model)

            # If summary_only is True, don't save to output_dir (None)
            output_dir = None if args.summary_only else args.output_dir

            # Handle directory processing
            if args.directory:
                import glob

                # Find all JSON files in the directory
                json_pattern = os.path.join(args.directory, "*.json")
                json_files = glob.glob(json_pattern)

                if not json_files:
                    print(f"❌ No JSON files found in directory: {args.directory}")
                    return

                print(f"Found {len(json_files)} JSON files to process")

                total_files_processed = 0
                total_usage = {"total_tokens": 0}
                total_cost = {"total_cost": 0.0}

                for json_file in sorted(json_files):
                    print(f"\n📄 Processing: {os.path.basename(json_file)}")

                    try:
                        evaluation_data = evaluator.generate_enhanced_report(
                            results_path=json_file,
                            output_dir=output_dir,
                            groundtruth_path=getattr(args, "groundtruth", None),
                        )

                        total_files_processed += 1

                        # Display summary for this file
                        overall_rating = evaluation_data.get("overall_rating", {})
                        print(
                            f"  Overall Rating: {overall_rating.get('rating', 'N/A')}"
                        )

                        metrics = overall_rating.get("metrics", {})
                        if metrics:
                            print(f"  Questions: {metrics.get('num_questions', 'N/A')}")

                            pass_rate = metrics.get("pass_rate", "N/A")
                            if isinstance(pass_rate, (int, float)):
                                print(f"  Pass Rate: {pass_rate:.1%}")
                            else:
                                print(f"  Pass Rate: {pass_rate}")

                            mean_similarity = metrics.get("mean_similarity", "N/A")
                            if isinstance(mean_similarity, (int, float)):
                                print(f"  Mean Similarity: {mean_similarity:.3f}")
                            else:
                                print(f"  Mean Similarity: {mean_similarity}")

                        # Accumulate usage and cost
                        if evaluation_data.get("total_usage"):
                            file_usage = evaluation_data["total_usage"]
                            total_usage["total_tokens"] += file_usage.get(
                                "total_tokens", 0
                            )

                        if evaluation_data.get("total_cost"):
                            file_cost = evaluation_data["total_cost"]
                            total_cost["total_cost"] += file_cost.get("total_cost", 0.0)

                    except Exception as e:
                        log.error(f"Error processing {json_file}: {e}")
                        print(f"  ❌ Error: {e}")
                        continue

                print(
                    f"\n✅ Successfully processed {total_files_processed}/{len(json_files)} files"
                )

                if not args.summary_only and total_files_processed > 0:
                    print(f"  Detailed Reports: {args.output_dir}")

                # Print total cost information
                if total_usage["total_tokens"] > 0:
                    print(f"  Total Token Usage: {total_usage['total_tokens']:,}")
                if total_cost["total_cost"] > 0:
                    print(f"  Total Cost: ${total_cost['total_cost']:.4f}")

            else:
                # Handle single file processing (existing logic)
                evaluation_data = evaluator.generate_enhanced_report(
                    results_path=args.results_file,
                    output_dir=output_dir,
                    groundtruth_path=getattr(args, "groundtruth", None),
                )

                print("✅ Successfully evaluated RAG system")

                # Display summary information
                overall_rating = evaluation_data.get("overall_rating", {})
                print(f"  Overall Rating: {overall_rating.get('rating', 'N/A')}")

                metrics = overall_rating.get("metrics", {})
                if metrics:
                    print(f"  Questions: {metrics.get('num_questions', 'N/A')}")

                    pass_rate = metrics.get("pass_rate", "N/A")
                    if isinstance(pass_rate, (int, float)):
                        print(f"  Pass Rate: {pass_rate:.1%}")
                    else:
                        print(f"  Pass Rate: {pass_rate}")

                    mean_similarity = metrics.get("mean_similarity", "N/A")
                    if isinstance(mean_similarity, (int, float)):
                        print(f"  Mean Similarity: {mean_similarity:.3f}")
                    else:
                        print(f"  Mean Similarity: {mean_similarity}")

                if not args.summary_only:
                    print(f"  Detailed Report: {args.output_dir}")

                # Print cost information if available
                if evaluation_data.get("total_usage") and evaluation_data.get(
                    "total_cost"
                ):
                    total_usage = evaluation_data["total_usage"]
                    total_cost = evaluation_data["total_cost"]
                    print(f"  Token Usage: {total_usage['total_tokens']:,} total")
                    print(f"  Cost: ${total_cost['total_cost']:.4f}")

        except Exception as e:
            log.error(f"Error evaluating RAG system: {e}")
            print(f"❌ Error evaluating RAG system: {e}")
            return

        return

    # Handle generate command
    if args.action == "generate":
        if args.meeting_transcript:
            log.info("Generating example meeting transcripts")
            try:
                from gaia.eval.transcript_generator import TranscriptGenerator
            except ImportError as e:
                log.error(f"Failed to import TranscriptGenerator: {e}")
                print("❌ Error: Failed to import transcript generator module.")
                print("The evaluation dependencies are not installed.")
                print("")
                print("To fix this, install the evaluation dependencies:")
                print("  pip install .[eval]")
                print("")
                print("This will install required packages including:")
                print("  - anthropic (for Claude AI)")
                print("  - beautifulsoup4 (for HTML processing)")
                print("  - python-dotenv (for environment variables)")
                return

            try:
                generator = TranscriptGenerator(claude_model=args.claude_model)

                # Filter meeting types if specified
                if args.meeting_types:
                    # Temporarily filter the templates
                    original_templates = generator.meeting_templates.copy()
                    generator.meeting_templates = {
                        k: v
                        for k, v in generator.meeting_templates.items()
                        if k in args.meeting_types
                    }

                # Set default target tokens for transcripts if not specified
                target_tokens = args.target_tokens if args.target_tokens else 1000

                result = generator.generate_transcript_set(
                    output_dir=args.output_dir,
                    target_tokens=target_tokens,
                    count_per_type=args.count_per_type,
                )

                print("✅ Successfully generated meeting transcripts")
                print(f"  Output directory: {result['output_directory']}")
                print(f"  Generated files: {len(result['generated_files'])}")
                print(f"  Metadata file: {result['metadata_file']}")

                # Show summary stats
                summary = result["summary"]
                generation_info = summary["generation_info"]
                total_tokens = generation_info["total_claude_usage"]["total_tokens"]
                total_cost = generation_info["total_claude_cost"]["total_cost"]
                avg_tokens = (
                    total_tokens / len(summary["transcripts"])
                    if summary["transcripts"]
                    else 0
                )

                print(f"  Total tokens used: {total_tokens:,}")
                print(f"  Total cost: ${total_cost:.4f}")
                print(f"  Average tokens per file: {avg_tokens:.0f}")
                print(
                    f"  Average cost per file: ${total_cost/len(summary['transcripts']):.4f}"
                )
                print(f"  Meeting types: {', '.join(generation_info['meeting_types'])}")
                print(f"  Claude model: {generation_info['claude_model']}")

                # Restore original templates if they were filtered
                if args.meeting_types:
                    generator.meeting_templates = original_templates

            except Exception as e:
                log.error(f"Error generating transcripts: {e}")
                print(f"❌ Error generating transcripts: {e}")
                return

        elif args.email:
            log.info("Generating example business emails")
            try:
                from gaia.eval.email_generator import EmailGenerator
            except ImportError as e:
                log.error(f"Failed to import EmailGenerator: {e}")
                print("❌ Error: Failed to import email generator module.")
                print("The evaluation dependencies are not installed.")
                print("")
                print("To fix this, install the evaluation dependencies:")
                print("  pip install .[eval]")
                print("")
                print("This will install required packages including:")
                print("  - anthropic (for Claude AI)")
                print("  - beautifulsoup4 (for HTML processing)")
                print("  - python-dotenv (for environment variables)")
                return

            try:
                generator = EmailGenerator(claude_model=args.claude_model)

                # Filter email types if specified
                if args.email_types:
                    # Temporarily filter the templates
                    original_templates = generator.email_templates.copy()
                    generator.email_templates = {
                        k: v
                        for k, v in generator.email_templates.items()
                        if k in args.email_types
                    }

                # Set default target tokens for emails if not specified
                target_tokens = args.target_tokens if args.target_tokens else 800

                result = generator.generate_email_set(
                    output_dir=args.output_dir,
                    target_tokens=target_tokens,
                    count_per_type=args.count_per_type,
                )

                print("✅ Successfully generated business emails")
                print(f"  Output directory: {result['output_directory']}")
                print(f"  Generated files: {len(result['generated_files'])}")
                print(f"  Metadata file: {result['metadata_file']}")

                # Show summary stats
                summary = result["summary"]
                generation_info = summary["generation_info"]
                total_tokens = generation_info["total_claude_usage"]["total_tokens"]
                total_cost = generation_info["total_claude_cost"]["total_cost"]
                avg_tokens = (
                    total_tokens / len(summary["emails"]) if summary["emails"] else 0
                )

                print(f"  Total tokens used: {total_tokens:,}")
                print(f"  Total cost: ${total_cost:.4f}")
                print(f"  Average tokens per file: {avg_tokens:.0f}")
                print(
                    f"  Average cost per file: ${total_cost/len(summary['emails']):.4f}"
                )
                print(f"  Email types: {', '.join(generation_info['email_types'])}")
                print(f"  Claude model: {generation_info['claude_model']}")

                # Restore original templates if they were filtered
                if args.email_types:
                    generator.email_templates = original_templates

            except Exception as e:
                log.error(f"Error generating emails: {e}")
                print(f"❌ Error generating emails: {e}")
                return

        return

    # Handle batch-experiment command
    if args.action == "batch-experiment":
        log.info("Running batch experiments")
        try:
            from gaia.eval.batch_experiment import BatchExperimentRunner
        except ImportError as e:
            log.error(f"Failed to import BatchExperimentRunner: {e}")
            print("❌ Error: Failed to import batch experiment module.")
            print("The evaluation dependencies are not installed.")
            print("")
            print("To fix this, install the evaluation dependencies:")
            print("  pip install .[eval]")
            print("")
            print("This will install required packages including:")
            print("  - anthropic (for Claude AI)")
            print("  - beautifulsoup4 (for HTML processing)")
            print("  - python-dotenv (for environment variables)")
            return

        # Create sample config if requested
        if args.create_sample_config:
            runner = BatchExperimentRunner.__new__(BatchExperimentRunner)
            runner.log = get_logger(__name__)
            runner.create_sample_config(args.create_sample_config)
            print(f"✅ Sample configuration created: {args.create_sample_config}")
            print("Edit this file to define your experiments, then run:")
            print(
                f"  gaia batch-experiment -c {args.create_sample_config} -i <input_path> -o <output_dir>"
            )
            return

        # Create config from groundtruth if requested
        if args.create_config_from_groundtruth:
            # Determine output filename if not provided in the argument
            groundtruth_path = Path(args.create_config_from_groundtruth)
            default_output = f"{groundtruth_path.stem}.config.json"

            runner = BatchExperimentRunner.__new__(BatchExperimentRunner)
            runner.log = get_logger(__name__)
            try:
                config_path = runner.create_config_from_groundtruth(
                    args.create_config_from_groundtruth, default_output
                )
                print(
                    f"✅ Configuration created from groundtruth metadata: {config_path}"
                )
                print("Review and edit the configuration, then run:")
                print(
                    f"  gaia batch-experiment -c {config_path} -i <input_path> -o <output_dir>"
                )
            except Exception as e:
                print(f"❌ Error creating config from groundtruth: {e}")
                return
            return

        # Validate required arguments
        if not args.config or not args.input:
            print(
                "❌ Error: Both --config and --input are required (unless using --create-sample-config or --create-config-from-groundtruth)"
            )
            return

        try:
            # Run batch experiments
            runner = BatchExperimentRunner(args.config)
            result_files = runner.run_all_experiments(
                input_path=args.input,
                output_dir=args.output_dir,
                delay_seconds=args.delay,
                queries_source=args.queries_source,
            )

            print(f"✅ Completed {len(result_files)} experiments")
            print(f"  Results saved to: {args.output_dir}")
            print("  Generated files:")
            for result_file in result_files:
                print(f"    - {Path(result_file).name}")

            print("\nNext steps:")
            print("  1. Evaluate results using: gaia eval -f <result_file>")
            print(f"  2. Generate comparative report: gaia report -d {args.output_dir}")

        except Exception as e:
            log.error(f"Error running batch experiments: {e}")
            print(f"❌ Error running batch experiments: {e}")
            return

        return

    # Handle Blender command
    if args.action == "blender":
        handle_blender_command(args)
        return

    # Handle visualize command
    if args.action == "visualize":
        handle_visualize_command(args)
        return

    # Log error for unknown action
    log.error(f"Unknown action specified: {args.action}")
    parser.print_help()
    return


def kill_process_by_port(port):
    """Find and kill a process running on a specific port."""
    try:
        # For Windows
        if sys.platform.startswith("win"):
            cmd = f"netstat -ano | findstr :{port}"
            output = subprocess.check_output(cmd, shell=True).decode()
            if output:
                # Split output into lines and process each line
                for line in output.strip().split("\n"):
                    # Only process lines that contain the specific port
                    if f":{port}" in line:
                        parts = line.strip().split()
                        # Get the last part which should be the PID
                        try:
                            pid = int(parts[-1])
                            if pid > 0:  # Ensure we don't try to kill PID 0
                                # Add check=True to subprocess.run
                                subprocess.run(
                                    f"taskkill /PID {pid} /F", shell=True, check=True
                                )
                                return {
                                    "success": True,
                                    "message": f"Killed process {pid} running on port {port}",
                                }
                        except (IndexError, ValueError):
                            continue
                return {
                    "success": False,
                    "message": f"Could not find valid PID for port {port}",
                }
        return {"success": False, "message": f"No process found running on port {port}"}
    except subprocess.CalledProcessError:
        return {"success": False, "message": f"No process found running on port {port}"}
    except Exception as e:
        return {
            "success": False,
            "message": f"Error killing process on port {port}: {str(e)}",
        }


def wait_for_user():
    """Wait for user to press Enter before continuing."""
    input("Press Enter to continue to the next example...")


def run_blender_examples(agent, selected_example=None, print_result=True):
    """
    Run the Blender agent example demonstrations.

    Args:
        agent: The BlenderAgent instance
        selected_example: Optional example number to run specifically
        print_result: Whether to print the result
    """
    console = agent.console

    examples = {
        1: {
            "name": "Clearing the scene",
            "description": "This example demonstrates how to clear all objects from a scene.",
            "query": "Clear the scene to start fresh",
        },
        2: {
            "name": "Creating a basic cube",
            "description": "This example creates a red cube at the center of the scene.",
            "query": "Create a red cube at the center of the scene and make sure it has a red material",
        },
        3: {
            "name": "Creating a sphere with specific properties",
            "description": "This example creates a blue sphere with specific parameters.",
            "query": "Create a blue sphere at position (3, 0, 0) and set its scale to (2, 2, 2)",
        },
        4: {
            "name": "Creating multiple objects",
            "description": "This example creates multiple objects with specific arrangements.",
            "query": "Create a green cube at (0, 0, 0) and a red sphere 3 units above it",
        },
        5: {
            "name": "Creating and modifying objects",
            "description": "This example creates objects and then modifies them.",
            "query": "Create a blue cylinder, then make it taller and move it up 2 units",
        },
    }

    # If a specific example is requested, run only that one
    if selected_example and selected_example in examples:
        example = examples[selected_example]
        console.print_header(f"=== Example {selected_example}: {example['name']} ===")
        console.print_header(example["description"])
        agent.process_query(example["query"])
        agent.display_result(print_result=print_result)
        return

    # Run all examples in sequence
    for idx, example in examples.items():
        console.print_header(f"=== Example {idx}: {example['name']} ===")
        console.print_header(example["description"])
        agent.process_query(example["query"], output_to_file=True)
        agent.display_result(print_result=print_result)

        # Wait for user input between examples, except the last one
        if idx < len(examples):
            wait_for_user()


def run_blender_interactive_mode(agent, print_result=True):
    """
    Run the Blender Agent in interactive mode where the user can continuously input queries.

    Args:
        agent: The BlenderAgent instance
        print_result: Whether to print the result
    """
    console = agent.console
    console.print_header("=== Blender Interactive Mode ===")
    console.print_header(
        "Enter your 3D scene queries. Type 'exit', 'quit', or 'q' to exit."
    )

    while True:
        try:
            query = input("\nEnter Blender query: ")
            if query.lower() in ["exit", "quit", "q"]:
                console.print_header("Exiting Blender interactive mode.")
                break

            if query.strip():  # Process only non-empty queries
                agent.process_query(query)
                agent.display_result(print_result=print_result)

        except KeyboardInterrupt:
            console.print_header("\nBlender interactive mode interrupted. Exiting.")
            break
        except Exception as e:
            console.print_error(f"Error processing Blender query: {e}")


def handle_visualize_command(args):
    """
    Handle the evaluation results visualizer command.

    Args:
        args: Parsed command line arguments for the visualize command
    """
    log = get_logger(__name__)

    try:
        import webbrowser
        import socket
    except ImportError as e:
        log.error(f"Failed to import required modules: {e}")
        print("❌ Error: Failed to import required modules for visualizer")
        return

    # Determine workspace and data directories
    workspace_dir = Path(args.workspace) if args.workspace else Path.cwd()
    experiments_dir = (
        Path(args.experiments_dir)
        if args.experiments_dir
        else workspace_dir / "experiments"
    )
    evaluations_dir = (
        Path(args.evaluations_dir)
        if args.evaluations_dir
        else workspace_dir / "evaluation"
    )

    # Get the webapp directory
    webapp_dir = Path(__file__).parent / "eval" / "webapp"

    if not webapp_dir.exists():
        print("❌ Error: Evaluation webapp not found")
        print(f"Expected location: {webapp_dir}")
        return

    # Check if Node.js is available
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: Node.js is not installed or not in PATH")
        print("The evaluation visualizer requires Node.js to run.")
        print("Please install Node.js from https://nodejs.org/")
        return

    # Check if dependencies are installed
    node_modules_dir = webapp_dir / "node_modules"
    if not node_modules_dir.exists():
        print("📦 Installing webapp dependencies...")
        try:
            subprocess.run(
                ["npm", "install"],
                cwd=webapp_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print("❌ Error: Failed to install webapp dependencies")
            print(f"Error: {e.stderr}")
            return

    # Check if port is available
    def is_port_available(host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0

    if not is_port_available(args.host, args.port):
        print(f"❌ Error: Port {args.port} is already in use")
        print("Try using a different port with --port <port_number>")
        return

    # Set up environment variables for the webapp
    env = os.environ.copy()
    env["PORT"] = str(args.port)
    env["EXPERIMENTS_PATH"] = str(experiments_dir.absolute())
    env["EVALUATIONS_PATH"] = str(evaluations_dir.absolute())

    print("🚀 Starting evaluation results visualizer...")
    print(f"   Workspace: {workspace_dir.absolute()}")
    print(f"   Experiments: {experiments_dir.absolute()}")
    print(f"   Evaluations: {evaluations_dir.absolute()}")
    print(f"   Server: http://{args.host}:{args.port}")

    # Start the Node.js server
    try:
        server_process = subprocess.Popen(
            ["node", "server.js"],
            cwd=webapp_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        # Wait a moment for server to start
        time.sleep(2)

        # Check if server started successfully
        if server_process.poll() is not None:
            output, _ = server_process.communicate()
            print("❌ Error: Failed to start webapp server")
            print(f"Server output: {output}")
            return

        # Open browser if requested
        if not args.no_browser:
            url = f"http://{args.host}:{args.port}"
            try:
                webbrowser.open(url)
                print(f"🌐 Opened browser at {url}")
            except Exception as e:
                print(f"⚠️  Could not open browser automatically: {e}")
                print(f"   Please open {url} manually")

        print("\n📊 Evaluation Results Visualizer is running!")
        print(f"   Access at: http://{args.host}:{args.port}")
        print("   Press Ctrl+C to stop the server")

        # Stream server output
        try:
            for line in iter(server_process.stdout.readline, ""):
                if line.strip():
                    print(f"[SERVER] {line.rstrip()}")
        except KeyboardInterrupt:
            pass

    except KeyboardInterrupt:
        print("\n⏹️  Stopping evaluation visualizer...")
    except Exception as e:
        log.error(f"Error running visualizer: {e}")
        print(f"❌ Error: {e}")
    finally:
        # Clean up server process
        try:
            if "server_process" in locals():
                server_process.terminate()
                server_process.wait(timeout=5)
                print("✅ Server stopped successfully")
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("⚠️  Server force-killed")
        except Exception as e:
            print(f"⚠️  Error stopping server: {e}")


def handle_blender_command(args):
    """
    Handle the Blender agent command.

    Args:
        args: Parsed command line arguments for the blender command
    """
    log = get_logger(__name__)

    # Check if Lemonade server is running
    log.info("Checking Lemonade server connectivity...")
    if not check_lemonade_health():
        print_lemonade_error()
        sys.exit(1)
    log.info("✅ Lemonade server is accessible")

    # Check if Blender MCP server is running
    mcp_port = getattr(args, "mcp_port", 9876)
    log.info(f"Checking Blender MCP server connectivity on port {mcp_port}...")
    if not check_mcp_health(port=mcp_port):
        print_mcp_error()
        print(f"Note: Checking for MCP server on port {mcp_port}", file=sys.stderr)
        sys.exit(1)
    log.info("✅ Blender MCP server is accessible")

    # Create output directory if specified
    output_dir = args.output_dir
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        # Create MCP client with custom port if specified
        mcp_client = MCPClient(host="localhost", port=mcp_port)

        # Create the BlenderAgent
        agent = BlenderAgent(
            use_local_llm=True,
            mcp=mcp_client,
            model_id=args.model,
            max_steps=args.steps,
            output_dir=output_dir,
            streaming=args.stream,
            show_stats=args.stats,
            debug_prompts=args.debug_prompts,
        )

        # Run in interactive mode if specified
        if args.interactive:
            run_blender_interactive_mode(agent, print_result=args.print_result)
        # Process a custom query if provided
        elif args.query:
            agent.console.print_header(f"Processing Blender query: '{args.query}'")
            agent.process_query(args.query)
            agent.display_result(print_result=args.print_result)
        # Run specific example if provided, otherwise run all examples
        else:
            run_blender_examples(
                agent, selected_example=args.example, print_result=args.print_result
            )

    except Exception as e:
        log.error(f"Error running Blender agent: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
