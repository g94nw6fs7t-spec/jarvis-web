import pvporcupine
import pyaudio
import struct
import subprocess
import os
import time

# === YOUR PICOVOICE KEY ===
ACCESS_KEY = "vPKJ4MBhwDO/F2BN2QghfcQMCJeFj8qEn0y9kNxh86uSFi5Gswth0g=="
# ==========================

PIPER_BIN = "/home/connor/piper/piper/piper"
MODEL = "/home/connor/JARVIS-Core/en_GB-alan-medium.onnx"
WIN_WAV = "C:/Users/Connor/Desktop/jarvis_out.wav"

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
        time.sleep(3)  # Wait for speech to finish
    except Exception as e:
        print(f"TTS Error: {e}")

def main():
    print("JARVIS OFFLINE MODE — SAY 'JARVIS'")
    porcupine = pvporcupine.create(access_key=ACCESS_KEY, keywords=["jarvis"])
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16,
        input=True, frames_per_buffer=porcupine.frame_length
    )
    
    try:
        while True:
            pcm = stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            if porcupine.process(pcm) >= 0:
                print("WAKE WORD DETECTED!")
                stream.stop_stream()  # MUTE MIC
                speak("Yes, sir. JARVIS at your service.")
                stream.start_stream()  # UNMUTE
    except KeyboardInterrupt:
        print("\nJARVIS OFFLINE — SHUTTING DOWN")
    finally:
        stream.close()
        pa.terminate()
        porcupine.delete()

if __name__ == "__main__":
    main()
