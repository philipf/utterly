#!/usr/bin/env python3
"""
Example script demonstrating the speaker identification functionality.

This script shows how to use the SpeakerMapper.identify_speaker method
to get context for speakers in a transcript file.
"""

import sys
import json
from pathlib import Path
from utterly.speaker_mapper import SpeakerMapper, SpeakerMapperError, NoSpeakersFoundError


def main():
    """Run the speaker identification example."""
    if len(sys.argv) < 2:
        print("Usage: python identify_speakers.py <transcript_file> [context_words]")
        sys.exit(1)

    transcript_path = sys.argv[1]
    context_words = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    try:
        # Create a SpeakerMapper instance
        mapper = SpeakerMapper()
        
        # Get context for all speakers
        print(f"Getting {context_words} words of context for each speaker...")
        contexts = mapper.identify_speaker(transcript_path, context_words=context_words)
        
        # Display the results
        print("\nSpeaker Identification Results:")
        print("===============================")
        
        for context in contexts:
            print(f"\nSpeaker: {context.speaker_label}")
            print(f"Words: {' '.join(context.words_spoken)}")
            
            if context.start_timestamp is not None and context.end_timestamp is not None:
                print(f"Time range: {context.start_timestamp:.2f}s - {context.end_timestamp:.2f}s")
        
        # Optionally, create a speaker mapping
        print("\nWould you like to create a speaker mapping? (y/n)")
        response = input("> ")
        
        if response.lower() == 'y':
            mapping = mapper.create_speaker_mapping(transcript_path)
            print("\nSpeaker mapping created:")
            for speaker, name in mapping.items():
                print(f"  {speaker} -> {name}")
            
    except (SpeakerMapperError, NoSpeakersFoundError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()