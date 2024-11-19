import abc
import asyncio
from typing import Callable, Awaitable, Union

# Definition of BaseTTS class
class BaseTTS(abc.ABC):
    def __init__(self, audio_sink):
        self.audio_sink = audio_sink
        # Speichern des aktuellen Event-Loops beim Initialisieren
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.get_event_loop()

    @abc.abstractmethod
    async def speak(self, session, text, on_start: Callable = lambda session: None):
        pass

    @abc.abstractmethod
    def stop(self, session):
        pass


    def run_callback(self, callback: Union[Callable[[object], None], Awaitable], session):
        """
        Utility-Funktion, um Callbacks sicher auszuführen (sowohl synchron als auch asynchron).

        :param callback: Der Callback (synchron oder asynchron).
        :param session: Der Session-Kontext, der an den Callback übergeben wird.
        """
        if asyncio.iscoroutinefunction(callback):
            # Wenn der Callback asynchron ist, führe ihn mit await aus
            callback(session)
        else:
            # Andernfalls führe den synchronen Callback im Haupt-Event-Loop aus
            #loop = asyncio.get_running_loop()
            self.loop.call_soon_threadsafe(callback, session)