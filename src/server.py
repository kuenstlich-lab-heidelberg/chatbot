from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import textwrap

from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
import mimetypes
import secrets
import os
import json
import asyncio
from dotenv import load_dotenv
load_dotenv() 

from tts.factory import TTSEngineFactory
from llm.factory import LLMFactory
from stt.factory import STTFactory
from session import Session as ChatSession
from websocketmanager import WebSocketManager
from audio.websocket import WebSocketSink
from estimator import Estimator


# Definieren Sie den relativen Pfad zur system_prompt-Datei
SYSTEM_PROMPT_FILE = 'system_prompt.txt'

# Konvertieren Sie den Pfad in einen absoluten Pfad
SYSTEM_PROMPT_PATH = os.path.abspath(SYSTEM_PROMPT_FILE)

system_prompt = None

# Versuchen Sie, die system_prompt-Datei vom absoluten Pfad zu lesen
if os.path.exists(SYSTEM_PROMPT_PATH):
    try:
        with open(SYSTEM_PROMPT_PATH, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except Exception as e:
        print(f"Fehler beim Lesen der system_prompt-Datei '{SYSTEM_PROMPT_PATH}': {e}")
        print("Standard-System-Prompt wird verwendet.")
else:
    print(f"Warnung: system_prompt-Datei '{SYSTEM_PROMPT_PATH}' nicht gefunden. Standard-System-Prompt wird verwendet.")


app = FastAPI(title="Chat Application", version="1.0.0")
templates = Jinja2Templates(directory="templates")

session_store: Dict[str, Dict] = {}


class ChatMessage(BaseModel):
    text: str

def session_factory():
    # Prepare keyword arguments for the Session constructor
    session_kwargs = {
        'llm': LLMFactory.create(),
        'tts': TTSEngineFactory.create(WebSocketSink()),
        'stt': STTFactory.create(),
    }
    # Add system_prompt if available
    if system_prompt is not None:
        session_kwargs['system_prompt'] = system_prompt
    return ChatSession(**session_kwargs)


# Middleware to retrieve or create a session
def get_session(request: Request, response: Response) -> Dict:
    session_id = request.cookies.get("session_id")
    print(f"Current session_id (get_session): {session_id}")

    if session_id and session_id in session_store:
        return session_store[session_id], session_id

    if session_id is None:
        session_id = str(uuid4())
    
    session_store[session_id] = session_factory()
    response.set_cookie("session_id", session_id, httponly=True)
    return session_store[session_id], session_id


def get_session_by_token(token):
    for session_id, session in session_store.items():
        if session.ws_token == token:
            return session, session_id
    return None, None


async def send_tag_message_after_delay(token: str, tag_content: str, delay_in_seconds: float):
    try:
        await asyncio.sleep(delay_in_seconds)
        # Send message via WebSocketManager
        WebSocketManager.send_message(token, json.dumps({"function": "tag_event", "tag": tag_content}))
    except asyncio.CancelledError:
        # Task was cancelled
        pass


# Mount the static files directory
app.mount("/assets", StaticFiles(directory="static"), name="assets")


# Updated /ui route to require authentication
@app.get("/ui", response_class=HTMLResponse, name="ui")
async def ui(request: Request, response: Response):
    session, session_id = get_session(request, response)
    print(f"Using session with session_id: {request.cookies.get('session_id')} for /ui request")
    return templates.TemplateResponse("index.html", {"request": request, "session": session})


# Chat endpoint with cookie-based authentication
@app.post("/api/chat", name="chat")
async def chat(request: Request, data: ChatMessage, response: Response):
    session, session_id = get_session(request, response)
    text = data.text
    
    if text.lower() == "debug":
        session.llm.dump()
        return
     
    if text.lower() == "reset":
        session.llm.reset(session)
        return
    
    if text.lower() == "start":
        old_ws_token = session.ws_token
        session_store[session_id] = session_factory()
        session, session_id = get_session(request, response)
        session.ws_token = old_ws_token
        text = "Erkläre dem Spieler in kurzen Worten worum es hier geht und wer du bist"


    response_text = ""
    if len(text) > 0:
        response = session.llm.chat(session, text)
        session.tts.stop(session)
        response_text = response["text"]

    token = session.ws_token
    WebSocketManager.send_message(token, json.dumps({"function":"speak.stop"}))

    # Cancel existing scheduled tasks
    for task in session.scheduled_tasks:
        task.cancel()
    session.scheduled_tasks.clear()


    cleaned_text = Estimator.clean_up(response_text)
    
    wrapped_text = textwrap.fill(response_text, width=60)
    print("\n------------------------------------------------------------")
    print(wrapped_text)
    print("------------------------------------------------------------\n")

    # Definieren Sie die on_start Callback-Funktion
    def on_tts_start(session):
        tag_durations = Estimator.estimate_tag_locations(response_text)
        for tag_content, estimated_duration in tag_durations:
            task = asyncio.create_task(send_tag_message_after_delay(token, tag_content, estimated_duration))
            session.scheduled_tasks.append(task)

    session.tts.speak(session, cleaned_text, on_start=on_tts_start)
    
    return JSONResponse({"response": cleaned_text})


@app.get("/websocket/connect", name="ws_connect")
async def ws_connect(request: Request, response: Response):
    # Proceed to load the UI if authenticated
    session, session_id = get_session(request, response)

    if not session.ws_token:
        session.ws_token = str(uuid4())

    print(f"Retrieved or created ws_token: {session.ws_token}")
    return {"token": session.ws_token}


# WebSocket handling
@app.websocket("/websocket/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await WebSocketManager.connect(websocket, token)
    try:
        while True:
            await WebSocketManager.process_queue(token)
            
            #await asyncio.sleep(0.1)
            
            # Try to receive a message from the client with a timeout
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                data = json.loads(data)
                if data["function"] == "speak.stop":
                    session, session_id = get_session_by_token(token)
                    if session:
                        session.tts.stop(session)
                elif data["function"] == "speak.statistic":
                    Estimator.statistic(characters=data["characters"], duration= data["duration"])

            except asyncio.TimeoutError:
                # No data received; continue the loop
                pass

    except WebSocketDisconnect:
        print("WebSocket disconnected")
        await WebSocketManager.remove(token)
        

if __name__ == "__main__":
    import uvicorn
    
    Estimator.statistic(characters=430, duration=20.43)
    uvicorn.run(app, host="127.0.0.1", port=9000)


