import os
from typing import Optional
from pathlib import Path
import click
from dotenv import load_dotenv
from .config import Config, ConfigError
from .runtime_settings import RuntimeSettings, RuntimeSettingsError
from .recorder import AudioRecorder
from .transcriber import Transcriber, TranscriptionError
from .transcript_processor import TranscriptProcessor, TranscriptProcessorError


# Create a Click group for our commands
@click.group(invoke_without_command=True)
@click.option(
    "--config", type=click.Path(exists=True, dir_okay=False), help="Path to config file"
)
@click.pass_context
def cli(ctx, config: Optional[str]):
    """utterly - Record, transcribe, and summarize meetings."""
    try:
        ctx.ensure_object(dict)
        ctx.obj["config"] = Config(config)
        
        # If no command is provided, run pipeline by default
        if ctx.invoked_subcommand is None:
            ctx.invoke(pipeline)
    except ConfigError as e:
        raise click.ClickException(str(e))


@cli.command()
@click.option(
    "--list-devices", is_flag=True, help="List available audio devices and exit"
)
@click.option("--device", type=int, help="Input device ID")
@click.option("--filename", type=str, help="Output filename")
@click.pass_context
def record(ctx, list_devices: bool, device: Optional[int], filename: Optional[str]):
    """Record audio from a meeting."""
    recorder = AudioRecorder()

    if list_devices:
        devices = recorder.list_devices()
        click.echo("Available audio devices:")
        click.echo(devices)

        return None, None

    try:
        # Get runtime settings
        runtime = RuntimeSettings(ctx.obj["config"])
        settings = runtime.get_recording_settings()

        # Generate temporary filename based on current date/time
        from datetime import datetime

        temp_filename = datetime.now().strftime("%Y-%m-%d_%H%M") + ".ogg"

        # Use temporary filename for recording
        output_path = ctx.obj["config"].get_output_path(
            "recording", temp_filename, use_date_subdir=True
        )

        click.echo("Starting recording... Press Ctrl+C to stop")

        # Record with explicit parameters
        output_file = recorder.record(
            filename=output_path,
            device=device,
            channels=settings["channels"],
            samplerate=settings["samplerate"],
            subtype=settings["subtype"],
        )
        click.echo(f"Recording saved to: {output_file}")

        recording_name = click.prompt("Enter name for this utterly recording")
        final_filename = f"{datetime.now().strftime('%Y-%m-%d_%H%M')}_{click.format_filename(recording_name)}.ogg"
        final_path = ctx.obj["config"].get_output_path(
            "recording", final_filename, use_date_subdir=True
        )

        # Rename the file
        os.rename(output_file, final_path)
        click.echo(f"File renamed to: {final_path}")

        # Ask if user wants to continue with transcription
        if click.confirm(
            "Would you like to transcribe this recording now?", default=True
        ):
            transcript_file = ctx.invoke(transcribe, audio_file=final_path)
            # Return both paths as a tuple so pipeline knows transcription was done
            return final_path, transcript_file
        return final_path, None

    except Exception as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("transcript_file", type=click.Path(exists=True))
@click.pass_context
def speaker_map(ctx, transcript_file: str):
    """Interactively map speaker labels to names."""
    import json

    try:
        # Read the transcript file
        with open(transcript_file, "r") as f:
            transcript = json.load(f)

        # Extract unique speaker labels
        speakers = set()
        for word in (
            transcript.get("results", {})
            .get("channels", [{}])[0]
            .get("alternatives", [{}])[0]
            .get("words", [])
        ):
            if "speaker" in word:
                speakers.add(f"Speaker {word['speaker']}")

        if not speakers:
            raise click.ClickException("No speaker labels found in transcript")

        # Create speaker mapping
        click.echo("\nDetected speakers:")
        mapping = {}
        for speaker in sorted(speakers):
            name = click.prompt(f"Enter name for {speaker}")
            mapping[speaker] = name

        # Update transcript with speaker names
        for word in (
            transcript.get("results", {})
            .get("channels", [{}])[0]
            .get("alternatives", [{}])[0]
            .get("words", [])
        ):
            if "speaker" in word:
                speaker_label = f"Speaker {word['speaker']}"
                word["speaker_name"] = mapping[speaker_label]

        # Save updated transcript
        with open(transcript_file, "w") as f:
            json.dump(transcript, f, indent=4)

        # Display final mapping
        click.echo("\nSpeaker mapping:")
        for speaker, name in mapping.items():
            click.echo(f"{speaker} => {name}")

        return mapping

    except Exception as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("--output", type=str, help="Output filename")
