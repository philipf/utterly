import os
from typing import Optional
from pathlib import Path
import subprocess
import click
from dotenv import load_dotenv
from .config import Config, ConfigError
from .runtime_settings import RuntimeSettings, RuntimeSettingsError
from .recorder import AudioRecorder
from .transcriber import Transcriber, TranscriptionError
from .transcript_processor import TranscriptProcessor, TranscriptProcessorError
from .file_opener import FileOpener


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
@click.option(
    "--context-words", type=int, default=20, help="Number of words to show for context"
)
@click.pass_context
def speaker_map(ctx, transcript_file: str, context_words: int):
    """Interactively map speaker labels to names."""
    from .speaker_mapper import SpeakerMapper, SpeakerMapperError, NoSpeakersFoundError

    def click_prompt_callback(speaker_label: str) -> str:
        """Wrapper to use click.prompt for speaker name input."""
        return click.prompt(f"Enter name for {speaker_label}")

    try:
        # First identify speakers and show context
        click.echo("\nIdentifying speakers and getting context...")
        mapper = SpeakerMapper(name_prompt_callback=click_prompt_callback)

        # Get context for all speakers
        contexts = mapper.identify_speaker(transcript_file, context_words=context_words)

        # Display the results
        click.echo("\nSpeaker Identification Results:")
        click.echo("===============================")

        for context in contexts:
            click.echo(f"\nSpeaker: {context.speaker_label}")
            click.echo(f"Words: {' '.join(context.words_spoken)}")

            if (
                context.start_timestamp is not None
                and context.end_timestamp is not None
            ):
                click.echo(
                    f"Time range: {context.start_timestamp:.2f}s - {context.end_timestamp:.2f}s"
                )

        # Now proceed with speaker mapping
        click.echo("\nDetected speakers:")
        mapping = mapper.create_speaker_mapping(transcript_file)

        # Display final mapping
        click.echo("\nSpeaker mapping:")
        for speaker, name in mapping.items():
            click.echo(f"{speaker} => {name}")

        return mapping

    except NoSpeakersFoundError:
        raise click.ClickException("No speaker labels found in transcript")
    except SpeakerMapperError as e:
        raise click.ClickException(str(e))
    except Exception as e:
        raise click.ClickException(f"Unexpected error during speaker mapping: {str(e)}")


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
        transcriber.transcribe_file(audio_file, output_path)
        click.echo("Transcription completed successfully")
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
        # Get available prompty files
        from .prompty_utils import list_prompty_files

        prompty_files = list_prompty_files()

        if not prompty_files:
            raise click.ClickException(
                "No prompty files found in the prompts directory"
            )

        # Select prompt template
        selected_prompty = _select_prompt_template(prompty_files)

        # Determine output path
        output_path = _get_summary_output_path(ctx, transcript_file, output)

        # Generate summary
        summarizer = TranscriptProcessor(str(selected_prompty["path"]))
        summary = summarizer.generate_summary(transcript_file, output_path)
        click.echo(summary)
        return output_path

    except (TranscriptProcessorError, Exception) as e:
        raise click.ClickException(str(e))


def _select_prompt_template(prompty_files):
    """Helper to select a prompt template from available options."""
    # Display prompt options
    click.echo("\nAvailable summary prompts:")
    for i, prompty_file in enumerate(prompty_files, 1):
        click.echo(f"{i}. {prompty_file['description']}")
        if i == 1:
            click.echo("   (Default)")

    # Get user selection with retry logic
    max_attempts = 3
    selected_index = 0  # Default to first prompt

    for attempt in range(max_attempts):
        try:
            selection = click.prompt(
                "\nSelect a prompt number",
                type=str,
                default="1",
                show_default=False,
            )

            if not selection.strip():
                break  # Use default

            selected_num = int(selection)
            if 1 <= selected_num <= len(prompty_files):
                selected_index = selected_num - 1
                break
            else:
                click.echo(f"Please enter a number between 1 and {len(prompty_files)}")
        except ValueError:
            click.echo("Please enter a valid number")

        if attempt < max_attempts - 1:
            click.echo(f"Attempts remaining: {max_attempts - attempt - 1}")
        else:
            click.echo("\nUsing default prompt (1)")

    return prompty_files[selected_index]


def _get_summary_output_path(ctx, transcript_file: str, output: Optional[str]):
    """Helper to determine the output path for summary."""
    if output:
        return output

    # Auto-generate output path
    base_name = Path(transcript_file).stem
    return ctx.obj["config"].get_output_path(
        "summary", f"{base_name}_summary.md", use_date_subdir=True
    )


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
        ctx.invoke(speaker_map, transcript_file=transcript_file)

        # Summarize
        click.echo("\nStep 4: Generating summary...")
        summary_file = ctx.invoke(summarize, transcript_file=transcript_file)

        click.echo("\nPipeline completed successfully!")
        click.echo(f"Audio: {audio_file}")
        click.echo(f"Transcript: {transcript_file}")
        click.echo(f"Summary: {summary_file}")
        FileOpener.open_file(summary_file)

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
