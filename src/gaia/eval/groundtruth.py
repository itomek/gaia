import json
import argparse
from datetime import datetime
from pathlib import Path
from gaia.eval.claude import ClaudeClient
from gaia.logger import get_logger


class GroundTruthGenerator:
    """Generates ground truth data for RAG system evaluation using Claude."""

    @staticmethod
    def get_default_prompt(num_samples=5):
        """Generate default prompt with specified number of samples."""
        return f"""
    Given this document, generate exactly {num_samples} short queries a user may ask about the document
    and produce a set of ground truth answers to be used in validating a RAG system. 
    Include a summary of the document in the queries. Return a json formatted list of 
    query-response pairs formatted as follows:
    {{
        'source': 'path/to/document',
        'summary': 'summarized document',
        'qa_pairs': [
            {{'query': 'query1', 'response': 'response1'}},
            {{'query': 'query2', 'response': 'response2'}},
            ...
        ]
    }}

    Generate exactly {num_samples} qa_pairs - no more, no less.
    """

    def __init__(self, model="claude-sonnet-4-20250514", max_tokens=4096):
        self.log = get_logger(__name__)
        self.claude = ClaudeClient(model=model, max_tokens=max_tokens)

    def generate(
        self, file_path, prompt=None, save_text=True, output_dir=None, num_samples=5
    ):
        """
        Generate ground truth data for a given document.

        Args:
            file_path (str): Path to the input document
            prompt (str, optional): Custom prompt for Claude. If None, uses default prompt with num_samples
            save_text (bool): Whether to save extracted text for HTML files
            output_dir (str, optional): Directory to save output files. If None, uses same directory as input
            num_samples (int): Number of Q&A pairs to generate (default: 5)

        Returns:
            dict: Generated ground truth data with metadata
        """
        self.log.info(f"Generating ground truth data for: {file_path}")

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        prompt = prompt or self.get_default_prompt(num_samples)

        try:
            # Generate analysis using Claude
            analysis = self.claude.analyze_file(
                str(file_path), prompt, save_text=save_text
            )
            token_count = self.claude.count_file_tokens(str(file_path), prompt)

            # Debug: Log the raw analysis response
            self.log.debug(
                f"Raw Claude response length: {len(analysis) if analysis else 0}"
            )
            self.log.debug(
                f"Raw Claude response preview: {analysis[:500] if analysis else 'None'}"
            )

            # Check if analysis is valid
            if not analysis or not analysis.strip():
                raise ValueError(
                    "Claude returned an empty response. This may be due to token limits or API issues."
                )

            # Try to parse the JSON response
            try:
                parsed_analysis = json.loads(analysis)
            except json.JSONDecodeError as je:
                # Try to extract JSON from the response if it's wrapped in text
                self.log.warning(
                    "Initial JSON parsing failed, attempting to extract JSON from response"
                )

                # Look for JSON content within the response
                start_idx = analysis.find("{")
                end_idx = analysis.rfind("}") + 1

                if start_idx >= 0 and end_idx > start_idx:
                    json_content = analysis[start_idx:end_idx]
                    try:
                        parsed_analysis = json.loads(json_content)
                        self.log.info("Successfully extracted JSON from response")
                    except json.JSONDecodeError:
                        self.log.error(
                            f"Failed to parse extracted JSON. Response content: {analysis}"
                        )
                        raise ValueError(
                            f"Claude response is not valid JSON: {str(je)}"
                        )
                else:
                    self.log.error(f"No JSON content found in response: {analysis}")
                    raise ValueError(
                        f"No valid JSON found in Claude response: {str(je)}"
                    )

            # Prepare output data with metadata
            output_data = {
                "metadata": {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "model": self.claude.model,
                    "source_file": str(file_path),
                    "prompt": prompt,
                    "token_count": token_count,
                    "num_samples_requested": num_samples,
                },
                "analysis": parsed_analysis,
            }

            # Save to file if output_dir specified
            if output_dir:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{file_path.stem}.groundtruth.json"
            else:
                output_path = file_path.with_suffix(".groundtruth.json")

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)
            self.log.info(f"Ground truth data saved to: {output_path}")

            return output_data

        except Exception as e:
            self.log.error(f"Error generating ground truth data: {e}")
            raise

    def generate_batch(self, input_dir, file_pattern="*.html", **kwargs):
        """
        Generate ground truth data for multiple documents in a directory.

        Args:
            input_dir (str): Directory containing input documents
            file_pattern (str): Glob pattern to match input files
            **kwargs: Additional arguments passed to generate()

        Returns:
            list: List of generated ground truth data for each document
        """
        input_dir = Path(input_dir)
        if not input_dir.is_dir():
            raise NotADirectoryError(f"Input directory not found: {input_dir}")

        results = []
        for file_path in input_dir.glob(file_pattern):
            self.log.info(f"Processing file: {file_path}")
            try:
                result = self.generate(file_path, **kwargs)
                results.append(result)
            except Exception as e:
                self.log.error(f"Error processing {file_path}: {e}")
                continue

        return results


