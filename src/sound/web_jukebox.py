from websocketmanager import WebSocketManager

import json
from typing import Dict, List

class WebJukebox:
    def __init__(self, sound_dir):
        self.sound_dir= sound_dir

    def play_sound(self, session, file_name, loop=True):
        """
        Play a sound from the given file path.
        :param file_path: Absolute path to the sound file (wav or mp3).
        :param loop: If True, play sound in an infinite loop; otherwise, play once.
        :return: PlayingSound object for controlling this sound.
        """
        print(f"PLAY SOUND: {file_name}")
        if not file_name or len(file_name)==0:
            return #silently
        message = json.dumps({ "function":"sound.play_sound", "loop":loop, "file_name":file_name}, indent=4)
        WebSocketManager.send_message(session.ws_token, message)


    def stop_all(self, session):
        """Stop all currently playing sounds."""
        message = json.dumps({ "function":"sound.stop_all"}, indent=4)
        WebSocketManager.send_message(session.ws_token, message)

