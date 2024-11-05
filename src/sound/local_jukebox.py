import pygame
from pygame import mixer
import os
import time

pygame.mixer.init()


class LocalJukebox:
    def __init__(self):
        self.playing_channels = []

    def play_sound(self, session, file_name, loop=True):
        """
        Play a sound from the given file path.
        :param file_path: Absolute path to the sound file (wav or mp3).
        :param loop: If True, play sound in an infinite loop; otherwise, play once.
        :return: PlayingSound object for controlling this sound.
        """
        if not file_name or len(file_name)==0:
            return #silently
        
        sound_dir = session.conversation_dir
        file_path = f"{sound_dir}{file_name}"

        try:
            if not os.path.isabs(file_path):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(current_dir, file_path)
        
            # Load the sound
            sound = mixer.Sound(file_path)
            
            # Find a free channel to play the sound
            channel = mixer.find_channel()
            if channel is None:
                raise RuntimeError("No free channel available to play sound")

            # Play the sound
            loops = -1 if loop else 0
            channel.play(sound, loops=loops)
            
            # Create a PlayingSound object and add it to the list of playing sounds
            self.playing_channels.append(channel)
        except:
            print(f"Unable to play sound: '{file_path}'")


    def stop_all(self, session):
        """Stop all currently playing sounds."""
        for channel in self.playing_channels:
            if channel.get_busy():
                channel.stop()
        self.playing_channels.clear()
