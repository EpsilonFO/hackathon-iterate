"""
Custom Audio Interface with Echo Cancellation for ElevenLabs
Prevents feedback loop when using speakers instead of headphones
"""
import pyaudio
import numpy as np
import queue
import threading
from typing import Optional
from elevenlabs.conversational_ai.conversation import AudioInterface


class EchoCancellationAudioInterface(AudioInterface):
    """
    Audio interface with echo cancellation to prevent feedback loop.
    Uses dynamic volume threshold and silence detection.
    """

    def __init__(
        self,
        input_device_id: Optional[int] = None,
        output_device_id: Optional[int] = None,
        sample_rate: int = 16000,
        chunk_size: int = 4096,
        volume_threshold: float = 0.015,  # Increased to reduce sensitivity
        silence_duration: float = 0.5,    # Time after playback before listening
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.volume_threshold = volume_threshold
        self.silence_duration = silence_duration

        self.input_device_id = input_device_id
        self.output_device_id = output_device_id

        # Playback state tracking
        self.is_playing = False
        self.last_playback_time = 0
        self.playback_lock = threading.Lock()

        # Audio buffers
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()

        # PyAudio setup
        self.audio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None

        # Noise floor calibration
        self.noise_floor = 0.0
        self.calibration_samples = []
        self.is_calibrated = False

    def start(self):
        """Start audio streams"""
        # Input stream (microphone)
        self.input_stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.input_device_id,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._input_callback
        )

        # Output stream (speakers)
        self.output_stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            output=True,
            output_device_index=self.output_device_id,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._output_callback
        )

        print("🎤 Audio interface started with echo cancellation")
        print(f"📊 Volume threshold: {self.volume_threshold}")
        print("🔇 Calibrating noise floor (please stay quiet for 2 seconds)...")

        self.input_stream.start_stream()
        self.output_stream.start_stream()

    def stop(self):
        """Stop audio streams"""
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        self.audio.terminate()
        print("🔴 Audio interface stopped")

    def _input_callback(self, in_data, frame_count, time_info, status):
        """Handle input audio from microphone"""
        audio_data = np.frombuffer(in_data, dtype=np.int16)

        # Calibrate noise floor (first 2 seconds)
        if not self.is_calibrated:
            self.calibration_samples.append(audio_data)
            if len(self.calibration_samples) >= 30:  # ~2 seconds at 16kHz
                all_samples = np.concatenate(self.calibration_samples)
                self.noise_floor = np.std(all_samples.astype(np.float32) / 32768.0) * 1.5
                self.is_calibrated = True
                print(f"✅ Calibration complete. Noise floor: {self.noise_floor:.4f}")
                self.calibration_samples = []

        # Calculate volume (RMS)
        volume = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)) / 32768.0

        # Check if we should process this audio
        import time
        current_time = time.time()

        with self.playback_lock:
            time_since_playback = current_time - self.last_playback_time
            should_ignore = self.is_playing or time_since_playback < self.silence_duration

        # Apply echo cancellation logic
        if should_ignore:
            # Agent is speaking or just finished - ignore microphone input
            return (None, pyaudio.paContinue)

        # Use adaptive threshold based on noise floor
        adaptive_threshold = max(self.volume_threshold, self.noise_floor * 2)

        if volume > adaptive_threshold:
            # Valid speech detected
            self.input_queue.put(in_data)

        return (None, pyaudio.paContinue)

    def _output_callback(self, in_data, frame_count, time_info, status):
        """Handle output audio to speakers"""
        try:
            data = self.output_queue.get_nowait()

            # Mark that we're playing audio
            import time
            with self.playback_lock:
                self.is_playing = True
                self.last_playback_time = time.time()

            return (data, pyaudio.paContinue)
        except queue.Empty:
            with self.playback_lock:
                self.is_playing = False
            return (bytes(frame_count * 2), pyaudio.paContinue)

    def input(self) -> bytes:
        """Get audio input from microphone (blocking)"""
        try:
            return self.input_queue.get(timeout=0.1)
        except queue.Empty:
            return b''

    def output(self, audio_data: bytes):
        """Send audio to speakers"""
        self.output_queue.put(audio_data)

    def interrupt(self):
        """Clear output queue (user interrupted)"""
        while not self.output_queue.empty():
            try:
                self.output_queue.get_nowait()
            except queue.Empty:
                break

        with self.playback_lock:
            self.is_playing = False


# Helper function to list available audio devices
def list_audio_devices():
    """List all available audio input/output devices"""
    audio = pyaudio.PyAudio()
    print("\n🎤 Available Audio Devices:\n")

    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        print(f"Device {i}: {info['name']}")
        print(f"  - Max Input Channels: {info['maxInputChannels']}")
        print(f"  - Max Output Channels: {info['maxOutputChannels']}")
        print(f"  - Default Sample Rate: {info['defaultSampleRate']}")
        print()

    audio.terminate()


if __name__ == "__main__":
    # Test the audio interface
    print("Testing Echo Cancellation Audio Interface\n")
    list_audio_devices()
