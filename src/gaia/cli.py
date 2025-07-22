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

import requests
import aiohttp
from aiohttp import ClientTimeout

from gaia.logger import get_logger
from gaia.audio.audio_client import AudioClient

from gaia.version import version

# Set debug level for the logger
logging.getLogger("gaia").setLevel(logging.INFO)

# Add the parent directory to sys.path to import gaia modules
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent.parent
sys.path.append(str(parent_dir))


def check_lemonade_health(host="127.0.0.1", port=8000):
    """Check if Lemonade server is running and healthy."""
    log = get_logger(__name__)
    url = f"http://{host}:{port}/health"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            log.debug("Lemonade server is healthy")
            return True
        else:
            log.warning(f"Lemonade server returned status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        log.debug(f"Failed to connect to Lemonade server: {str(e)}")
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
    print("Then try your command again.", file=sys.stderr)


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
                            print(f"\n✅ Transcribed: {text}")
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
        if args.download_youtube_transcript:
            log.info(f"Downloading transcript from {args.download_youtube_transcript}")
            from llama_index.readers.youtube_transcript import YoutubeTranscriptReader

            doc = YoutubeTranscriptReader().load_data(
                ytlinks=[args.download_youtube_transcript]
            )
            output_path = args.output_transcript_path or "transcript.txt"
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
                print(f"  Token count: {result['metadata']['token_count']}")
                print(f"  QA pairs: {len(result['analysis']['qa_pairs'])}")

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
                    total_tokens = sum(r["metadata"]["token_count"] for r in results)
                    print(f"✅ Successfully processed {len(results)} files")
                    print(f"  Output: {args.output_dir}")
                    print(f"  Total QA pairs: {total_pairs}")
                    print(f"  Total tokens: {total_tokens}")
                else:
                    print("❌ No files were processed successfully")
                    return

        except Exception as e:
            log.error(f"Error during groundtruth processing: {e}")
            print(f"❌ Error during processing: {e}")
            return

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


if __name__ == "__main__":
    main()
