"""
Transcription functionality for utterly using Deepgram.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict
import httpx

from deepgram import (
    DeepgramClient,
)


class TranscriptionError(Exception):
    """Custom exception for transcription-related errors."""

    pass


class Transcriber:
    """Handles audio transcription using Deepgram's API."""

    def __init__(self, settings: Dict, log_level: int = logging.INFO):
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

        # In v5, client configuration is simplified.
        # Verbosity is handled by the standard logging library, not a custom config.
        # Timeouts are managed by passing a configured httpx.Client.
        httpx_client = httpx.Client(timeout=httpx.Timeout(self.timeout, connect=10.0))
        self.client = DeepgramClient(api_key=self.api_key, httpx_client=httpx_client)
        logging.getLogger("deepgram").setLevel(log_level)

    def transcribe_file(
        self, audio_file: str, output_file: Optional[str] = None, **kwargs
    ) -> Dict:
        """
        Transcribe an audio file using Deepgram.

        Args:
            audio_file: Path to the audio file to transcribe.
            output_file: Path to save the transcript JSON. If None, auto-generates name.
            **kwargs: Additional options to pass to Deepgram.

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

            # v5 uses direct keyword arguments. The audio data is passed via 'request'.
            
            # Perform transcription
            start_time = datetime.now()
            response = self.client.listen.v1.media.transcribe_file(
                request=buffer_data,
                model=self.model,
                smart_format=True,
                utterances=True,
                punctuate=True,
                diarize=True,
                keyterm=self.keyterms, # Use 'keyterm' as requested by API
                **kwargs,
            )
            duration = (datetime.now() - start_time).seconds

            # Construct the transcript data in the expected format
            transcript_data = {"results": response.results.model_dump()}

            # Save transcript
            with open(output_file, "w") as f:
                f.write(json.dumps(transcript_data, indent=4))

            print(f"Transcription completed in {duration} seconds")
            print(f"Audio file: {audio_file}")
            print(f"Transcript saved to: {output_file}")

            return transcript_data

        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {str(e)}")
