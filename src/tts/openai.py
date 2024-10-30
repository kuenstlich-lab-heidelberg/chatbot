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

        # Vor dem Starten prüfen, ob eine Wiedergabe läuft, und diese stoppen
        self.stop()

        self.stop_event.clear()  # Event zurücksetzen

        def play_audio():
            try:
                self.player_stream = pyaudio.PyAudio().open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=24000,
                    output=True
                )
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
                        self.player_stream.write(chunk)
            except Exception as e:
                print(f"Fehler im play_audio-Thread: {e}")
            finally:
                # Stellen Sie sicher, dass der Stream geschlossen wird
                if self.player_stream is not None:
                    try:
                        self.player_stream.stop_stream()
                        self.player_stream.close()
                        print("Player-Stream geschlossen")
                    except Exception as e:
                        print(f"Fehler beim Schließen des Streams: {e}")
                    finally:
                        self.player_stream = None

        # Starten Sie den neuen Thread für die Audiowiedergabe
        self.audio_thread = threading.Thread(target=play_audio)
        self.audio_thread.start()


    def stop(self):
        print("OpenAiTTS: stop")
        self.stop_event.set()
        if self.audio_thread is not None:
            if self.audio_thread.is_alive():
                self.audio_thread.join()
            self.audio_thread = None
