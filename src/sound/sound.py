
class Sound:
    def __init__(self, sound, channel):
        self.sound = sound
        self.channel = channel

    def stop(self):
        """Stop this sound from playing."""
        if self.channel.get_busy():
            self.channel.stop()
