import serial
import speech_recognition as sr
import time
import ollama
import os
import pygame
from gtts import gTTS

# 🔌 Arduino
arduino = serial.Serial('COM5', 9600)
time.sleep(2)

# 🎤 Mic
recognizer = sr.Recognizer()

# 🔊 Audio
pygame.mixer.init()

listening = False
is_speaking = False
interrupt_flag = False
stop_listening = None

# 🧠 MEMORY (STRICT SHORT RESPONSES)
chat_history = [
    {'role': 'system', 'content':
     'You are ZYN, a smart, confident, slightly witty male AI assistant. '
     'Always respond in 1 to 2 short sentences only. '
     'Be clear, direct, and conversational. Do NOT give long explanations.'}
]

print("ZYN is ready... Press button")

# 🔊 SPEAK FUNCTION
def speak(text):
    global is_speaking, interrupt_flag

    print("ZYN:", text)

    try:
        is_speaking = True
        interrupt_flag = False

        text = text.replace(",", "").replace("...", "").strip()
        filename = "voice.mp3"

        tts = gTTS(text=text, lang='en')
        tts.save(filename)

        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            if interrupt_flag:
                pygame.mixer.music.stop()
                break
            time.sleep(0.05)

        pygame.mixer.music.unload()
        os.remove(filename)

    except Exception as e:
        print("TTS Error:", e)

    is_speaking = False

# 🧠 AI FUNCTION (SHORT + FAST)
def ask_ai(prompt):
    global chat_history

    chat_history.append({'role': 'user', 'content': prompt})

    if len(chat_history) > 12:
        chat_history.pop(1)

    response = ollama.chat(
        model='llama3',
        messages=chat_history,
        options={
            "num_predict": 60,   # 🔥 limit response length
            "temperature": 0.7
        }
    )

    reply = response['message']['content'].strip()

    # 🔥 HARD LIMIT TO 2 SENTENCES
    reply = '. '.join(reply.split('. ')[:2])

    chat_history.append({'role': 'assistant', 'content': reply})

    return reply

# 🎤 BACKGROUND LISTENING
def callback(recognizer, audio):
    global interrupt_flag, listening

    if not listening:
        return

    try:
        text = recognizer.recognize_google(audio).lower()
        print("You:", text)

        # 🔥 interrupt speaking instantly
        interrupt_flag = True

        # 🛑 stop command
        if any(word in text for word in ["bye", "goodbye", "see you"]):
            speak("Goodbye")
            listening = False
            return


        reply = ask_ai(text)

        # 🔥 chunked speech
        chunks = reply.split('. ')

        for chunk in chunks:
            if chunk.strip():
                speak(chunk)

    except:
        pass

# 🔁 MAIN LOOP
while True:

    # 🔘 Button toggle
    if arduino.in_waiting:
        data = arduino.readline().decode().strip()

        if data == "START":
            listening = not listening

            if listening:
                print("🎤 Listening ON...")
                speak("I am listening")

                stop_listening = recognizer.listen_in_background(
                    sr.Microphone(),
                    callback,
                    phrase_time_limit=4
                )

            else:
                print("🛑 Listening OFF...")
                speak("Goodbye")

                if stop_listening:
                    stop_listening(wait_for_stop=False)