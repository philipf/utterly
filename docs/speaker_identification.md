# Speaker Identification

## Overview

The Speaker Identification feature helps users identify speakers in a transcript by providing context from their spoken words. This makes it easier to map speaker labels (e.g., "Speaker 1") to actual names when reviewing transcripts.

## Usage

### Basic Usage

```python
from utterly.speaker_mapper import SpeakerMapper

# Create a SpeakerMapper instance
mapper = SpeakerMapper()

# Get context for all speakers (default 10 words per speaker)
contexts = mapper.identify_speaker("path/to/transcript.json")

# Display the results
for context in contexts:
    print(f"Speaker: {context.speaker_label}")
    print(f"Words: {' '.join(context.words_spoken)}")
    
    if context.start_timestamp is not None and context.end_timestamp is not None:
        print(f"Time range: {context.start_timestamp:.2f}s - {context.end_timestamp:.2f}s")
```

### Get Context for a Specific Speaker

```python
# Get context for a specific speaker
context = mapper.identify_speaker("path/to/transcript.json", "Speaker 1")
print(f"Speaker {context.speaker_label} said: {' '.join(context.words_spoken)}")
```

### Customize Context Size

```python
# Get more context (e.g., 20 words per speaker)
contexts = mapper.identify_speaker("path/to/transcript.json", context_words=20)

# Get less context (e.g., 5 words per speaker)
contexts = mapper.identify_speaker("path/to/transcript.json", context_words=5)
```

## API Reference

### SpeakerContext Class

A dataclass that holds speaker identification context:

- `speaker_label`: The speaker's label (e.g., "Speaker 1")
- `words_spoken`: List of words spoken by this speaker
- `start_timestamp`: Start time of the first word (if available)
- `end_timestamp`: End time of the last word (if available)

### SpeakerMapper.identify_speaker Method

```python
def identify_speaker(
    self, 
    transcript_path: str | Path, 
    speaker_label: Optional[str] = None, 
    context_words: int = 10
) -> Union[SpeakerContext, List[SpeakerContext]]
```

**Parameters:**
- `transcript_path`: Path to the transcript file
- `speaker_label`: Optional specific speaker to identify. If None, identifies all speakers
- `context_words`: Number of words to include for context (default 10)

**Returns:**
- If `speaker_label` is provided: SpeakerContext for that specific speaker
- If `speaker_label` is None: List of SpeakerContext objects for all speakers

**Raises:**
- `SpeakerMapperError`: For various identification-related errors
- `NoSpeakersFoundError`: If no speakers are found in the transcript

## Command Line Example

The package includes an example script that demonstrates the speaker identification functionality:

```bash
python examples/identify_speakers.py path/to/transcript.json [context_words]
```

This script will:
1. Identify all speakers in the transcript
2. Display context for each speaker
3. Optionally create a speaker mapping