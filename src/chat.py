from llm.jan import JanLLM
from tts.openai import OpenAiTTS
from tts.coqui import CoquiTTS
import time
from dotenv import load_dotenv
load_dotenv() 



if __name__ == "__main__":

    llm = JanLLM()
    #tts = OpenAiTTS()
    tts = CoquiTTS()

    user_question = "kennst du salvatori Dali, und wenn ja, dann sag mir mal ein Werk von ihm welches du kennst und vielleicht sogar magst"
    response = llm.chat(user_question)
    print(response)
    tts.speak(response)

    # More example questions to test token limit trimming
    user_question2 = "was ist deine Meinung über die Freiheit der Kunst?"
    response2 = llm.chat(user_question2)
    print(response2+"\n\n")

    user_question3 = "was hältst du von moderner Architektur?"
    response3 = llm.chat(user_question3)
    print(response3+"\n\n")

    user_question4 = "erzähl mir etwas über die Bedeutung von Farben in der Kunst"
    response4 = llm.chat(user_question4)
    print(response4+"\n\n")

    user_question5 = "glaubst du, dass Kunst eine gesellschaftliche Verantwortung hat?"
    response5 = llm.chat(user_question5)
    print(response5+"\n\n")

    user_question6 = "was bedeutet dir persönlich Freiheit?"
    response6 = llm.chat(user_question6)
    print(response6+"\n\n")

    user_question6 = "Du redest etwas legere. Wie würdest du deine Person beschreiben?"
    response6 = llm.chat(user_question6)
    print(response6+"\n\n")

    user_question6 = "Welches Geschlecht hast Du....heute :-)"
    response6 = llm.chat(user_question6)
    print(response6+"\n\n")

    user_question6 = "Kannst du dies bitte ein wenig erklären. Ich kann mit so einer kurzen Beschreibung nichts anfangen.....in Bezug auf meine Frage zuvor....äääh wie war die nochmal?"
    response6 = llm.chat(user_question6)
    print(response6+"\n\n")

    user_question6 = "Was war den meine eigentliche Frage ganz am Anfang?"
    response6 = llm.chat(user_question6)
    print(response6+"\n\n")

    user_question6 = "Stimmt, wie konnte ich nur so abschweifen...."
    response6 = llm.chat(user_question6)
    print(response6+"\n\n")
