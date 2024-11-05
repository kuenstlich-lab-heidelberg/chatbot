import pyaudio

from audio.base_sink import BaseAudioSink
from websocketmanager import WebSocketManager

class WebSocketSink(BaseAudioSink):

    def __init__(self):
        self.close = False


    def write(self, session, chunk):
        if not self.close:
            WebSocketManager.send_bytes(session.ws_token, chunk)

    def close(self, session):
        self.close = True

