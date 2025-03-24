import json
from typing import Dict, Set, Callable, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SpeakerContext:
    """Class to hold speaker identification context."""

    speaker_label: str
    words_spoken: List[str]
    start_timestamp: Optional[float] = None
    end_timestamp: Optional[float] = None


class SpeakerMapperError(Exception):
    """Base exception for SpeakerMapper errors."""

    pass


class NoSpeakersFoundError(SpeakerMapperError):
    """Raised when no speakers are found in the transcript."""

    pass


class SpeakerMapper:
    """Handles mapping of speaker labels to names in transcripts."""

    def __init__(self, name_prompt_callback: Optional[Callable[[str], str]] = None):
        """
        Initialize the SpeakerMapper.

        Args:
            name_prompt_callback: Optional callback function that takes a speaker label
                                and returns the mapped name. If not provided, will
                                use an internal default implementation.
        """
        self.name_prompt_callback = name_prompt_callback or self._default_name_prompt

    def _default_name_prompt(self, speaker_label: str) -> str:
        """Default implementation for prompting for speaker names."""
        return input(f"Enter name for {speaker_label}: ")

    def _extract_speakers(self, transcript: dict) -> Set[str]:
        """
        Extract unique speaker labels from the transcript.

        Args:
            transcript: The transcript dictionary.

        Returns:
            A set of unique speaker labels.

        Raises:
            NoSpeakersFoundError: If no speakers are found in the transcript.
        """
        speakers = set()
        try:
            words = (
                transcript.get("results", {})
                .get("channels", [{}])[0]
                .get("alternatives", [{}])[0]
                .get("words", [])
            )

            for word in words:
                if "speaker" in word:
                    # Handle different speaker formats
                    speaker_value = word["speaker"]

                    # If speaker_name is available, use it directly
                    if "speaker_name" in word:
                        speakers.add(word["speaker_name"])
                    # Otherwise, format as "Speaker X"
                    else:
                        speakers.add(f"Speaker {speaker_value}")
        except (IndexError, AttributeError) as e:
            raise SpeakerMapperError(f"Invalid transcript format: {e}")

        if not speakers:
            raise NoSpeakersFoundError("No speaker labels found in transcript")

        return speakers

    def _validate_transcript_structure(self, transcript: dict) -> list:
        """
        Validate transcript structure and return the words list.

        Args:
            transcript: The transcript dictionary to validate.

        Returns:
            List of words from the transcript.

        Raises:
            SpeakerMapperError: If the transcript format is invalid.
        """
        if not isinstance(transcript, dict):
            raise SpeakerMapperError("Transcript must be a dictionary")

        results = transcript.get("results")
        if not isinstance(results, dict):
            raise SpeakerMapperError(
                "Invalid transcript format: missing or invalid 'results' field"
            )

        channels = results.get("channels")
        if not isinstance(channels, list) or not channels:
            raise SpeakerMapperError(
                "Invalid transcript format: missing or invalid 'channels' field"
            )

        alternatives = channels[0].get("alternatives")
        if not isinstance(alternatives, list) or not alternatives:
            raise SpeakerMapperError(
                "Invalid transcript format: missing or invalid 'alternatives' field"
            )

        words = alternatives[0].get("words")
        if not isinstance(words, list):
            raise SpeakerMapperError(
                "Invalid transcript format: missing or invalid 'words' field"
            )

        return words

    def _update_word_speakers(self, words: list, mapping: Dict[str, str]) -> None:
        """
        Update speaker names in the words list.

        Args:
            words: List of word dictionaries to update.
            mapping: Dictionary mapping speaker labels to names.

        Raises:
            SpeakerMapperError: If there's an error updating the words.
        """
        try:
            for word in words:
                if "speaker" in word and "speaker_name" not in word:
                    speaker_label = f"Speaker {word['speaker']}"
                    if speaker_label in mapping:
                        word["speaker_name"] = mapping[speaker_label]
        except (KeyError, TypeError) as e:
            raise SpeakerMapperError(f"Error updating transcript: {e}")

    def _update_transcript(self, transcript: dict, mapping: Dict[str, str]) -> dict:
        """
        Update the transcript with speaker names.

        Args:
            transcript: The transcript dictionary to update.
            mapping: Dictionary mapping speaker labels to names.

        Returns:
            The updated transcript dictionary.

        Raises:
            SpeakerMapperError: If the transcript format is invalid.
        """
        words = self._validate_transcript_structure(transcript)
        self._update_word_speakers(words, mapping)
        return transcript

    def create_speaker_mapping(self, transcript_path: str | Path) -> Dict[str, str]:
        """
        Create speaker mapping for a transcript file.

        Args:
            transcript_path: Path to the transcript file.

        Returns:
            Dictionary mapping speaker labels to names.

        Raises:
            SpeakerMapperError: For various mapping-related errors.
            NoSpeakersFoundError: If no speakers are found in the transcript.
        """
        transcript_path = Path(transcript_path)

        try:
            with open(transcript_path, "r") as f:
                transcript = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise SpeakerMapperError(f"Error reading transcript file: {e}")

        # Extract unique speaker labels
        speakers = self._extract_speakers(transcript)

        # Create speaker mapping
        mapping = {}
        for speaker in sorted(speakers):
            name = self.name_prompt_callback(speaker)
            mapping[speaker] = name

        # Update transcript with speaker names
        updated_transcript = self._update_transcript(transcript, mapping)

        # Save updated transcript
        try:
            with open(transcript_path, "w") as f:
                json.dump(updated_transcript, f, indent=4)
        except OSError as e:
            raise SpeakerMapperError(f"Error saving updated transcript: {e}")

        return mapping

    def _is_speaker_match(self, word: dict, speaker_label: str) -> bool:
        """
        Check if a word matches a given speaker.

        Args:
            word: The word dictionary.
            speaker_label: The speaker label to match.

        Returns:
            bool: True if the word matches the speaker, False otherwise.
        """
        # Check for direct speaker_name match
        if "speaker_name" in word and word["speaker_name"] == speaker_label:
            return True

        # Check for "Speaker X" format match
        if speaker_label.startswith("Speaker ") and "speaker" in word:
            speaker_number = speaker_label.split()[-1]
            if str(word["speaker"]) == speaker_number:
                return True

        return False

    def _get_word_timestamps(self, word: dict) -> tuple[Optional[float], Optional[float]]:
        """
        Extract start and end timestamps from a word.

        Args:
            word: The word dictionary.

        Returns:
            Tuple of (start_time, end_time), each may be None if not found.
        """
        start_time = None
        end_time = None

        # Get start time
        if "start_time" in word:
            start_time = float(word["start_time"])
        elif "start" in word:
            start_time = float(word["start"])

        # Get end time
        if "end_time" in word:
            end_time = float(word["end_time"])
        elif "end" in word:
            end_time = float(word["end"])

        return start_time, end_time

    def _collect_speaker_words(
        self, words: list, speaker_label: str, context_words: int
    ) -> tuple[list[str], Optional[float], Optional[float]]:
        """
        Collect words and timestamps for a speaker.

        Args:
            words: List of word dictionaries.
            speaker_label: The speaker label to collect words for.
            context_words: Number of words to include in context.

        Returns:
            Tuple of (word_list, start_time, end_time).

        Raises:
            SpeakerMapperError: If no words are found for the speaker.
        """
        speaker_words = []
        start_time = None
        end_time = None

        for word in words:
            if self._is_speaker_match(word, speaker_label):
                # Get the word text
                word_text = word.get("text", word.get("word", ""))
                speaker_words.append(word_text)

                # Track timestamps
                if start_time is None:
                    word_start, _ = self._get_word_timestamps(word)
                    start_time = word_start

                _, word_end = self._get_word_timestamps(word)
                if word_end is not None:
                    end_time = word_end

        if not speaker_words:
            raise SpeakerMapperError(f"No words found for {speaker_label}")

        # Limit to the requested context size
        context = speaker_words[:context_words] if context_words > 0 else []

        return context, start_time, end_time

    def _get_speaker_context(
        self, transcript: dict, speaker_label: str, context_words: int
    ) -> SpeakerContext:
        """
        Get context for a specific speaker from the transcript.

        Args:
            transcript: The transcript dictionary.
            speaker_label: The speaker label to get context for (e.g., "Speaker 1" or a name).
            context_words: Number of words to include in the context.

        Returns:
            SpeakerContext object containing the speaker's words and timestamps.

        Raises:
            SpeakerMapperError: If the transcript format is invalid or speaker not found.
            ValueError: If context_words is negative.
        """
        if context_words < 0:
            raise ValueError("context_words must be a non-negative integer")

        try:
            words = (
                transcript.get("results", {})
                .get("channels", [{}])[0]
                .get("alternatives", [{}])[0]
                .get("words", [])
            )
        except (IndexError, AttributeError) as e:
            raise SpeakerMapperError(f"Invalid transcript format: {e}")

        context, start_time, end_time = self._collect_speaker_words(
            words, speaker_label, context_words
        )

        return SpeakerContext(
            speaker_label=speaker_label,
            words_spoken=context,
            start_timestamp=start_time,
            end_timestamp=end_time,
        )

    def identify_speaker(
        self,
        transcript_path: str | Path,
        speaker_label: Optional[str] = None,
        context_words: int = 10,
    ) -> Union[SpeakerContext, List[SpeakerContext]]:
        """
        Identify speaker(s) with context from their spoken words.

        Args:
            transcript_path: Path to the transcript file.
            speaker_label: Optional specific speaker to identify. If None, identifies all speakers.
            context_words: Number of words to include for context (default 10).

        Returns:
            If speaker_label is provided: SpeakerContext for that specific speaker.
            If speaker_label is None: List of SpeakerContext objects for all speakers.

        Raises:
            SpeakerMapperError: For various identification-related errors.
            NoSpeakersFoundError: If no speakers are found in the transcript.
        """
        transcript_path = Path(transcript_path)

        try:
            with open(transcript_path, "r") as f:
                transcript = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise SpeakerMapperError(f"Error reading transcript file: {e}")

        # If specific speaker requested
        if speaker_label:
            return self._get_speaker_context(transcript, speaker_label, context_words)

        # Otherwise, get context for all speakers
        speakers = self._extract_speakers(transcript)
        contexts = []

        for speaker in sorted(speakers):
            try:
                context = self._get_speaker_context(transcript, speaker, context_words)
                contexts.append(context)
            except SpeakerMapperError:
                # Skip speakers with no words (shouldn't happen, but just in case)
                continue

        if not contexts:
            raise NoSpeakersFoundError("No speakers with words found in transcript")

        return contexts
