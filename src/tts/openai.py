from tts.base import BaseTTS
import pyaudio
import threading
from openai import OpenAI

class OpenAiTTS(BaseTTS):
    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()
        self.player_stream = None
        self.client = OpenAI()
        self.audio_thread = None

    def speak(self, text):
        print("OpenAiTTS: " + text)

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
                    rate=24000,
                    output=True
                )

                # Stream audio from the TTS service
                with self.client.audio.speech.with_streaming_response.create(
                    input=text,
                    speed=1.2,
                    response_format="pcm",
                    voice="onyx",
                    model="tts-1"
                ) as response:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        # Stop playback if stop_event is set
                        if self.stop_event.is_set():
                            break
                        self.player_stream.write(chunk)
            except Exception as e:
                print(f"Error in play_audio thread: {e}")
            finally:
                # Ensure the audio stream is closed in any case
                self._close_stream()

        # Start the playback in a separate thread
        self.audio_thread = threading.Thread(target=play_audio)
        self.audio_thread.start()


    def stop(self):
        print("OpenAiTTS: stop")
        try:
            # Set the stop event to signal the playback thread to stop
            self.stop_event.set()

            # Wait for the audio thread to finish if it's still running
            if self.audio_thread is not None and self.audio_thread.is_alive():
                self.audio_thread.join()
                print("Audio thread joined successfully.")
            self.audio_thread = None
        except Exception as e:
            print(f"Error in stop method: {e}")
        finally:
            # Ensure the audio stream is closed in case it wasn't already
            self._close_stream()


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
