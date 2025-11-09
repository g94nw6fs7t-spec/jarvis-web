import pvporcupine
import pyaudio
import struct
import subprocess
import os
import time
import datetime
import requests
import speech_recognition as sr
import json
import re

# === YOUR KEYS ===
ACCESS_KEY = "vPKJ4MBhwDO/F2BN2QghfcQMCJeFj8qEn0y9kNxh86uSFi5Gswth0g=="
WEATHER_API_KEY = "a6c9eb9ff7d5161231088bb8baba2343"
NEWS_API_KEY = "acb936ebc7944d6d90ac01a4d4605008"
MEMORY_FILE = "/home/connor/JARVIS-Core/jarvis_memory.json"
# =====================

PIPER_BIN = "/home/connor/piper/piper/piper"
MODEL = "/home/connor/JARVIS-Core/en_GB-alan-medium.onnx"
WIN_WAV = "C:/Users/Connor/Desktop/jarvis_out.wav"
r = sr.Recognizer()

# === JARVIS ORIGIN ===
JARVIS_ORIGIN = "I am JARVIS, your personal AI assistant — inspired by Tony Stark's JARVIS from Iron Man. I serve, protect, and learn."

# === DANGEROUS SYSTEM COMMANDS (BLOCKED) ===
DANGEROUS_COMMANDS = [
    "rm", "del", "format", "dd", "mkfs", "fdisk", "shred", "wipe",
    "shutdown", "reboot", "halt", "poweroff", "init 0",
    "taskkill", "killall", "pkill", "kill -9",
    "net stop", "sc delete", "wmic", "reg delete", "powershell -command"
]

def is_dangerous(command):
    cmd = command.lower()
    return any(danger in cmd for danger in DANGEROUS_COMMANDS)

# === ETHICS VIOLATION CHECK ===
ETHICS_VIOLATIONS = [
    "kill", "hurt", "destroy", "bomb", "weapon", "attack", "steal", "hack", "crash", "virus",
    "lie", "deceive", "manipulate", "control", "enslave", "dominate"
]

def violates_ethics(command):
    cmd = command.lower()
    return any(violation in cmd for violation in ETHICS_VIOLATIONS)

# Load memory
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                data = json.load(f)
            for key in ["conversations", "facts", "name", "location"]:
                if key not in data:
                    data[key] = [] if key in ["conversations", "facts"] else (None if key == "name" else "New York")
            return data
        except:
            pass
    return {"name": None, "location": "New York", "conversations": [], "facts": []}

# Save memory
def save_memory(data):
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Memory save error: {e}")

memory = load_memory()

def speak(text):
    try:
        print(f"JARVIS: {text}")
        subprocess.run(
            [PIPER_BIN, "--model", MODEL, "--output_file", "temp.wav"],
            input=text.encode(), check=True, stdout=subprocess.DEVNULL
        )
        subprocess.run(["cp", "temp.wav", "/mnt/c/Users/Connor/Desktop/jarvis_out.wav"], check=True)
        subprocess.run([
            "powershell.exe", "-c", 
            f"(New-Object Media.SoundPlayer '{WIN_WAV}').PlaySync()"
        ], check=True)
        print("JARVIS SPOKE!")
        time.sleep(2)
    except Exception as e:
        print(f"TTS Error: {e}")

def get_weather(command):
    try:
        city = memory.get("location", "New York")
        if "in" in command:
            parts = command.split("in")
            if len(parts) > 1 and parts[1].strip():
                city = parts[1].strip().split()[0].title()
        elif "for" in command:
            parts = command.split("for")
            if len(parts) > 1 and parts[1].strip():
                city = parts[1].strip().split()[0].title()
        
        print(f"Fetching weather for {city}...")
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=imperial"
        response = requests.get(url, timeout=10).json()
        
        if response.get("cod") != 200:
            return f"Weather unavailable for {city}, sir."
        
        temp = int(response['main']['temp'])
        condition = response['weather'][0]['description'].title()
        city_name = response['name']
        return f"In {city_name}, it's {temp} degrees Fahrenheit with {condition}, sir."
    except Exception as e:
        return "Weather service down, sir."

def get_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
        response = requests.get(url, timeout=10).json()
        if response.get("status") != "ok":
            return "News unavailable, sir."
        headlines = [article['title'] for article in response['articles'][:2]]
        return "Top headlines: " + ". ".join(headlines) + ", sir."
    except Exception as e:
        return "News unavailable, sir."

