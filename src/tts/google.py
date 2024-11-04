import numpy as np
import sys
import threading
import google.cloud.texttospeech as tts
import re
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

from tts.base import BaseTTS

class GoogleTTS(BaseTTS):
    def __init__(self, audio_sink):
        super().__init__()
        if audio_sink is None:
            print("No audio_sink to use")
            sys.exit(1)

        self.sample_rate = 24000  # Google TTS standard sample rate
        self.stop_event = threading.Event()
        self.audio_thread = None
        self.audio_sink = audio_sink
        self.client = tts.TextToSpeechClient()


    def speak(self, text):
        if self.audio_sink is None:
            print("No audio_sink to use")
            sys.exit(1)
        
        self.stop_event.clear()
        first_part, second_part = self._split_text(text)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_first = executor.submit(self._synthesize_text, first_part)
            future_second = executor.submit(self._synthesize_text, second_part) if second_part else None

            wait([future_first, future_second] if future_second else [future_first], return_when=FIRST_COMPLETED)
            audio_data_first = self._apply_fade_in(future_first.result())

            def play_audio_google():
                try:
                    for i in range(0, len(audio_data_first), 1024):
                        if self.stop_event.is_set():
                            break
                        chunk = audio_data_first[i:i+1024].tobytes()
                        self.audio_sink.write(chunk)

                    if future_second and not self.stop_event.is_set():
                        audio_data_second = self._apply_fade_in(future_second.result())
                        for i in range(0, len(audio_data_second), 1024):
                            if self.stop_event.is_set():
                                break
                            chunk = audio_data_second[i:i+1024].tobytes()
                            self.audio_sink.write(chunk)
                except Exception as e:
                    print(f"Error in play_audio_google thread: {e}")
                finally:
                    self.stop()

            self.audio_thread = threading.Thread(target=play_audio_google, daemon=True)
            self.audio_thread.start()


    def stop(self):
        self.stop_event.set()

        try:
            # Only join the thread if `stop` was not called from within `self.audio_thread`
            if (
                self.audio_thread is not None 
                and self.audio_thread.is_alive()
                and threading.current_thread() != self.audio_thread
            ):
                self.audio_thread.join()
            self.audio_thread = None
        except Exception as e:
            print(f"Error in stop method: {e}")


    def _synthesize_text(self, text):
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


    def _apply_fade_in(self, audio_data, duration_ms=10):
        """Apply a fade-in effect to the audio data."""
        audio_data = np.copy(audio_data)
        num_samples = int(self.sample_rate * duration_ms / 1000)
        fade = np.linspace(0, 1, num=num_samples)
        audio_data[:num_samples] = (audio_data[:num_samples].astype(float) * fade).astype(np.int16)
        return audio_data

    def _split_text(self, text):
        # Split text into first sentence and the rest
        split = re.split(r'(?<=[.!?])\s+', text, maxsplit=1)
        first_part = split[0]
        second_part = split[1] if len(split) > 1 else ""
        return first_part, second_part
