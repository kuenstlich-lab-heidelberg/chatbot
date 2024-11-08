from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Response, status, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
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

from motorcontroller.mock import MotorControlerMock
from state_engine import StateEngine
from tts.factory import TTSEngineFactory
from llm.factory import LLMFactory
from stt.factory import STTFactory
from session import Session as ChatSession
from sound.web_jukebox import WebJukebox
from websocketmanager import WebSocketManager
from audio.websocket import WebSocketSink

CONVERSATION_DIR  = os.getenv("CONVERSATION_DIR")
CONVERSATION_FILE =  os.getenv("CONVERSATION_FILE")


debug_ui = MotorControlerMock()
app = FastAPI(title="Chat Application", version="1.0.0")
templates = Jinja2Templates(directory="templates")

VALID_USERNAME = os.getenv("VALID_USERNAME", "user")
VALID_PASSWORD = os.getenv("VALID_PASSWORD", "pass")
session_store: Dict[str, Dict] = {}


class ChatMessage(BaseModel):
    text: str

def newChatSession():
    return ChatSession(
            conversation_dir = CONVERSATION_DIR,
            state_engine = StateEngine(f"{CONVERSATION_DIR}{CONVERSATION_FILE}"),
            llm = LLMFactory.create(),
            tts = TTSEngineFactory.create(WebSocketSink()),
            stt = STTFactory.create(),
            jukebox= WebJukebox(CONVERSATION_DIR)
        )

# Middleware to retrieve or create a session
def get_session(request: Request, response: Response) -> Dict:
    session_id = request.cookies.get("session_id")
    if session_id and session_id in session_store:
        return session_store[session_id]
    else:
        # Create a new session if one doesn't exist
        session_id = str(uuid4())
        session_store[session_id] = newChatSession()
        response.set_cookie(key="session_id", value=session_id)
        return session_store[session_id]


# GET route for the login page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# POST route for handling login form submissions
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Manually validate username and password without using HTTPBasic to avoid browser dialog
    if not (secrets.compare_digest(username, VALID_USERNAME) and secrets.compare_digest(password, VALID_PASSWORD)):
        # If credentials are invalid, re-render login page with an error message
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

    # Set a cookie for successful authentication and redirect to the main UI
    response = RedirectResponse(url="/ui", status_code=status.HTTP_302_FOUND)
    response.set_cookie("authenticated", "yes")  # Set an authentication cookie
    return response


# Updated /ui route to require authentication
@app.get("/ui", response_class=HTMLResponse)
async def ui(request: Request, response: Response):
    # Check if user is authenticated by looking for the "authenticated" cookie
    if request.cookies.get("authenticated") != "yes":
        return RedirectResponse(url="/login")  # Redirect to login if not authenticated

    # Proceed to load the UI if authenticated
    session = get_session(request, response)
    return templates.TemplateResponse("index.html", {"request": request, "session": session})


# Chat endpoint with cookie-based authentication
@app.post("/api/chat")
async def chat(request: Request, data: ChatMessage, response: Response):
    if request.cookies.get("authenticated") != "yes":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session = get_session(request, response)
    text = data.text
    
    if text.lower() == "debug":
        session.llm.dump()
        return
     
    if text.lower() == "reset":
        session.llm.reset(session)
        return
    
    if text.lower() == "start":
        session_id = request.cookies.get("session_id")
        session_store[session_id] = newChatSession()
        session = get_session(request, response)
        session.state_engine.trigger(session, "start")
        text = "Erkläre mir in kurzen Worten worum es hier geht und wer du bist"

    response_text = ""
    if len(text) > 0:
        response = session.llm.chat(session, text)
        action = response.get("action")
        session.tts.stop(session)
        if action:
            done = session.state_engine.trigger(session, action)
            if done:
                debug_ui.set(response["expressions"], session.state_engine.get_inventory())
                response_text = response["text"]
                session.llm.system(session.state_engine.get_action_system_prompt(action))
            else:
                # generate a negative answer to the last tried transition
                text = """
                Die letze Aktion hat leider nicht geklappt. Unten ist der Grund dafür. Schreibe den Benutzer 
                eine der Situation angepasste Antwort, so, dass die Gesamtstory und experience nicht kaputt geht. 
                Schreibe diese direkt raus und vermeide sowas wie 'Hier ist die Antort' oder so...
                Hier ist der Fehler den wir vom Sytem erhalten haben:
                """+session.state_engine.last_transition_error
                response = session.llm.chat(session, text)
                debug_ui.set(response["expressions"], session.state_engine.get_inventory() )

                response_text= response["text"]
        else:
            debug_ui.set(response["expressions"], session.state_engine.get_inventory())
            response_text = response["text"]

    token = session.ws_token
    if token:
        WebSocketManager.send_message(token, json.dumps({"function":"chat_response", "text":response_text}))

    WebSocketManager.send_message(token, json.dumps({"function":"speak.stop"}))
    session.tts.speak(session, response_text)
    debug_ui.set([], session.state_engine.get_inventory())

    return JSONResponse({"response": response_text})


# REST endpoint to serve audio files
@app.get("/api/audio/{filename}")
async def get_audio(filename: str, request: Request):
    if request.cookies.get("authenticated") != "yes":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    file_path = f"{CONVERSATION_DIR}{filename}"
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"
    if os.path.isfile(file_path):
        return FileResponse(path=file_path, filename=filename, media_type=mime_type)
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")


@app.get("/websocket/connect")
async def ws_connect(request: Request, response: Response):
    session = get_session(request, response)
    if not session.ws_token:
        unique_id = str(uuid4())
        session.ws_token = unique_id
    return {"token": session.ws_token}


# WebSocket handling
@app.websocket("/websocket/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await WebSocketManager.connect(websocket, token)
    try:
        while True:
            await WebSocketManager.process_queue(token)
            await asyncio.sleep(0.1)  # Small delay to prevent a tight loop, adjust as needed
    except WebSocketDisconnect:
        print("WebSocket disconnected")
        await WebSocketManager.remove(token)
        

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9000)


