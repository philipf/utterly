"""
Transcript simplification functionality for utterly.
"""

from typing import Dict, List, Any


class TranscriptSimplifier:
    """
    A class to simplify a JSON transcript by extracting and grouping words by speaker.

    The class expects the transcript JSON to have a structure like:

    {
        "results": {
            "channels": [
                {
                    "alternatives": [
                        {
                            "words": [ { "word": "hi", "punctuated_word": "Hi.", "speaker": 0, ... }, ... ]
                        }
                    ]
                }
            ]
        }
    }

    The output will be a list of strings with each string representing a speaker's utterance,
    grouped by consecutive words from the same speaker.
    """

    def __init__(self, transcript_data: Dict[str, Any]) -> None:
        """
        Initializes the TranscriptSimplifier with the JSON transcript data.

        :param transcript_data: The transcript JSON loaded as a dictionary.
        """
        self.transcript_data = transcript_data

    def simplify_transcript(self) -> List[str]:
        """
        Simplifies the transcript by grouping words by speaker.

        :return: A list of strings, each representing an utterance with format:
                 'speaker: <speaker_id> - <utterance text>'
        """
        words = self._extract_words()
        if not words:
            return []

        simplified_lines = []
        current_speaker = words[0].get(
            "speaker_name", f"Speaker {words[0].get('speaker')}"
        )
        utterance_words = []

        for word_info in words:
            speaker = word_info.get(
                "speaker_name", f"Speaker {word_info.get('speaker')}"
            )
            # Use the punctuated_word if available, otherwise fall back to word
            text = word_info.get("punctuated_word", word_info.get("word"))

            # If the speaker is the same as the current, accumulate the word
            if speaker == current_speaker:
                utterance_words.append(text)
            else:
                # Finalize the previous speaker's utterance and reset for the new speaker
                utterance = " ".join(utterance_words)
                simplified_lines.append(f"{current_speaker}: {utterance}")
                current_speaker = speaker
                utterance_words = [text]

        # Append the final utterance
        if utterance_words:
            utterance = " ".join(utterance_words)
            simplified_lines.append(f"{current_speaker}: {utterance}")

        return simplified_lines

    def _extract_words(self) -> List[Dict[str, Any]]:
        """
        Extracts the list of word objects from the transcript JSON.

        Expected location of words:
            transcript_data["results"]["channels"][0]["alternatives"][0]["words"]

        :return: A list of word objects, or an empty list if extraction fails.
        """
        try:
            channels = self.transcript_data["results"]["channels"]
            if channels:
                alternatives = channels[0]["alternatives"]
                if alternatives:
                    return alternatives[0]["words"]
        except KeyError as e:
            print("Key error while extracting words:", e)
        return []
