import pygame
from pygame import mixer
import os
import time

from sound.sound import Sound

pygame.mixer.init()


class Jukebox:
    def __init__(self, sound_dir):
        self.sound_dir= sound_dir
        self.playing_sounds = []

    def play_sound(self, file_name, loop=True):
        """
        Play a sound from the given file path.
        :param file_path: Absolute path to the sound file (wav or mp3).
        :param loop: If True, play sound in an infinite loop; otherwise, play once.
        :return: PlayingSound object for controlling this sound.
        """
        if not file_name or len(file_name)==0:
            return #silently
        
        file_path = f"{self.sound_dir}{file_name}"

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
            playing_sound = Sound(sound, channel)
            self.playing_sounds.append(playing_sound)
            return playing_sound
        except:
            print(f"Unable to play sound: '{file_path}'")
            return None


    def stop_all(self):
        """Stop all currently playing sounds."""
        for playing_sound in self.playing_sounds:
            playing_sound.stop()
        self.playing_sounds.clear()


# Example Usage
if __name__ == "__main__":
    jukebox = Jukebox()
    # Example sound file path; replace with an actual file path on your system
    sound_path = "bg-ocean.mp3"
    
    # Play sound once
    #sound1 = jukebox.play_sound(sound_path, loop=False)

    # Play sound infinitely in a loop
    sound2 = jukebox.play_sound(sound_path, loop=True)

    # Stop all sounds after some time or in response to an event
    # jukebox.stop_all()
    while True:
        time.sleep(0.5)