@click.pass_context
def transcribe(ctx, audio_file: str, output: Optional[str]):
    """Transcribe an audio recording."""
    try:
        # Get runtime settings
        runtime = RuntimeSettings(ctx.obj["config"])
        settings = runtime.get_transcription_settings()

        if output:
            output_path = output
        else:
            # Auto-generate output path
            base_name = Path(audio_file).stem
            output_path = ctx.obj["config"].get_output_path(
                "transcription", f"{base_name}_transcript.json", use_date_subdir=True
            )

        # Create transcriber with settings from runtime_settings
        transcriber = Transcriber(settings)

        # Transcribe file using settings from runtime_settings
        result = transcriber.transcribe_file(audio_file, output_path)
        click.echo(f"Transcription completed successfully")
        return output_path

    except (TranscriptionError, RuntimeSettingsError) as e:
        raise click.ClickException(str(e))


@cli.command()
@click.argument("transcript_file", type=click.Path(exists=True))
@click.option("--output", type=str, help="Output filename")
@click.pass_context
def summarize(ctx, transcript_file: str, output: Optional[str]):
    """Generate a summary from a transcript."""
    try:
        from .prompty_utils import list_prompty_files

        # Get available prompty files
        prompty_files = list_prompty_files()

        if not prompty_files:
            raise click.ClickException(
                "No prompty files found in the prompts directory"
            )

        # Display prompt options
        click.echo("\nAvailable summary prompts:")
        for i, prompty_file in enumerate(prompty_files, 1):
            click.echo(f"{i}. {prompty_file['description']}")
            if i == 1:
                click.echo("   (Default)")

        # Get user selection with retry logic
        max_attempts = 3
        selected_index = None

        for attempt in range(max_attempts):
            try:
                # Handle empty input (default to 1)
                selection = click.prompt(
                    "\nSelect a prompt number",
                    type=str,
                    default="1",
                    show_default=False,
                )

                if not selection.strip():
                    selected_index = 0
                    break

                selected_num = int(selection)
                if 1 <= selected_num <= len(prompty_files):
                    selected_index = selected_num - 1
                    break
                else:
                    click.echo(
                        f"Please enter a number between 1 and {len(prompty_files)}"
                    )
            except ValueError:
                click.echo("Please enter a valid number")

            if attempt < max_attempts - 1:
                click.echo(f"Attempts remaining: {max_attempts - attempt - 1}")
            else:
                click.echo("\nUsing default prompt (1)")
                selected_index = 0

        # Get selected prompty file
        selected_prompty = prompty_files[selected_index]

        if output:
            output_path = output
        else:
            # Auto-generate output path
            base_name = Path(transcript_file).stem
            output_path = ctx.obj["config"].get_output_path(
                "summary", f"{base_name}_summary.md", use_date_subdir=True
            )

        # Create summarizer with selected prompty file
        summarizer = TranscriptProcessor(str(selected_prompty["path"]))

        # Generate summary
        summary = summarizer.generate_summary(transcript_file, output_path)
        click.echo(summary)
        return output_path

    except (TranscriptProcessorError, Exception) as e:
        raise click.ClickException(str(e))


@cli.command()
@click.option("--output-dir", type=click.Path(), help="Output directory for all files")
@click.option(
    "--list-devices", is_flag=True, help="List available audio devices and exit"
)
@click.option("--device", type=int, help="Input device ID")
@click.pass_context
def pipeline(ctx, output_dir: Optional[str], device: Optional[int], list_devices: bool):
    """Run the complete meeting recording pipeline."""
    try:
        # Record
        click.echo("Step 1: Recording meeting...")
        audio_file, transcript_file = ctx.invoke(
            record, device=device, list_devices=list_devices
        )

        # Exit early if just listing devices
        if list_devices:
            return

        # Transcribe if not already done during recording
        if transcript_file is None:
            click.echo("\nStep 2: Transcribing recording...")
            transcript_file = ctx.invoke(transcribe, audio_file=audio_file)

        # Map speakers
        click.echo("\nStep 3: Mapping speakers...")
        speaker_mapping = ctx.invoke(speaker_map, transcript_file=transcript_file)

        # Summarize
        click.echo("\nStep 4: Generating summary...")
        summary_file = ctx.invoke(summarize, transcript_file=transcript_file)

        click.echo("\nPipeline completed successfully!")
        click.echo(f"Audio: {audio_file}")
        click.echo(f"Transcript: {transcript_file}")
        click.echo(f"Summary: {summary_file}")

    except click.ClickException as e:
        click.echo(f"Pipeline failed: {str(e)}", err=True)
        raise


def main():
    """Entry point for the CLI."""
    # Load environment variables from .env file
    load_dotenv()
    cli(obj={})


if __name__ == "__main__":
    main()
