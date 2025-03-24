import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from utterly.speaker_mapper import (
    SpeakerMapper,
    SpeakerMapperError,
    NoSpeakersFoundError,
    SpeakerContext,
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
                                {"text": "Hello", "speaker": "1", "start_time": "0.0", "end_time": "0.5"},
                                {"text": "world", "speaker": "1", "start_time": "0.6", "end_time": "1.0"},
                                {"text": "this", "speaker": "1", "start_time": "1.1", "end_time": "1.5"},
                                {"text": "is", "speaker": "1", "start_time": "1.6", "end_time": "2.0"},
                                {"text": "a", "speaker": "1", "start_time": "2.1", "end_time": "2.5"},
                                {"text": "test", "speaker": "1", "start_time": "2.6", "end_time": "3.0"},
                                {"text": "Hi", "speaker": "2", "start_time": "3.1", "end_time": "3.5"},
                                {"text": "there", "speaker": "2", "start_time": "3.6", "end_time": "4.0"},
                                {"text": "how", "speaker": "2", "start_time": "4.1", "end_time": "4.5"},
                                {"text": "are", "speaker": "2", "start_time": "4.6", "end_time": "5.0"},
                                {"text": "you", "speaker": "2", "start_time": "5.1", "end_time": "5.5"},
                                {"text": "doing", "speaker": "2", "start_time": "5.6", "end_time": "6.0"},
                                {"text": "today", "speaker": "2", "start_time": "6.1", "end_time": "6.5"},
                                {"text": "I'm", "speaker": "1", "start_time": "6.6", "end_time": "7.0"},
                                {"text": "good", "speaker": "1", "start_time": "7.1", "end_time": "7.5"},
                                {"text": "thanks", "speaker": "1", "start_time": "7.6", "end_time": "8.0"},
                            ]
                        }
                    ]
                }
            ]
        }
    }


@pytest.fixture
def sample_transcript_no_timestamps():
    return {
        "results": {
            "channels": [
                {
                    "alternatives": [
                        {
                            "words": [
                                {"text": "Hello", "speaker": "1"},
                                {"text": "world", "speaker": "1"},
                                {"text": "Hi", "speaker": "2"},
                                {"text": "there", "speaker": "2"},
                            ]
                        }
                    ]
                }
            ]
        }
    }


def test_get_speaker_context(sample_transcript):
    mapper = SpeakerMapper()
    context = mapper._get_speaker_context(sample_transcript, "Speaker 1", 3)
    
    assert isinstance(context, SpeakerContext)
    assert context.speaker_label == "Speaker 1"
    assert context.words_spoken == ["Hello", "world", "this"]
    assert context.start_timestamp == 0.0
    assert context.end_timestamp == 8.0  # Last timestamp for Speaker 1


def test_get_speaker_context_with_zero_context(sample_transcript):
    mapper = SpeakerMapper()
    context = mapper._get_speaker_context(sample_transcript, "Speaker 1", 0)
    
    assert isinstance(context, SpeakerContext)
    assert context.speaker_label == "Speaker 1"
    assert context.words_spoken == []
    assert context.start_timestamp == 0.0
    assert context.end_timestamp == 8.0


def test_get_speaker_context_with_large_context(sample_transcript):
    mapper = SpeakerMapper()
    context = mapper._get_speaker_context(sample_transcript, "Speaker 1", 100)
    
    # Should return all words for Speaker 1 (9 words total)
    assert len(context.words_spoken) == 9
    assert context.words_spoken == ["Hello", "world", "this", "is", "a", "test", "I'm", "good", "thanks"]


def test_get_speaker_context_no_timestamps(sample_transcript_no_timestamps):
    mapper = SpeakerMapper()
    context = mapper._get_speaker_context(sample_transcript_no_timestamps, "Speaker 1", 3)
    
    assert context.speaker_label == "Speaker 1"
    assert context.words_spoken == ["Hello", "world"]
    assert context.start_timestamp is None
    assert context.end_timestamp is None


def test_get_speaker_context_invalid_speaker(sample_transcript):
    mapper = SpeakerMapper()
    with pytest.raises(SpeakerMapperError, match="No words found for Speaker 3"):
        mapper._get_speaker_context(sample_transcript, "Speaker 3", 3)


def test_get_speaker_context_negative_context():
    mapper = SpeakerMapper()
    with pytest.raises(ValueError, match="context_words must be a non-negative integer"):
        mapper._get_speaker_context({}, "Speaker 1", -1)


def test_identify_speaker_single(sample_transcript, tmp_path):
    # Create a temporary transcript file
    transcript_file = tmp_path / "test_transcript.json"
    with open(transcript_file, "w") as f:
        json.dump(sample_transcript, f)
    
    mapper = SpeakerMapper()
    context = mapper.identify_speaker(transcript_file, "Speaker 1", 3)
    
    assert isinstance(context, SpeakerContext)
    assert context.speaker_label == "Speaker 1"
    assert context.words_spoken == ["Hello", "world", "this"]


def test_identify_speaker_all(sample_transcript, tmp_path):
    # Create a temporary transcript file
    transcript_file = tmp_path / "test_transcript.json"
    with open(transcript_file, "w") as f:
        json.dump(sample_transcript, f)
    
    mapper = SpeakerMapper()
    contexts = mapper.identify_speaker(transcript_file, context_words=2)
    
    assert isinstance(contexts, list)
    assert len(contexts) == 2
    
    # Check Speaker 1
    assert contexts[0].speaker_label == "Speaker 1"
    assert contexts[0].words_spoken == ["Hello", "world"]
    
    # Check Speaker 2
    assert contexts[1].speaker_label == "Speaker 2"
    assert contexts[1].words_spoken == ["Hi", "there"]


def test_identify_speaker_invalid_file():
    mapper = SpeakerMapper()
    with pytest.raises(SpeakerMapperError, match="Error reading transcript file"):
        mapper.identify_speaker("nonexistent_file.json")


def test_identify_speaker_invalid_speaker(sample_transcript, tmp_path):
    # Create a temporary transcript file
    transcript_file = tmp_path / "test_transcript.json"
    with open(transcript_file, "w") as f:
        json.dump(sample_transcript, f)
    
    mapper = SpeakerMapper()
    with pytest.raises(SpeakerMapperError, match="No words found for Speaker 3"):
        mapper.identify_speaker(transcript_file, "Speaker 3")


def test_identify_speaker_empty_transcript(tmp_path):
    # Create an empty transcript
    empty_transcript = {"results": {"channels": [{"alternatives": [{"words": []}]}]}}
    transcript_file = tmp_path / "empty_transcript.json"
    with open(transcript_file, "w") as f:
        json.dump(empty_transcript, f)
    
    mapper = SpeakerMapper()
    with pytest.raises(NoSpeakersFoundError):
        mapper.identify_speaker(transcript_file)