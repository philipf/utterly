#!/usr/bin/env python3
"""
Test script for the speaker-map CLI command.

Usage:
  python test_speaker_map_cli.py <transcript_json_file>
"""

import sys
import os
import json
from pathlib import Path
from utterly.cli import speaker_map
import click
from click.testing import CliRunner

def main():
    """Test the speaker-map CLI command."""
    if len(sys.argv) < 2:
        print("Usage: python test_speaker_map_cli.py <transcript_json_file>")
        sys.exit(1)

    transcript_path = sys.argv[1]
    transcript_path = os.path.abspath(transcript_path)
    
    # Verify file exists
    if not os.path.exists(transcript_path):
        print(f"ERROR: File {transcript_path} does not exist")
        sys.exit(1)
    
    # Check file permissions
    print(f"File permissions: {oct(os.stat(transcript_path).st_mode)[-3:]}")
    print(f"Is file readable: {os.access(transcript_path, os.R_OK)}")
    print(f"Is file writable: {os.access(transcript_path, os.W_OK)}")
    
    # Read the original file to verify its structure
    try:
        with open(transcript_path, 'r') as f:
            transcript_data = json.load(f)
        # Check if we have speaker IDs
        try:
            words = transcript_data["results"]["channels"][0]["alternatives"][0]["words"]
            speakers = set()
            for word in words:
                if "speaker" in word:
                    speakers.add(f"Speaker {word['speaker']}")
            print(f"Found speakers: {speakers}")
        except (KeyError, IndexError) as e:
            print(f"Error checking transcript structure: {e}")
    except Exception as e:
        print(f"Error reading transcript file: {e}")
        sys.exit(1)
        
    # Set up mock inputs for speaker names
    mock_inputs = {}
    for speaker in sorted(speakers):
        mock_inputs[f"Enter name for {speaker}"] = f"Test name for {speaker}"
    
    # Run the CLI command in test mode
    runner = CliRunner()
    
    def run_with_inputs():
        """Run with mock inputs for speaker names."""
        result = runner.invoke(
            speaker_map, 
            [transcript_path, "--context-words", "5"],
            input="\n".join(mock_inputs.values())
        )
        return result
    
    # Run the command
    print("\nRunning speaker_map command...")
    result = run_with_inputs()
    
    # Check the result
    print(f"Exit code: {result.exit_code}")
    if result.exit_code != 0:
        print(f"Error: {result.exception}")
        print(f"Traceback: {result.exc_info}")
    
    # Verify the file was updated
    print("\nVerifying file was updated...")
    try:
        with open(transcript_path, 'r') as f:
            updated_data = json.load(f)
        # Check if we have speaker names
        try:
            words = updated_data["results"]["channels"][0]["alternatives"][0]["words"]
            speaker_names = set()
            has_names = False
            for word in words:
                if "speaker_name" in word:
                    speaker_names.add(word["speaker_name"])
                    has_names = True
            
            if has_names:
                print(f"SUCCESS: Found speaker names: {speaker_names}")
            else:
                print("ERROR: No speaker_name fields found in the updated transcript")
        except (KeyError, IndexError) as e:
            print(f"Error checking updated transcript structure: {e}")
    except Exception as e:
        print(f"Error reading updated transcript file: {e}")

if __name__ == "__main__":
    main()