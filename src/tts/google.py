import numpy as np
import pyaudio
import threading
import google.cloud.texttospeech as tts

from tts.base import BaseTTS

class GoogleTTS(BaseTTS):
    def __init__(self):
        super().__init__()
        self.sample_rate = 24000  # Google TTS standard sample rate (adjust if needed)
        self.stop_event = threading.Event()
        self.player_stream = None
        self.audio_thread = None

        # Set up Google Text-to-Speech client
        self.client = tts.TextToSpeechClient()
        

    def speak(self, text):
        print("GoogleTTS: " + text)

        # Ensure any ongoing playback is stopped before starting a new one
        self.stop()

        # Clear the stop event for a new playback
        self.stop_event.clear()

        def play_audio():
            try:
                # Synthesize the speech
                response = self.client.synthesize_speech(
                    input=tts.SynthesisInput(text=text),
                    voice=tts.VoiceSelectionParams(
                        language_code="de-DE",
                        name="de-DE-Journey-D"
                    ),
                    audio_config=tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)
                )

                # Convert audio_content (base64-encoded bytes) to int16 for playback
                audio_data = np.frombuffer(response.audio_content, dtype=np.int16)

                # Initialize and open the audio stream
                self.player_stream = pyaudio.PyAudio().open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    output=True,
                    frames_per_buffer=1024  # Set a smaller buffer size for lower latency
                )

                # Write audio data to the stream
                for i in range(0, len(audio_data), 1024):
                    if self.stop_event.is_set():
                        break
                    self.player_stream.write(audio_data[i:i+1024].tobytes())
            except Exception as e:
                print(f"Error in play_audio thread: {e}")
            finally:
                # Ensure the audio stream is closed in any case
                self._close_stream()

        # Start the playback in a separate thread
        self.audio_thread = threading.Thread(target=play_audio)
        self.audio_thread.start()

    def stop(self):
        print("GoogleTTS: stop")
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
