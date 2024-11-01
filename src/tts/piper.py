import asyncio
import numpy as np
import sounddevice as sd
from tts.base import BaseTTS
from piper.voice import PiperVoice
from concurrent.futures import ThreadPoolExecutor

class PiperTTS(BaseTTS):
    def __init__(self):
        super().__init__()
        self.model = "/Users/D023280/Documents/workspace/künstlich-lab/chat/chatbot/piper_voices/Thorsten-Voice_Hessisch_Piper_high-Oct2023.onnx"
        self.voice = PiperVoice.load(self.model)
        self.sample_rate = self.voice.config.sample_rate
        self.talk = False
        self.stream = None
        self.executor = ThreadPoolExecutor(max_workers=1)  # For async thread management
        self.loop = asyncio.new_event_loop()


    def speak(self, text):
        self.stop()
        self.stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype='int16')
        self.stream.start()
        self.talk = True
        self.executor.submit(self._run_async_playback, text)


    def _run_async_playback(self, text):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._play_audio_async(text))


    async def _play_audio_async(self, text):
        for audio_bytes in self.voice.synthesize_stream_raw(text):
            if not self.talk:
                break  # Stop if talk is False
            int_data = np.frombuffer(audio_bytes, dtype=np.int16)
            self.stream.write(int_data)
        self.stream.stop()
        self.stream.close()


    def stop(self):
        self.talk = False
        if self.stream and self.stream.active:
            self.stream.stop()
            self.stream.close()
        print("Piper: stopped speaking")
