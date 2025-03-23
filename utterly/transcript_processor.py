import os
import json
from typing import Optional
from datetime import datetime
import pytz

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from .transcript_simplifier import TranscriptSimplifier
from .prompty_utils import create_prompt_from_prompty, load_prompty_file


class TranscriptProcessorError(Exception):
    """Custom exception for summary-related errors."""

    pass


class TranscriptProcessor:
    """Processes transcript data by transforming and analyzing it using configurable prompts and LLM models.

    This class provides functionality to:
    - Load and apply custom prompts for transcript processing
    - Transform transcript data using LLM models
    - Generate structured output based on transcript content
    - Handle transcript metadata and formatting
    """

    def __init__(self, prompty_path: str):
        """
        Initialize the transformer  with a prompty file.

        Args:
            prompty_path: Path to the prompty file.
        """
        if not os.path.exists(prompty_path):
            raise TranscriptProcessorError(f"Prompty file not found: {prompty_path}")

        try:
            # Load the prompty file
            self.prompty = load_prompty_file(prompty_path)

            # Get model configuration and parameters from prompty
            model_config = self.prompty.model.configuration
            model_params = self.prompty.model.parameters

            # Initialize LLM with parameters from prompty
            self.llm = ChatOpenAI(model=model_config.get("name"), **model_params)

            # Create prompt from prompty
            self.prompt = create_prompt_from_prompty(prompty_path)

            # Set up chain
            self.chain = self.prompt | self.llm | StrOutputParser()

        except Exception as e:
            raise TranscriptProcessorError(f"Failed to initialize summarizer: {str(e)}")

    def generate_summary(
        self, transcript_file: str, output_file: Optional[str] = None
    ) -> str:
        """
        Generate a a response from a transcript file.

        Args:
            transcript_file: Path to the transcript file (JSON or text).
            output_file: Path to save the summary. If None, auto-generates name.

        Returns:
            str: The generated summary text.
        """
        try:
            # Simplify transcript
            simplified_transcript = self.transcript_to_text(transcript_file)

            # Generate summary using transcript with created date
            # Use the variable name expected by the prompty template
            summary = self.chain.invoke({"transcript": simplified_transcript})

            # Save summary if output file specified
            if output_file:
                with open(output_file, "w") as f:
                    f.write(summary)

                print(f"Summary saved to: {output_file}")

            return summary

        except Exception as e:
            raise TranscriptProcessorError(f"Summary generation failed: {str(e)}")

    def transcript_to_text(self, transcript_file: str) -> str:
        """
        Convert a transcript JSON file to simplified text format.

        Args:
            transcript_file: Path to the transcript JSON file.

        Returns:
            str: The simplified transcript text with recording timestamp.
        """
        # Read and parse transcript JSON
        with open(transcript_file, "r") as f:
            transcript_data = json.load(f)

        simplifier = TranscriptSimplifier(transcript_data)
        simplified_lines = simplifier.simplify_transcript()
        simplified_transcript = "\n".join(simplified_lines)

        recorded_at_str = self.get_recorded_at_line(transcript_data)

        # Add created date to transcript and save
        simplified_transcript = f"{recorded_at_str}\n\n{simplified_transcript}"
        simplified_file = transcript_file.rsplit(".", 1)[0] + ".txt"

        with open(simplified_file, "w") as f:
            f.write(simplified_transcript)

        print(f"Simplified transcript saved to: {simplified_file}")
        return simplified_transcript

    # Function to extract the created time from the transcript metadata
    def get_recorded_at_line(self, transcript_data):
        created_str = "Recording created: (timestamp unavailable)"
        try:
            timestamp = transcript_data["metadata"]["created"]
            # Parse the ISO format date with Z timezone indicator
            created_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            # Convert to NZ timezone
            nz_timezone = pytz.timezone("Pacific/Auckland")
            created_local = created_utc.astimezone(nz_timezone)
            # Format with timezone name (NZDT/NZST) which automatically handles daylight savings
            created_str = (
                f"Recording created: {created_local.strftime('%Y-%m-%d %H:%M %Z')}"
            )
        except Exception as e:
            print(f"Warning: Could not parse timestamp: {str(e)}")
        return created_str