def main():
    """Command line interface for ground truth generation."""
    parser = argparse.ArgumentParser(
        description="Generate ground truth data for RAG system evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single file
  python -m gaia.eval.groundtruth -f ./data/html/blender/introduction.html

  # Process all HTML files in a directory
  python -m gaia.eval.groundtruth -d ./data/html/blender

  # Process with custom output directory
  python -m gaia.eval.groundtruth -f ./data/html/intro.html -o ./output/gt

  # Process with custom file pattern
  python -m gaia.eval.groundtruth -d ./data -p "*.pdf" -o ./output/gt

  # Use custom Claude model
  python -m gaia.eval.groundtruth -f ./data/doc.html -m claude-3-opus-20240229

  # Generate 10 Q&A pairs per document
  python -m gaia.eval.groundtruth -d ./data/html/blender --num-samples 10
        """,
    )

    # Input source (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-f", "--file", type=str, help="Path to a single document file to process"
    )
    input_group.add_argument(
        "-d", "--directory", type=str, help="Directory containing documents to process"
    )

    # Optional arguments
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="./output/groundtruth",
        help="Output directory for generated ground truth files (default: ./output/groundtruth)",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        type=str,
        default="*.html",
        help="File pattern to match when processing directory (default: *.html)",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="claude-3-7-sonnet-20250219",
        help="Claude model to use (default: claude-3-7-sonnet-20250219)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Maximum tokens for Claude responses (default: 4096)",
    )
    parser.add_argument(
        "--no-save-text",
        action="store_true",
        help="Don't save extracted text for HTML files",
    )
    parser.add_argument(
        "--custom-prompt",
        type=str,
        help="Path to a file containing a custom prompt for Claude",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=5,
        help="Number of Q&A pairs to generate per document (default: 5)",
    )

    args = parser.parse_args()

    # Initialize generator
    try:
        generator = GroundTruthGenerator(model=args.model, max_tokens=args.max_tokens)
    except Exception as e:
        print(f"Error initializing generator: {e}")
        return 1

    # Load custom prompt if provided
    custom_prompt = None
    if args.custom_prompt:
        try:
            with open(args.custom_prompt, "r", encoding="utf-8") as f:
                custom_prompt = f.read().strip()
            print(f"Using custom prompt from: {args.custom_prompt}")
        except Exception as e:
            print(f"Error loading custom prompt: {e}")
            return 1

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
            print(f"✓ Successfully generated ground truth data")
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
                print(f"✓ Successfully processed {len(results)} files")
                print(f"  Output: {args.output_dir}")
                print(f"  Total QA pairs: {total_pairs}")
                print(f"  Total tokens: {total_tokens}")
            else:
                print("No files were processed successfully")
                return 1

    except Exception as e:
        print(f"Error during processing: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
