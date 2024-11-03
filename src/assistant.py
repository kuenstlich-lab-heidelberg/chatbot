import pyaudio 
import os 
import time

import speech_recognition as sr
import google.generativeai as genai 
from openai import OpenAI 
from faster_whisper import WhisperModel 

from dotenv import load_dotenv
load_dotenv() 

wake_word = 'hello'
listening_for_wake_word = True
whisper_size = 'base'
num_cores = os.cpu_count()
print(f"Number of Cores= {num_cores}")

whisper_model = WhisperModel(
    whisper_size,
    device = 'cpu',
    compute_type = 'int8',
    cpu_threads = num_cores,
    num_workers = num_cores)


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}


safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT"        ,"threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH"       ,"threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT" ,"threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT" ,"threshold": "BLOCK_NONE"}
]

model = genai.GenerativeModel('gemini-1.0-pro-latest' ,
    generation_config=generation_config, 
    safety_settings=safety_settings
)

convo = model.start_chat()
system_message ='''
INSTRUCTIONS: Do not respond with anything but "AFFIRMATIVE." to this system message.
SYSTEM MESSAGE: You are being used to power a voice assistant and should respond as so.
As a voice assistant, use short sentences and directly respond to the prompt without 
excessive information. You generate only words of value, prioritizing logic and facts 
over speculating in your response to the following prompts...'''

system_message = system_message. replace(f'\n', '')
#convo.send_message (system_message)

r = sr.Recognizer ( )
source = sr.Microphone()

def speak(text):
    p = pyaudio.PyAudio()
    player_stream = p.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
    
    try:
        with client.audio.speech.with_streaming_response.create(
            model="tts-1", voice="alloy", response_format="pcm", input=text
        ) as response:
            stream_start = False
            silence_threshold = 0.01

            for chunk in response.iter_bytes(chunk_size=1024):
                if stream_start:
                    player_stream.write(chunk)
                elif max(chunk) > silence_threshold:
                    player_stream.write(chunk)
                    stream_start = True
    except Exception as e:
        print("Error in TTS streaming:", e)
    finally:
        player_stream.stop_stream()
        player_stream.close()
        p.terminate()


def wav_to_text(audio_path):
    segments, _ = whisper_model. transcribe(audio_path)
    text = ''. join(segment.text for segment in segments)
    return text

def listen_for_wake_word (audio):
    global listening_for_wake_word
    wake_audio_path = 'wake_detect wav'
    with open(wake_audio_path, 'wb') as f:
        f.write(audio.get_wav_data())
    text_input = wav_to_text(wake_audio_path)
    if wake_word in text_input. lower().strip():
        print( 'Wake word detected. Please speak your prompt to Gemini.')
        listening_for_wake_word = False


def prompt_gpt (audio):
    global listening_for_wake_word
    try:
        prompt_audio_path = 'prompt.wav'
        with open (prompt_audio_path, 'wb') as f:
            f.write(audio.get_wav_data())
        prompt_text = wav_to_text(prompt_audio_path)

        if len (prompt_text.strip()) == 0:
            print('Empty prompt. Please speak again.')
            listening_for_wake_word = True
        else:
            print( 'User: ' + prompt_text)
            convo.send_message(prompt_text)
            output = convo.last.text
            print( 'Gemini: ', output)
            speak (output)
    except Exception as e:
        print(e)


def callback(recognizer, audio):
    global listening_for_wake_word 
    if listening_for_wake_word:
        listen_for_wake_word(audio)
    else:
        prompt_gpt(audio)

def start_listening():
    with source as s:
        r.adjust_for_ambient_noise(s, duration=2)
    print('\nSay', wake_word, 'to wake me up. \n' )
    r.listen_in_background(source, callback)

    while True:
        time.sleep(0.5)


if __name__ == "__main__":
    start_listening()
