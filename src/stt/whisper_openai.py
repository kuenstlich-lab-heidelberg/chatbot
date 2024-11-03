import speech_recognition as sr
import pyaudio
import time
import traceback
from openai import OpenAI
import wave
import io

from stt.base import BaseSTT
from vad.webrtc import WebrtcVad

_false_positiv = ["Amara.org", "Untertitel ", "Pff"]

class WhisperOpenAi(BaseSTT):
    def __init__(self, on_speech_start=None):
        self.vad = WebrtcVad(on_speech_start=self.on_speech_start, on_speech_end=self.on_speech_end, on_speech_data=self.on_speech_data)
        self.frames = []
        self._stopped = False
        self.transcription_ready = False
        self.current_transcription = None
        if on_speech_start is None:
            on_speech_start = lambda: None  # Leere Lambda-Funktion
        self.on_speech_start_callback = on_speech_start


    def stop(self):
        self.do_run = False
        self.vad.close()


    def on_speech_start(self):
        self.frames = []
        self.on_speech_start_callback()


    def on_speech_end(self):
        self.current_transcription = self.transcribe()
        # Now we use the is_false_positive method here to check the transcription
        if not self._is_false_positive(self.current_transcription):
            self.transcription_ready = True
        else:
            # If it's a false positive, we simply ignore the transcription
            #print("Transcription ignored due to false positive match.")
            pass


    def on_speech_data(self, frame, sample_rate):
        self.frames.append(frame)
        return (frame, pyaudio.paContinue)
 

    def _is_false_positive(self, transcription):
        # Check if any of the false positive phrases are in the transcription
        if transcription:
            for phrase in _false_positiv:
                if phrase.lower() in transcription.lower():
                    #print(f"Filtered out transcription due to false positive: '{phrase}' found.")
                    return True
        return False


    def _create_wav_file(self, frames, sample_rate):
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wave_file:
            wave_file.setnchannels(1)  # Mono
            wave_file.setsampwidth(2)   # PCM16
            wave_file.setframerate(sample_rate)
            wave_file.writeframes(b''.join(frames))
        buffer.seek(0)  # Reset buffer position to the beginning
        return buffer


    def transcribe(self):
        try:
            start_time = time.time()
            wav_buffer = self._create_wav_file(self.frames, self.vad.sample_rate)

            client = OpenAI()
            # Prepare the file parameter as a tuple
            filename = "audio.wav"  # Name of the file to be sent
            content_type = "audio/wav"  # Set content type for WAV files

            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                language="de",
                file=(filename, wav_buffer, content_type)
            )
  
            # Measure how much time it took to transcribe
            duration = time.time() - start_time
            print(f"Transcription completed in {duration:.2f} seconds.")
            print(transcription.text)

            return transcription.text
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""


    def start_recording(self):
        # Start the VAD process and yield transcriptions as they become available
        print("Starting VAD...")
        try:
            self.vad.start()
            self.do_run = True
            while self.do_run == True:
                if self.transcription_ready:
                    self.transcription_ready = False
                    if self.current_transcription:
                        print(self.current_transcription)
                        yield self.current_transcription
                else:
                    # Add a small sleep to prevent excessive CPU usage
                    time.sleep(0.1)
        except Exception as e:
            print(f"Error starting VAD: {e}")
            traceback.print_exc()
        finally:
            self.vad.close()

