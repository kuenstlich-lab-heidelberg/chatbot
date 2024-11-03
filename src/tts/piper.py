import numpy as np
import pyaudio
import threading
from tts.base import BaseTTS
from piper.voice import PiperVoice

class PiperTTS(BaseTTS):
    def __init__(self):
        super().__init__()
        self.model = "/Users/D023280/Documents/workspace/künstlich-lab/chat/chatbot/piper_voices/de_DE-thorsten-high.onnx"
        self.voice = PiperVoice.load(self.model)
        self.sample_rate = self.voice.config.sample_rate
        self.stop_event = threading.Event()
        self.player_stream = None
        self.audio_thread = None
        self.speed = 1.3

    def speak(self, text):
        print("PiperTTS: " + text)

        # Ensure any ongoing playback is stopped before starting a new one
        self.stop()

        # Clear the stop event
        self.stop_event.clear()

        def play_audio():
            try:
                # Initialize and open the audio stream
                self.player_stream = pyaudio.PyAudio().open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    output=True,
                    frames_per_buffer=1024  # Set a smaller buffer size for lower latency
                )

                # Stream audio generated by Piper
                for audio_bytes in self.voice.synthesize_stream_raw(text):
                    # Check stop event after each chunk
                    if self.stop_event.is_set():
                        break
                    # Convert the audio to int16 format for playback
                    audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
                    # Play the audio data immediately
                    self.player_stream.write(audio_data.tobytes())
            except Exception as e:
                print(f"Error in play_audio thread: {e}")
            finally:
                # Close the audio stream as soon as possible after stopping
                self._close_stream()

        # Start the playback in a separate thread
        self.audio_thread = threading.Thread(target=play_audio)
        self.audio_thread.start()


    def stop(self):
        print("PiperTTS: stop")
        # Set the stop event to signal the playback thread to stop
        self.stop_event.set()
        
        try:
            # Ensure the audio stream stops immediately by closing it
            self._close_stream()
            
            # Wait for the audio thread to finish if it's still running
            if self.audio_thread is not None and self.audio_thread.is_alive():
                self.audio_thread.join()
                print("Audio thread joined successfully.")
            self.audio_thread = None
        except Exception as e:
            print(f"Error in stop method: {e}")

    def _close_stream(self):
        """Helper method to safely close the audio stream."""
        if self.player_stream is not None:
            try:
                self.player_stream.stop_stream()
                self.player_stream.close()
                print("Player stream closed successfully.")
            except Exception as e:
                print(f"Error while closing the stream: {e}")
            finally:
                self.player_stream = None

    def __del__(self):
        # Ensure resources are cleaned up on deletion
        self.stop()
        if hasattr(self, 'audio_interface') and self.audio_interface is not None:
            self.audio_interface.terminate()
