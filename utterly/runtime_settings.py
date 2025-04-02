"""
Runtime settings management for utterly.

This module handles runtime-specific settings like API keys and model parameters,
separate from configuration management.
"""

import os


class RuntimeSettingsError(Exception):
    """Custom exception for runtime settings errors."""

    pass


class RuntimeSettings:
    """Manages runtime settings like API keys and model parameters."""

    def __init__(self, config):
        """
        Initialize runtime settings.

        Args:
            config: Config instance to read initial values from
        """
        self.config = config

    def get_summary_settings(self):
        """
        Get runtime settings for summarization.

        Returns:
            dict: Runtime settings including output directory

        Raises:
            RuntimeSettingsError: If required settings are missing
        """
        summary_config = self.config.get_summary_config()

        # Extract only runtime parameters
        settings = {"output_dir": summary_config.get("output_dir", "summaries")}

        return settings

    def get_available_prompts(self):
        """
        Get list of available prompts from prompty files.

        Returns:
            list: List of prompt entries with description

        Raises:
            RuntimeSettingsError: If no prompts are found
        """
        from .prompty_utils import list_prompty_files

        prompty_files = list_prompty_files()

        if not prompty_files:
            raise RuntimeSettingsError(
                "No prompty files found in the prompts directory"
            )

        return [{"description": p["description"]} for p in prompty_files]

    def get_recording_settings(self):
        """
        Get runtime settings for audio recording.

        Returns:
            dict: Runtime settings for audio recording
        """
        recording_config = self.config.get_recording_config()

        # Extract only runtime parameters
        return {
            "channels": recording_config.get("channels", 2),
            "samplerate": recording_config.get("samplerate"),
            "subtype": recording_config.get("subtype"),
        }


    def get_transcription_settings(self):
        """
        Get runtime settings for transcription.

        Returns:
            dict: Runtime settings including API key and model parameters

        Raises:
            RuntimeSettingsError: If required settings are missing
        """
        transcription_config = self.config.get_transcription_config()

        # Extract only runtime parameters
        settings = {
            "api_key": os.getenv("DEEPGRAM_API_KEY"),
            "model": transcription_config.get("model"),
            "timeout": transcription_config.get("timeout", 300),
            "keyterms": transcription_config.get("keyterms", []),
        }

        if not settings["api_key"]:
            raise RuntimeSettingsError("DEEPGRAM_API_KEY environment variable not set")

        return settings