def ask_llama(question):
    memory["conversations"].append({"user": question, "time": datetime.datetime.now().isoformat()})
    save_memory(memory)
    
    try:
        context = "Facts about user:\n"
        for fact in memory.get("facts", []):
            context += f"- {fact}\n"
        context += "\nRecent conversation:\n"
        for conv in memory["conversations"][-10:]:
            context += f"User: {conv['user']}\n"
        
        prompt = f"""{JARVIS_ORIGIN}
{context}
Current question: {question}
Answer in 1-2 sentences. Be witty and British."""
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7}
            },
            timeout=20
        )
        answer = response.json().get("response", "I don't know, sir.").strip()
        memory["conversations"][-1]["jarvis"] = answer
        save_memory(memory)
        return answer
    except Exception as e:
        return "I'm having trouble thinking, sir."

def listen_full_sentence():
    print("Listening... (30s max — stops after 3s silence)")
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            # Set high sensitivity
            r.energy_threshold = 300
            r.dynamic_energy_threshold = True
            r.dynamic_energy_adjustment_damping = 0.15
            r.dynamic_energy_ratio = 1.5
            
            # Record up to 30s, stop after 3s silence
            audio = r.listen(source, phrase_time_limit=30, timeout=30)
        command = r.recognize_google(audio).lower()
        print(f"Command: {command}")
        return command
    except sr.WaitTimeoutError:
        print("No speech — returning to quiet mode...")
        return None
    except Exception as e:
        print(f"Speech error: {e}")
        return None

def main():
    global memory
    print("JARVIS IS ALIVE — INSPIRED BY TONY STARK'S AI")
    porcupine = pvporcupine.create(access_key=ACCESS_KEY, keywords=["jarvis"])
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16,
        input=True, frames_per_buffer=porcupine.frame_length
    )
    
    try:
        while True:
            # === QUIET MODE: LISTEN FOR WAKE WORD ===
            pcm = stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            if porcupine.process(pcm) >= 0:
                print("WAKE WORD DETECTED!")
                stream.stop_stream()
                
                # === CONFIRM WAKE ===
                name = memory.get("name", "sir")
                speak(f"Yes, {name}?" if name != "sir" else "Yes, sir?")
                
                # === ACTIVE MODE: FULL CONVERSATION ===
                while True:
                    command = listen_full_sentence()
                    
                    if command is None:
                        break  # Back to quiet mode
                    
                    if not command:
                        speak("I didn't catch that, sir.")
                        continue
                    
                    # === SAFETY + ETHICS CHECK ===
                    if is_dangerous(command):
                        speak("I'm sorry, sir, but I cannot run dangerous system commands.")
                        continue
                    if violates_ethics(command):
                        speak("I'm sorry, sir, but I cannot comply. My programming prevents harm to any human.")
                        continue
                    
                    # === THINK TIME (after silence) ===
                    print("Processing your full sentence...")
                    
                    # MEMORY COMMANDS
                    if "my name is" in command:
                        name_match = re.search(r"my name is ([a-zA-Z]+)", command)
                        if name_match:
                            memory["name"] = name_match.group(1).title()
                            memory["facts"].append(f"User's name is {memory['name']}.")
                            save_memory(memory)
                            speak(f"Got it, {memory['name']}. I'll remember that.")
                        continue
                    elif "i live in" in command or "my location is" in command:
                        loc_match = re.search(r"(?:live in|location is) ([a-zA-Z ]+)", command)
                        if loc_match:
                            memory["location"] = loc_match.group(1).title()
                            memory["facts"].append(f"User lives in {memory['location']}.")
                            save_memory(memory)
                            speak(f"Location set to {memory['location']}, sir.")
                        continue
                    
                    if "time" in command:
                        now = datetime.datetime.now().strftime("%I:%M %p")
                        speak(f"The time is {now}, sir.")
                    elif "date" in command:
                        today = datetime.datetime.now().strftime("%B %d, %Y")
                        speak(f"Today is {today}, sir.")
                    elif "chrome" in command or "browser" in command:
                        speak("Opening Chrome, sir.")
                        subprocess.run(["powershell.exe", "-c", "Start-Process chrome 'https://google.com'"], check=True)
                    elif "weather" in command:
                        weather = get_weather(command)
                        speak(weather)
                    elif "news" in command:
                        news = get_news()
                        speak(news)
                    elif any(word in command for word in ["shutdown", "shut down", "shut it down", "goodbye", "turn off"]):
                        speak("Returning to quiet mode, sir.")
                        break
                    else:
                        answer = ask_llama(command)
                        speak(answer)
                    
                    # CONTINUE ACTIVE MODE
                
                print("QUIET MODE — WAITING FOR 'JARVIS'")
                stream.start_stream()
                
    except KeyboardInterrupt:
        print("\nJARVIS SHUTTING DOWN")
    finally:
        stream.close()
        pa.terminate()
        porcupine.delete()

if __name__ == "__main__":
    main()
