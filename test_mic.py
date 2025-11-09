import speech_recognition as sr

print("MIC TEST STARTED")
print("Say 'HELLO JARVIS' now...")

r = sr.Recognizer()
with sr.Microphone() as source:
    r.adjust_for_ambient_noise(source, duration=0.5)
    audio = r.listen(source, timeout=10, phrase_time_limit=5)

try:
    text = r.recognize_google(audio)
    print(f"HEARD: {text}")
    if "jarvis" in text.lower():
        print("WAKE WORD DETECTED!")
    else:
        print("No wake word — but mic works!")
except Exception as e:
    print(f"MIC ERROR: {e}")
