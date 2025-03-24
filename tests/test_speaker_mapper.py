import json
import pytest
from unittest.mock import MagicMock
from utterly.speaker_mapper import (
    SpeakerMapper,
    SpeakerMapperError,
    NoSpeakersFoundError,
)


@pytest.fixture
def sample_transcript():
    return {
        "results": {
            "channels": [
                {
                    "alternatives": [
                        {
                            "words": [
                                {"text": "Hello", "speaker": 1},
                                {"text": "Hi", "speaker": 2},
                                {"text": "there", "speaker": 1},
                            ]
                        }
                    ]
                }
            ]
        }
    }


@pytest.fixture
def mock_name_prompt():
    def _prompt(speaker_label: str) -> str:
        return f"Test Name for {speaker_label}"

    return _prompt


def test_extract_speakers(sample_transcript):
    mapper = SpeakerMapper()
    speakers = mapper._extract_speakers(sample_transcript)
    assert speakers == {"Speaker 1", "Speaker 2"}


def test_extract_speakers_no_speakers():
    transcript = {"results": {"channels": [{"alternatives": [{"words": []}]}]}}
    mapper = SpeakerMapper()
    with pytest.raises(NoSpeakersFoundError):
        mapper._extract_speakers(transcript)


def test_extract_speakers_invalid_format():
    mapper = SpeakerMapper()
    with pytest.raises(SpeakerMapperError):
        mapper._extract_speakers({})


def test_update_transcript(sample_transcript):
    mapper = SpeakerMapper()
    mapping = {
        "Speaker 1": "Alice",
        "Speaker 2": "Bob",
    }
    updated = mapper._update_transcript(sample_transcript, mapping)

    words = updated["results"]["channels"][0]["alternatives"][0]["words"]
    assert words[0]["speaker_name"] == "Alice"
    assert words[1]["speaker_name"] == "Bob"
    assert words[2]["speaker_name"] == "Alice"


def test_update_transcript_invalid_format():
    mapper = SpeakerMapper()
    with pytest.raises(SpeakerMapperError):
        mapper._update_transcript({}, {})


def test_create_speaker_mapping(sample_transcript, mock_name_prompt, tmp_path):
    # Create a temporary transcript file
    transcript_file = tmp_path / "test_transcript.json"
    with open(transcript_file, "w") as f:
        json.dump(sample_transcript, f)

    mapper = SpeakerMapper(name_prompt_callback=mock_name_prompt)
    mapping = mapper.create_speaker_mapping(transcript_file)

    assert mapping == {
        "Speaker 1": "Test Name for Speaker 1",
        "Speaker 2": "Test Name for Speaker 2",
    }

    # Verify the file was updated correctly
    with open(transcript_file, "r") as f:
        updated_transcript = json.load(f)
        words = updated_transcript["results"]["channels"][0]["alternatives"][0]["words"]
        assert words[0]["speaker_name"] == "Test Name for Speaker 1"
        assert words[1]["speaker_name"] == "Test Name for Speaker 2"


def test_create_speaker_mapping_invalid_file():
    mapper = SpeakerMapper()
    with pytest.raises(SpeakerMapperError):
        mapper.create_speaker_mapping("nonexistent_file.json")


def test_default_name_prompt(monkeypatch):
    # Mock the built-in input function
    mock_input = MagicMock(return_value="Test User")
    monkeypatch.setattr("builtins.input", mock_input)

    mapper = SpeakerMapper()
    result = mapper._default_name_prompt("Speaker 1")

    assert result == "Test User"
    mock_input.assert_called_once_with("Enter name for Speaker 1: ")
