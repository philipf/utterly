import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


class Config:
    """Manages configuration loading and validation."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration from a YAML file.

        Args:
            config_file: Path to config file. If None, searches default locations.

        Raises:
            ConfigError: If config file not found or invalid
        """
        self.config_data = {}

        # Search for config file
        if config_file:
            config_path = Path(config_file)
        else:
            # Default locations
            search_paths = [
                Path("config.yml"),
                Path("config.yaml"),
                Path.home() / ".config" / "utterly" / "config.yml",
            ]

            for path in search_paths:
                if path.is_file():
                    config_path = path
                    break
            else:
                raise ConfigError(
                    "No configuration file found. Create config.yml or specify path with --config"
                )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.config_data = yaml.safe_load(f)
        except Exception as e:
            raise ConfigError(f"Failed to load config file: {str(e)}")

        # Validate configuration
        self._validate_config()

    def _validate_config(self):
        """
        Validate configuration structure and required fields.

        Raises:
            ConfigError: If configuration is invalid
        """
        required_sections = ["recording", "transcription", "summary"]

        for section in required_sections:
            if section not in self.config_data:
                raise ConfigError(f"Missing required section: {section}")

    def get_summary_config(self) -> Dict[str, Any]:
        """Get summary configuration section."""
        return self.config_data.get("summary", {})

    def get_recording_config(self) -> Dict[str, Any]:
        """Get recording configuration section."""
        return self.config_data.get("recording", {})

    def get_transcription_config(self) -> Dict[str, Any]:
        """Get transcription configuration section."""
        return self.config_data.get("transcription", {})

    def get_output_path(
        self, section: str, filename: str, use_date_subdir: bool = False
    ) -> str:
        """
        Get full output path for a file.

        Args:
            section: Configuration section ('recording', 'transcription', or 'summary')
            filename: Output filename
            use_date_subdir: Whether to use YYYY-MM subdirectories

        Returns:
            str: Full output path

        Raises:
            ConfigError: If section not found or output_dir not configured
        """
        if section not in self.config_data:
            raise ConfigError(f"Invalid section: {section}")

        output_dir = self.config_data[section].get("output_dir")
        if not output_dir:
            raise ConfigError(f"output_dir not configured for {section}")

        # Create base output directory
        os.makedirs(output_dir, exist_ok=True)

        if use_date_subdir:
            # Get YYYY-MM from filename (assumes format YYYY-MM-DD_...)
            date_prefix = filename[:7]
            if not date_prefix or len(date_prefix.split("-")) != 2:
                raise ConfigError(
                    f"Invalid filename format for date subdirectory: {filename}"
                )

            # Create date subdirectory
            subdir = os.path.join(output_dir, date_prefix)
            os.makedirs(subdir, exist_ok=True)
            return os.path.join(subdir, filename)

        return os.path.join(output_dir, filename)
