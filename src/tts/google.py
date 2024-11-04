import numpy as np
import pyaudio
import threading
import google.cloud.texttospeech as tts
import re
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

from tts.base import BaseTTS

class GoogleTTS(BaseTTS):
    def __init__(self):
        super().__init__()
        self.sample_rate = 24000  # Google TTS standard sample rate
        self.stop_event = threading.Event()
        self.lock = threading.Lock()  # Lock for thread-safe access to the player stream
        self.player_stream = None
        self.audio_thread = None

        self.pyaudio_instance = pyaudio.PyAudio()  # Singleton instance of pyaudio

        # Set up Google Text-to-Speech client
        self.client = tts.TextToSpeechClient()

    def _split_text(self, text):
        # Split text into first sentence and the rest
        split = re.split(r'(?<=[.!?])\s+', text, maxsplit=1)
        first_part = split[0]
        second_part = split[1] if len(split) > 1 else ""
        return first_part, second_part

    def synthesize_text(self, text):
        """Synthesize text and return audio data."""
        response = self.client.synthesize_speech(
            input=tts.SynthesisInput(text=text),
            voice=tts.VoiceSelectionParams(
                language_code="de-DE",
                name="de-DE-Journey-D"
            ),
            audio_config=tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)
        )
        # Convert audio_content to int16 format for playback
        audio_data = np.frombuffer(response.audio_content, dtype=np.int16)
        return audio_data

    def apply_fade_in(self, audio_data, duration_ms=10):
        """Apply a fade-in effect to the audio data."""
        audio_data = np.copy(audio_data)
        num_samples = int(self.sample_rate * duration_ms / 1000)
        fade = np.linspace(0, 1, num=num_samples)
        audio_data[:num_samples] = (audio_data[:num_samples].astype(float) * fade).astype(np.int16)
        return audio_data

    def speak(self, text):
        self.stop()

        self.stop_event.clear()
        first_part, second_part = self._split_text(text)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_first = executor.submit(self.synthesize_text, first_part)
            future_second = executor.submit(self.synthesize_text, second_part) if second_part else None

            done, _ = wait([future_first, future_second] if future_second else [future_first], return_when=FIRST_COMPLETED)
            audio_data_first = self.apply_fade_in(future_first.result())

            with self.lock:
                if self.player_stream is None:
                    self.player_stream = self.pyaudio_instance.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=self.sample_rate,
                        output=True,
                        frames_per_buffer=1024
                    )

            def play_audio():
                try:
                    with self.lock:
                        for i in range(0, len(audio_data_first), 1024):
                            if self.stop_event.is_set():
                                break
                            chunk = audio_data_first[i:i+1024].tobytes()
                            self.player_stream.write(chunk)

                        if future_second and not self.stop_event.is_set():
                            audio_data_second = self.apply_fade_in(future_second.result())
                            for i in range(0, len(audio_data_second), 1024):
                                if self.stop_event.is_set():
                                    break
                                chunk = audio_data_second[i:i+1024].tobytes()
                                self.player_stream.write(chunk)

                except Exception as e:
                    print(f"Error in play_audio thread: {e}")
                finally:
                    self._close_stream()

            self.audio_thread = threading.Thread(target=play_audio)
            self.audio_thread.start()

    def stop(self):
        self.stop_event.set()
        try:
            self._close_stream()
            if self.audio_thread is not None and self.audio_thread.is_alive():
                self.audio_thread.join()
            self.audio_thread = None
        except Exception as e:
            print(f"Error in stop method: {e}")


    def _close_stream(self):
        with self.lock:
            if self.player_stream is not None:
                try:
                    self.player_stream.stop_stream()
                    self.player_stream.close()
                except Exception as e:
                    print(f"Error while closing the stream: {e}")
                finally:
                    self.player_stream = None

