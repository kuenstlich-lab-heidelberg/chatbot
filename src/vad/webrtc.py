import pyaudio
import webrtcvad
import traceback
from vad.base import BaseVad

class WebrtcVad(BaseVad):
    def __init__(self, on_speech_start=None, on_speech_end=None, on_speech_data=None):
        self.audio_interface = pyaudio.PyAudio()
        self.stream = None

        self.vad = webrtcvad.Vad(2)
        self.sample_rate = 16000
        self.format = pyaudio.paInt16
        self.frame_duration_ms = 30
        self.frames = []
        self.recording = False
        self.silence_duration = 0  # Track duration of silence
        self.silence_threshold = 700  # Silence threshold in milliseconds
        self.chunk_size = int(self.sample_rate * self.frame_duration_ms / 1000)

        if on_speech_data is None:
            on_speech_data = lambda: None
        self.on_speech_data = on_speech_data

        if on_speech_start is None:
            on_speech_start = lambda: None
        self.on_speech_start = on_speech_start

        if on_speech_end is None:
            on_speech_end = lambda: None
        self.on_speech_end = on_speech_end


    def start(self):
        self.stream = self.audio_interface.open(
            format=self.format,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self.audio_callback
        )
        self.stream.start_stream()
        print("VAD Audio stream started.")


    def close(self):
        if self.stream is not None:
            print("Stopping audio stream...")
            try:
                self.stream.stop_stream()
                self.stream.close()
                print("Audio stream stopped.")
            except Exception as e:
                print(f"Error stopping audio stream: {e}")
                traceback.print_exc()
            finally:
                self.stream = None
      

    def audio_callback(self, in_data, frame_count, time_info, status):
        try:
            if in_data is not None and self.vad.is_speech(in_data, self.sample_rate):
                if not self.recording:
                    print("Speech detected, starting recording...")
                    self.on_speech_start()
                    self.recording = True
                    self.silence_duration = 0
                self.on_speech_data(in_data, self.sample_rate)
            else:
                if self.recording:
                    self.silence_duration += self.frame_duration_ms                    
                    if self.silence_duration >= self.silence_threshold:
                        print("Silence detected, stopping recording...")
                        self.on_speech_end()
                        self.recording = False
            return (in_data, pyaudio.paContinue)
        except Exception as e:
            print(f"Error in audio callback: {e}")
            traceback.print_exc()
            return (None, pyaudio.paContinue)

