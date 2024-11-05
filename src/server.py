from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, Dict
from uuid import uuid4
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chat Application", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory session store
session_store: Dict[str, Dict] = {}

# WebSocket manager for handling connections
class WSManager:
    def __init__(self):
        self.connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, token: str):
        await websocket.accept()
        websocket_id = str(uuid4())
        if token not in self.connections:
            self.connections[token] = {}
        self.connections[token][websocket_id] = websocket
        return websocket_id

    async def disconnect(self, token: str, websocket_id: str):
        if token in self.connections and websocket_id in self.connections[token]:
            await self.connections[token][websocket_id].close()
            del self.connections[token][websocket_id]

    async def send_message(self, token: str, websocket_id: str, message: str):
        if token in self.connections and websocket_id in self.connections[token]:
            await self.connections[token][websocket_id].send_text(message)

ws_manager = WSManager()

# Pydantic model for chat request payload
class ChatMessage(BaseModel):
    text: str

# Middleware to retrieve or create a session
def get_session(request: Request, response: Response) -> Dict:
    session_id = request.cookies.get("session_id")
    if session_id and session_id in session_store:
        return session_store[session_id]
    else:
        # Create a new session if one doesn't exist
        session_id = str(uuid4())
        session_store[session_id] = {"messages": []}
        response.set_cookie(key="session_id", value=session_id)
        return session_store[session_id]

# UI endpoint that serves the HTML interface at /ui
@app.get("/ui", response_class=HTMLResponse)
async def ui(request: Request, response: Response):
    # Create or retrieve session when loading the page
    session = get_session(request, response)
    return templates.TemplateResponse("index.html", {"request": request, "session": session})

# Chat REST endpoint for processing messages
@app.post("/api/chat")
async def chat(request: Request, data: ChatMessage, response: Response):
    session = get_session(request, response)
    message = data.text
    logger.info(f"Received message: {message}")
    
    # Process the message and store it in the session
    response_text = f"Echo: {message}"
    session["messages"].append({"text": message, "response": response_text})
    
    # Return the processed response
    return JSONResponse({"response": response_text})

# WebSocket connection endpoint
@app.get("/websocket/connect")
async def ws_connect(request: Request, response: Response):
    session = get_session(request, response)
    unique_id = str(uuid4())
    session["ws_token"] = unique_id
    return {"token": unique_id}

# WebSocket endpoint for real-time communication
@app.websocket("/websocket/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    websocket_id = await ws_manager.connect(websocket, token)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received via WebSocket: {data}")
            # Echo back the message
            await ws_manager.send_message(token, websocket_id, f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        await ws_manager.disconnect(token, websocket_id)

# Entry point to start the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
