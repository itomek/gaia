#!/usr/bin/env python3
"""
Simple Chat App with conversation history using the existing LLMClient wrapper.
"""

import argparse
import sys
from collections import deque
from typing import Optional, List

from gaia.logger import get_logger
from gaia.llm.llm_client import LLMClient
from gaia.agents.chat.prompts import Prompts


class ChatApp:
    """Simple Chat application with conversation history using LLMClient."""

    def __init__(
        self, system_prompt: Optional[str] = None, model: Optional[str] = None
    ):
        """Initialize the Chat app."""
        self.log = get_logger(__name__)
        # Don't pass system_prompt to LLMClient since we handle it through prompts.py
        self.client = LLMClient(use_local=True, system_prompt=None)
        self.custom_system_prompt = system_prompt
        # Use Llama-3.2-3B-Instruct-Hybrid as default model
        self.model = model or "Llama-3.2-3B-Instruct-Hybrid"

        # Store conversation history
        self.n_chat_messages = 4
        self.chat_history = deque(
            maxlen=self.n_chat_messages * 2
        )  # Store both user and assistant messages in format expected by prompts.py

        self.log.debug("Chat app initialized")

    def _format_history_for_context(self, model: Optional[str] = None) -> str:
        """Format chat history for inclusion in LLM context using model-specific formatting."""
        model_name = model or self.model

        # Convert deque to list format expected by Prompts
        history_list = list(self.chat_history)

        # Use prompts.py for proper model-specific formatting
        return Prompts.format_chat_history(model_name, history_list)

    def send_message(
        self,
        user_message: str,
        model: Optional[str] = None,
        max_tokens: int = 512,
        stream: bool = False,
        **kwargs,
    ) -> str:
        """Send a message and get response, maintaining conversation history."""
        if not user_message.strip():
            raise ValueError("Message cannot be empty")

        self.log.debug(f"Processing message with model: {model or 'default'}")

        # Add user message to history in format expected by prompts.py
        self.chat_history.append(f"user: {user_message.strip()}")

        # Prepare prompt with conversation context using model-specific formatting
        model_to_use = model or self.model
        full_prompt = self._format_history_for_context(model_to_use)

        # Debug: Log the formatted prompt to see what's being sent
        self.log.debug(f"Full prompt being sent to LLM:\n{full_prompt}")

        # Prepare arguments
        generate_kwargs = dict(kwargs)
        if max_tokens:
            generate_kwargs["max_tokens"] = max_tokens

        # Generate response
        response = self.client.generate(
            prompt=full_prompt, model=model_to_use, stream=stream, **generate_kwargs
        )

        if stream:
            # Handle streaming response
            full_response = ""
            for chunk in response:
                full_response += chunk
            assistant_message = full_response
        else:
            assistant_message = response

        # Add assistant message to history in format expected by prompts.py
        self.chat_history.append(f"assistant: {assistant_message}")

        return assistant_message

    def get_history(self) -> List[str]:
        """Get the current conversation history."""
        return list(self.chat_history)

    def clear_history(self):
        """Clear the conversation history."""
        self.chat_history.clear()
        self.log.debug("Chat history cleared")

    def start_interactive_chat(
        self, model: Optional[str] = None, max_tokens: int = 512, **kwargs
    ):
        """Start an interactive chat session."""
        print("=" * 50)
        print("Interactive Chat Session Started")
        current_model = model or self.model
        print(f"Using model: {current_model}")
        print("Type 'quit', 'exit', or 'bye' to end the conversation")
        print("Commands:")
        print("  /clear    - clear conversation history")
        print("  /history  - show conversation history")
        print("  /system   - show current system prompt")
        print("  /model    - show current model info")
        print("  /prompt   - show complete formatted prompt")
        print("  /stats    - show performance statistics")
        print("  /help     - show this help message")
        print("=" * 50)

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ["quit", "exit", "bye"]:
                    print("\nGoodbye!")
                    break
                elif user_input.lower() == "/clear":
                    self.clear_history()
                    print("Conversation history cleared.")
                    continue
                elif user_input.lower() == "/history":
                    self._display_history()
                    continue
                elif user_input.lower() == "/system":
                    self._display_system_prompt()
                    continue
                elif user_input.lower() == "/model":
                    self._display_model_info()
                    continue
                elif user_input.lower() == "/prompt":
                    self._display_complete_prompt()
                    continue
                elif user_input.lower() == "/stats":
                    self._display_stats()
                    continue
                elif user_input.lower() == "/help":
                    self._display_help()
                    continue
                elif not user_input:
                    print("Please enter a message.")
                    continue

                print("\nAssistant: ", end="", flush=True)

                # Add user message to history in format expected by prompts.py
                self.chat_history.append(f"user: {user_input}")

                # Prepare prompt with conversation context using model-specific formatting
                model_to_use = model or self.model
                full_prompt = self._format_history_for_context(model_to_use)

                # Debug: Log the formatted prompt to see what's being sent
                self.log.debug(f"Full prompt being sent to LLM:\n{full_prompt}")

                # Generate and stream response
                response = self.client.generate(
                    prompt=full_prompt,
                    model=model_to_use,
                    stream=True,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                # Stream and collect the response
                full_response = ""
                for chunk in response:
                    print(chunk, end="", flush=True)
                    full_response += chunk
                print()  # Add newline

                # Add assistant message to history in format expected by prompts.py
                self.chat_history.append(f"assistant: {full_response}")

            except KeyboardInterrupt:
                print("\n\nChat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                self.log.error(f"Chat error: {e}")

    def _display_history(self):
        """Display the current conversation history."""
        if not self.chat_history:
            print("No conversation history.")
            return

        print("\n" + "=" * 30)
        print("Conversation History:")
        print("=" * 30)
        for entry in self.chat_history:
            # Parse the format "role: message"
            if ": " in entry:
                role, message = entry.split(": ", 1)
                print(f"{role.title()}: {message}")
            else:
                print(entry)
        print("=" * 30)

    def _display_system_prompt(self, model: Optional[str] = None):
        """Display the current system prompt for the given model with formatting."""
        model_name = model or self.model
        matched_model = Prompts.match_model_name(model_name)

        # Get model-specific system prompt or use custom one
        if self.custom_system_prompt:
            system_msg = self.custom_system_prompt
        else:
            system_msg = Prompts.system_messages.get(
                matched_model, "You are a helpful AI assistant."
            )

        # Get the format template for this model
        format_template = Prompts.prompt_formats.get(matched_model, {})
        system_template = format_template.get("system", "{system_message}")

        # Format the system message using the template
        formatted_system = system_template.format(system_message=system_msg)

        print("\n" + "=" * 60)
        print("Current System Prompt Configuration:")
        print(f"Model: {model_name} (matched as: {matched_model})")
        print("=" * 60)
        print("Raw System Message:")
        print("-" * 30)
        print(system_msg)
        print("-" * 30)
        print("Formatted System Prompt Template:")
        print("-" * 30)
        print(repr(formatted_system))
        print("-" * 30)
        print("Actual Formatted Output:")
        print("-" * 30)
        print(formatted_system)
        print("=" * 60)

    def _display_model_info(self, model: Optional[str] = None):
        """Display current model information."""
        model_name = model or self.model
        matched_model = Prompts.match_model_name(model_name)

        print("\n" + "=" * 50)
        print("Current Model Information:")
        print("=" * 50)
        print(f"Model Name: {model_name}")
        print(f"Matched Format: {matched_model}")
        print(f"Chat History Length: {len(self.chat_history)}")
        print(f"Max History Length: {self.chat_history.maxlen}")
        print("=" * 50)

    def _display_complete_prompt(self, model: Optional[str] = None):
        """Display the complete formatted prompt that would be sent to the LLM."""
        model_name = model or self.model

        # Get the complete formatted prompt as it would be sent
        complete_prompt = self._format_history_for_context(model_name)

        print("\n" + "=" * 70)
        print("Complete Formatted Prompt (as sent to LLM):")
        print(f"Model: {model_name}")
        print("=" * 70)
        print(complete_prompt)
        print("=" * 70)
        print(f"Total characters: {len(complete_prompt)}")
        print("=" * 70)

    def _display_stats(self):
        """Display performance statistics."""
        stats = self.get_stats()

        print("\n" + "=" * 50)
        print("Performance Statistics:")
        print("=" * 50)

        if stats:
            for key, value in stats.items():
                # Format different types of values appropriately
                if isinstance(value, float):
                    if "time" in key.lower():
                        print(f"  {key}: {value:.3f}s")
                    elif "tokens_per_second" in key.lower():
                        print(f"  {key}: {value:.2f} tokens/s")
                    else:
                        print(f"  {key}: {value:.4f}")
                elif isinstance(value, int):
                    if "tokens" in key.lower():
                        print(f"  {key}: {value:,} tokens")
                    else:
                        print(f"  {key}: {value}")
                else:
                    print(f"  {key}: {value}")
        else:
            print("  No statistics available")
            print("  (Statistics are collected after LLM interactions)")

        print("=" * 50)

    def _display_help(self):
        """Display available commands."""
        print("\n" + "=" * 40)
        print("Available Commands:")
        print("=" * 40)
        print("  /clear    - clear conversation history")
        print("  /history  - show conversation history")
        print("  /system   - show current system prompt")
        print("  /model    - show current model info")
        print("  /prompt   - show complete formatted prompt")
        print("  /stats    - show performance statistics")
        print("  /help     - show this help message")
        print("\nTo exit: type 'quit', 'exit', or 'bye'")
        print("=" * 40)

    def get_stats(self):
        """Get performance statistics."""
        return self.client.get_performance_stats() or {}


def main(
    message: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 512,
    system_prompt: Optional[str] = None,
    interactive: bool = False,
) -> Optional[str]:
    """Main function to run the Chat app."""
    app = ChatApp(system_prompt=system_prompt, model=model)

    if interactive:
        app.start_interactive_chat(model=model, max_tokens=max_tokens)
        return None
    elif message:
        return app.send_message(
            user_message=message, model=model, max_tokens=max_tokens, stream=False
        )
    else:
        raise ValueError("Either message or interactive mode is required")


def cli_main():
    """Command line interface."""
    parser = argparse.ArgumentParser(description="Simple Chat App with History")

    parser.add_argument(
        "message",
        nargs="?",
        help="Message to send to the chatbot (defaults to interactive mode if not provided)",
    )
    parser.add_argument("--model", help="Model name to use")
    parser.add_argument(
        "--max-tokens", type=int, default=512, help="Max tokens (default: 512)"
    )
    parser.add_argument("--system-prompt", help="System prompt")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Force interactive chat mode"
    )
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument(
        "--logging-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Setup logging
    import logging
    from gaia.logger import log_manager

    log_manager.set_level("gaia", getattr(logging, args.logging_level))

    try:
        if args.interactive or not args.message:
            # Default to interactive mode if no message provided
            main(
                model=args.model,
                max_tokens=args.max_tokens,
                system_prompt=args.system_prompt,
                interactive=True,
            )
        else:
            # Single message mode
            response = main(
                message=args.message,
                model=args.model,
                max_tokens=args.max_tokens,
                system_prompt=args.system_prompt,
                interactive=False,
            )
            print(f"\n{'='*50}")
            print("Chat Response:")
            print("=" * 50)
            print(response)
            print("=" * 50)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
