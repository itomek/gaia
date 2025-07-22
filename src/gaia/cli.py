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
        model="llama3.2:1b",
        max_new_tokens=512,
        whisper_model_size="base",
        audio_device_index=1,
        silence_threshold=0.5,
        show_stats=False,
        enable_tts=True,
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
        self.max_new_tokens = max_new_tokens
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

        self.log.info("Gaia CLI client initialized.")
        self.log.debug(
            f"agent_name: {self.agent_name}\n host: {self.host}\n"
            f"port: {self.port}\n llm_port: {self.llm_port}\n"
            f"model: {self.model}\n max_new_tokens: {self.max_new_tokens}"
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

    async def chat(self):
        """Text-based chat interface"""
        print(
            f"Starting text chat with {self.agent_name}.\n"
            "Type 'stop' to quit or 'restart' to clear chat history."
        )
        while True:
            user_input = input("You: ").strip()
            if user_input.lower().rstrip(".") == "stop":
                break
            elif user_input.lower().rstrip(".") == "restart":
                print("Chat restart functionality not implemented")
            else:
                print(f"{self.agent_name}:", end=" ", flush=True)
                async for _ in self.send_message(user_input):
                    pass
                print()

    async def talk(self):
        """Voice-based chat interface"""
        self.audio_client.initialize_tts()
        await self.start_voice_chat()

    async def prompt(self, message):
        async for chunk in self.send_message(message):
            yield chunk


async def async_main(action, **kwargs):
    log = get_logger(__name__)

    # Check Lemonade health for all actions that require it
    if action in ["prompt", "chat", "talk", "stats"]:
        if not check_lemonade_health():
            print_lemonade_error()
            sys.exit(1)

    # All actions now require a client since we assume Lemonade is running
    client = GaiaCliClient(**{k: v for k, v in kwargs.items() if k != "message"})

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
        await client.chat()
        log.info("Chat session ended.")
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
        default="llama3.2:1b",
        help="Model to use for the agent (default: llama3.2:1b)",
    )
    prompt_parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=512,
        help="Maximum number of new tokens to generate (default: 512)",
    )
    prompt_parser.add_argument(
        "--stats",
        action="store_true",
        help="Show performance statistics after generation",
    )

    chat_parser = subparsers.add_parser(
        "chat", help="Start text conversation with Gaia", parents=[parent_parser]
    )
    chat_parser.add_argument(
        "--agent-name",
        default="Chaty",
        help="Name of the Gaia agent to use (e.g., Llm, Chaty, Joker, Clip, Rag, etc.)",
    )
    chat_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address for the Agent server (default: 127.0.0.1)",
    )
    chat_parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for the Agent server (default: 8001)",
    )
    chat_parser.add_argument(
        "--model",
        default="llama3.2:1b",
        help="Model to use for the agent (default: llama3.2:1b)",
    )
    chat_parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=512,
        help="Maximum number of new tokens to generate (default: 512)",
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
        default="llama3.2:1b",
        help="Model to use for the agent (default: llama3.2:1b)",
    )
    talk_parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=512,
        help="Maximum number of new tokens to generate (default: 512)",
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
        help="Generate ground truth data for RAG evaluation",
        parents=[parent_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single file
  gaia-cli groundtruth -f ./data/html/blender/introduction.html

  # Process all HTML files in a directory
  gaia-cli groundtruth -d ./data/html/blender

  # Process with custom output directory
  gaia-cli groundtruth -f ./data/html/intro.html -o ./output/gt

  # Process with custom file pattern
  gaia-cli groundtruth -d ./data -p "*.pdf" -o ./output/gt

  # Use custom Claude model
  gaia-cli groundtruth -f ./data/doc.html -m claude-3-opus-20240229

  # Generate 10 Q&A pairs per document
  gaia-cli groundtruth -d ./data/html/blender --num-samples 10
        """,
    )

    # Input source (mutually exclusive)
    gt_input_group = gt_parser.add_mutually_exclusive_group(required=True)
    gt_input_group.add_argument(
        "-f", "--file", type=str, help="Path to a single document file to process"
    )
    gt_input_group.add_argument(
        "-d", "--directory", type=str, help="Directory containing documents to process"
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
        default="*.html",
        help="File pattern to match when processing directory (default: *.html)",
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
        help="Number of Q&A pairs to generate per document (default: 5)",
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
  gaia-cli create-template -f ./output/groundtruth/introduction.groundtruth.json

  # Create template with custom output path
  gaia-cli create-template -f ./output/groundtruth/doc.groundtruth.json -o ./templates/

  # Create template with custom similarity threshold
  gaia-cli create-template -f ./output/groundtruth/doc.groundtruth.json --threshold 0.8
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
  # Evaluate RAG results file
  gaia-cli eval -f ./output/templates/introduction.template.json

  # Evaluate with custom output directory
  gaia-cli eval -f ./output/rag/results.json -o ./output/eval

  # Evaluate with specific Claude model
  gaia-cli eval -f ./output/rag/results.json -m claude-3-opus-20240229

  # Evaluate and display summary only (no detailed report file)
  gaia-cli eval -f ./output/rag/results.json --summary-only
        """,
    )

    eval_parser.add_argument(
        "-f",
        "--results-file",
        type=str,
        required=True,
        help="Path to the RAG results JSON file (template or results)",
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
  gaia-cli report -d ./output/eval

  # Generate report with custom output filename
  gaia-cli report -d ./output/eval -o Model_Comparison_Report.md

  # Generate report and display summary only
  gaia-cli report -d ./output/eval --summary-only
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
            print(
                "Error: Failed to import eval module. Please ensure all dependencies are installed."
            )
            return

        try:
            evaluator = RagEvaluator()

            # If summary_only is True, don't save the report file
            output_path = None if args.summary_only else args.output_file

            result = evaluator.generate_summary_report(
                eval_dir=args.eval_dir, output_path=output_path or "temp_report.md"
            )

            print(
                f"✓ Successfully analyzed {result['models_analyzed']} evaluation files"
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
            from gaia.eval.groundtruth import GroundTruthGenerator
        except ImportError as e:
            log.error(f"Failed to import GroundTruthGenerator: {e}")
            print(
                "❌ Error: Failed to import groundtruth module. Please ensure all dependencies are installed."
            )
            return

        # Initialize generator
        try:
            generator = GroundTruthGenerator(
                model=args.model, max_tokens=args.max_tokens
            )
        except Exception as e:
            log.error(f"Error initializing generator: {e}")
            print(f"❌ Error initializing generator: {e}")
            return

        # Load custom prompt if provided
        custom_prompt = None
        if args.custom_prompt:
            try:
                with open(args.custom_prompt, "r", encoding="utf-8") as f:
                    custom_prompt = f.read().strip()
                print(f"✅ Using custom prompt from: {args.custom_prompt}")
            except Exception as e:
                log.error(f"Error loading custom prompt: {e}")
                print(f"❌ Error loading custom prompt: {e}")
                return

        save_text = not args.no_save_text

        try:
            if args.file:
                # Process single file
                print(f"Processing single file: {args.file}")
                result = generator.generate(
                    file_path=args.file,
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
                print(
                    f"  QA pairs: {len(result['analysis']['qa_pairs'])} (${cost['total_cost']/len(result['analysis']['qa_pairs']):.4f} per pair)"
                )

            elif args.directory:
                # Process directory
                print(f"Processing directory: {args.directory}")
                print(f"File pattern: {args.pattern}")
                results = generator.generate_batch(
                    input_dir=args.directory,
                    file_pattern=args.pattern,
                    prompt=custom_prompt,
                    save_text=save_text,
                    output_dir=args.output_dir,
                    num_samples=args.num_samples,
                )

                if results:
                    total_pairs = sum(len(r["analysis"]["qa_pairs"]) for r in results)
                    total_usage = {
                        "input_tokens": sum(
                            r["metadata"]["usage"]["input_tokens"] for r in results
                        ),
                        "output_tokens": sum(
                            r["metadata"]["usage"]["output_tokens"] for r in results
                        ),
                        "total_tokens": sum(
                            r["metadata"]["usage"]["total_tokens"] for r in results
                        ),
                    }
                    total_cost = {
                        "input_cost": sum(
                            r["metadata"]["cost"]["input_cost"] for r in results
                        ),
                        "output_cost": sum(
                            r["metadata"]["cost"]["output_cost"] for r in results
                        ),
                        "total_cost": sum(
                            r["metadata"]["cost"]["total_cost"] for r in results
                        ),
                    }
                    print(f"✓ Successfully processed {len(results)} files")
                    print(f"  Output: {args.output_dir}")
                    print(f"  Total QA pairs: {total_pairs}")
                    print(
                        f"  Total token usage: {total_usage['input_tokens']:,} input + {total_usage['output_tokens']:,} output = {total_usage['total_tokens']:,} total"
                    )
                    print(
                        f"  Total cost: ${total_cost['input_cost']:.4f} input + ${total_cost['output_cost']:.4f} output = ${total_cost['total_cost']:.4f} total"
                    )
                    print(
                        f"  Average cost per file: ${total_cost['total_cost']/len(results):.4f}"
                    )
                    print(
                        f"  Average cost per QA pair: ${total_cost['total_cost']/total_pairs:.4f}"
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
            print(
                "❌ Error: Failed to import eval module. Please ensure all dependencies are installed."
            )
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
            print(
                "  Then run: gaia-cli eval -f <template_file> to evaluate performance"
            )

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
            print(
                "❌ Error: Failed to import eval module. Please ensure all dependencies are installed."
            )
            return

        try:
            evaluator = RagEvaluator(model=args.model)

            # If summary_only is True, don't save to output_dir (None)
            output_dir = None if args.summary_only else args.output_dir

            evaluation_data = evaluator.generate_enhanced_report(
                results_path=args.results_file, output_dir=output_dir
            )

            print("✅ Successfully evaluated RAG system")

            # Display summary information
            overall_rating = evaluation_data.get("overall_rating", {})
            print(f"  Overall Rating: {overall_rating.get('rating', 'N/A')}")

            metrics = overall_rating.get("metrics", {})
            if metrics:
                print(f"  Questions: {metrics.get('num_questions', 'N/A')}")
                print(f"  Pass Rate: {metrics.get('pass_rate', 'N/A'):.1%}")
                print(f"  Mean Similarity: {metrics.get('mean_similarity', 'N/A'):.3f}")

            if not args.summary_only:
                print(f"  Detailed Report: {args.output_dir}")

            # Print cost information if available
            if evaluation_data.get("total_usage") and evaluation_data.get("total_cost"):
                total_usage = evaluation_data["total_usage"]
                total_cost = evaluation_data["total_cost"]
                print(f"  Token Usage: {total_usage['total_tokens']:,} total")
                print(f"  Cost: ${total_cost['total_cost']:.4f}")

        except Exception as e:
            log.error(f"Error evaluating RAG system: {e}")
            print(f"❌ Error evaluating RAG system: {e}")
            return

        return

    # Handle Blender command
    if args.action == "blender":
        handle_blender_command(args)
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
