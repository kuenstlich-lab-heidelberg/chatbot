from tts.base import BaseTTS

import threading
import time
from openai import OpenAI

class OpenAiTTS(BaseTTS):
    def __init__(self, audio_sink):
        super().__init__(audio_sink)
        self.stop_event = threading.Event()
        self.player_stream = None
        self.client = OpenAI()
        self.audio_thread = None
        self.max_retries = 3


    def speak(self, session, text):
        # Ensure any ongoing playback is stopped before starting a new one
        self.stop()

        # Clear the stop event
        self.stop_event.clear()

        def play_audio():
            try:

                # Attempt to stream audio with retries
                retries = 0
                while retries < self.max_retries:
                    try:
                        with self.client.audio.speech.with_streaming_response.create(
                            input=text,
                            speed=1.2,
                            response_format="pcm",
                            voice="onyx",
                            model="tts-1"
                        ) as response:
                            for chunk in response.iter_bytes(chunk_size=8192):
                                if self.stop_event.is_set():
                                    break
                                self.audio_sink.write(session, chunk)
                        break  # Exit loop if streaming succeeds
                    except (ConnectionError, TimeoutError) as e:
                        retries += 1
                        print(f"Connection error ({retries}/{self.max_retries}): {e}")
                        time.sleep(1)
                    except Exception as e:
                        print(f"Unexpected error during streaming: {e}")
                        break
            except Exception as e:
                print(f"Error in play_audio thread: {e}")

        self.audio_thread = threading.Thread(target=play_audio)
        self.audio_thread.start()


    def stop(self, session):
        try:
            self.stop_event.set()

            # Wait for the audio thread to finish if it's still running
            if self.audio_thread is not None and self.audio_thread.is_alive():
                self.audio_thread.join()
            self.audio_thread = None
        except Exception as e:
            print(f"Error in stop method: {e}")

