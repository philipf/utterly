"""
Transcription functionality for utterly using Deepgram.
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict
import httpx

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    PrerecordedOptions,
    FileSource,
)


class TranscriptionError(Exception):
    """Custom exception for transcription-related errors."""

    pass


class Transcriber:
    """Handles audio transcription using Deepgram's API."""

    def __init__(self, settings: Dict, log_level: int = logging.NOTICE):
        """
        Initialize the transcriber.

        Args:
            settings: Transcription settings dictionary with api_key, model, and timeout
            log_level: Logging level for Deepgram client
        """
        # Store transcription settings
        self.api_key = settings["api_key"]
        self.model = settings["model"]
        self.timeout = settings["timeout"]
        self.keyterms = settings.get("keyterms", [])

        if not self.api_key:
            raise TranscriptionError("Deepgram API key not found")

        config = DeepgramClientOptions(verbose=log_level)
        self.client = DeepgramClient(self.api_key, config)

    def transcribe_file(
        self, audio_file: str, output_file: Optional[str] = None, **kwargs
    ) -> Dict:
        """
        Transcribe an audio file using Deepgram.

        Args:
            audio_file: Path to the audio file to transcribe.
            output_file: Path to save the transcript JSON. If None, auto-generates name.
            **kwargs: Additional options to pass to Deepgram's PrerecordedOptions.

        Returns:
            Dict: The transcription response data.
        """
        try:
            # Read audio file
            with open(audio_file, "rb") as f:
                buffer_data = f.read()

            # Generate output filename if not provided
            if output_file is None:
                base = os.path.splitext(audio_file)[0]
                output_file = f"{base}_transcript.json"

            # Set up transcription options using model from runtime settings
            payload: FileSource = {"buffer": buffer_data}
            options = PrerecordedOptions(
                model=self.model,
                smart_format=True,
                utterances=True,
                punctuate=True,
                diarize=True,
                keyterm=self.keyterms,
                **kwargs,
            )

            # Perform transcription using timeout from runtime settings
            start_time = datetime.now()
            response = self.client.listen.prerecorded.v("1").transcribe_file(
                payload, options, timeout=httpx.Timeout(self.timeout, connect=10.0)
            )
            duration = (datetime.now() - start_time).seconds

            # Save transcript
            with open(output_file, "w") as f:
                f.write(response.to_json(indent=4))

            print(f"Transcription completed in {duration} seconds")
            print(f"Audio file: {audio_file}")
            print(f"Transcript saved to: {output_file}")

            return response.results

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {str(e)}")
