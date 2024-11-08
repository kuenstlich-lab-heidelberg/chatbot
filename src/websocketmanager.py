import asyncio
from fastapi import WebSocket
from typing import Dict
from queue import Queue, Empty
import time
from starlette.websockets import WebSocketState

class WebSocketManager:
    # Class-level dictionary for managing connections
    connections: Dict[str, WebSocket] = {}
    message_queues: Dict[str, Queue] = {}          # Thread-safe queue for text messages
    binary_message_queues: Dict[str, Queue] = {}    # Thread-safe queue for binary messages

    @staticmethod
    async def connect(websocket: WebSocket, token: str) -> None:
        """Accepts a WebSocket connection and stores it under the provided token."""
        await websocket.accept()
        WebSocketManager.connections[token] = websocket
        WebSocketManager.message_queues[token] = Queue()  # Initialize text message queue
        WebSocketManager.binary_message_queues[token] = Queue()  # Initialize binary message queue

    @staticmethod
    async def remove(token: str) -> None:
        """Closes and removes a specific WebSocket connection by token."""
        if token in WebSocketManager.connections:
            del WebSocketManager.connections[token]
            del WebSocketManager.message_queues[token]
            del WebSocketManager.binary_message_queues[token]

    @staticmethod
    async def disconnect(token: str) -> None:
        """Closes and removes a specific WebSocket connection by token."""
        if token in WebSocketManager.connections:
            websocket = WebSocketManager.connections[token]
            if websocket.application_state == WebSocketState.CONNECTED:
                await websocket.close()
            del WebSocketManager.connections[token]
            del WebSocketManager.message_queues[token]
            del WebSocketManager.binary_message_queues[token]

    @staticmethod
    def send_message(token: str, message: str) -> None:
        """Adds a text message to the queue to be processed asynchronously."""
        print("SEND SEND SEND SEND")
        print(token, message)
        if token in WebSocketManager.message_queues:
            WebSocketManager.message_queues[token].put(message)  # Thread-safe enqueue for text

    @staticmethod
    def send_bytes(token: str, data: bytes) -> None:
        """Adds a binary message to the binary queue to be processed asynchronously."""
        if token in WebSocketManager.binary_message_queues:
            #print("+", end = "")
            WebSocketManager.binary_message_queues[token].put(data)
            # allow other thread to read form the queue. IF this sleep is not in, then the 
            # writer blocks everything. The writer is sometimes too fast and the read has noc chance to get something.
            time.sleep(0.01)


    @staticmethod
    async def process_queue(token: str) -> None:
        """Processes and sends all messages in both text and binary queues for the given token."""
        if token in WebSocketManager.connections:
            websocket = WebSocketManager.connections[token]

            # Process text messages
            message_queue = WebSocketManager.message_queues[token]
            while True:
                try:
                    message = message_queue.get_nowait()  # Non-blocking get for text messages
                    print("FOUND MESSAGE.......")
                    if websocket.application_state == WebSocketState.CONNECTED:
                        await websocket.send_text(message)
                except Empty:
                    break

            # Process binary messages
            binary_queue = WebSocketManager.binary_message_queues[token]
            while True:
                try:
                    binary_data = binary_queue.get_nowait()  # Non-blocking get for binary messages
                    await websocket.send_bytes(binary_data)
                    #print("-", end="")
                except Empty:
                    break
