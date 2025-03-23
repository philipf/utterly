"""
Audio recording functionality for utterly.
"""

import queue
import datetime
from typing import Optional, Dict, Any
import sounddevice as sd
import soundfile as sf
import numpy as np


class AudioRecorder:
    """Handles audio recording functionality."""

    def __init__(self):
        self.queue = queue.Queue()

    def callback(self, indata: np.ndarray, frames: int, time: Any, status: Any) -> None:
        """Callback for the InputStream to process audio blocks."""
        if status:
            print(status, flush=True)
        self.queue.put(indata.copy())

    @staticmethod
    def list_devices() -> Dict:
        """List all available audio devices."""
        return sd.query_devices()

    @staticmethod
    def get_device_info(device: Optional[int] = None) -> Dict:
        """Get information about a specific input device."""
        return sd.query_devices(device, "input")

    def record(
        self,
        filename: Optional[str] = None,
        device: Optional[int] = None,
        samplerate: Optional[int] = None,
        channels: int = 2,
        subtype: Optional[str] = None,
    ) -> str:
        """
        Record audio to a file.

        Args:
            filename: Output filename. If None, generates timestamp-based name.
            device: Input device ID. If None, uses default.
            samplerate: Sampling rate. If None, uses device default.
            channels: Number of input channels.
            subtype: Sound file subtype (e.g. "PCM_24").

        Returns:
            str: Path to the recorded audio file.
        """
        try:
            # Get device sample rate if not specified
            if samplerate is None:
                device_info = self.get_device_info(device)
                samplerate = int(device_info["default_samplerate"])

            # Generate filename if not provided
            if filename is None:
                filename = (
                    datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".ogg"
                )

            # Print the device ID and device information
            print(f"Recording from device {device}: {self.get_device_info(device)}")

            # Record audio
            with sf.SoundFile(
                filename,
                mode="w",
                samplerate=samplerate,
                channels=channels,
                subtype=subtype,
            ) as audio_file:
                with sd.InputStream(
                    samplerate=samplerate,
                    device=device,
                    channels=channels,
                    callback=self.callback,
                ):
                    print("#" * 80)
                    print("Recording... Press Ctrl+C to stop")
                    print("#" * 80)

                    while True:
                        audio_file.write(self.queue.get())

        except KeyboardInterrupt:
            print("\nRecording finished: " + repr(filename))
            return filename
        except Exception as e:
            raise RuntimeError(f"Recording failed: {str(e)}")
