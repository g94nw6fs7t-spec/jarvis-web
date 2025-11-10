from flask import Flask, render_template_string, request, jsonify
import subprocess
import os
import datetime
import requests
import base64

app = Flask(__name__)
JARVIS_DIR = "/home/connor/JARVIS-Core"
PIPER_BIN = f"{JARVIS_DIR}/../piper/piper/piper"
MODEL = f"{JARVIS_DIR}/en_GB-alan-medium.onnx"

def speak(text):
    try:
        subprocess.run(
            [PIPER_BIN, "--model", MODEL, "--output_file", f"{JARVIS_DIR}/temp.wav"],
            input=text.encode(), check=True, stdout=subprocess.DEVNULL
        )
        with open(f"{JARVIS_DIR}/temp.wav", "rb") as f:
            audio = base64.b64encode(f.read()).decode()
        return audio
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

def ask_llama(question):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:1b",
                "prompt": f"You are JARVIS, a witty British AI. Answer: {question}",
                "stream": False,
                "options": {"temperature": 0.7}
            },
            timeout=10
        )
        return response.json().get("response", "I don't know, sir.").strip()
    except:
        return "I'm having trouble thinking, sir."

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>JARVIS</title>
    <style>
        body { font-family: 'Courier New'; background: #000; color: #0f0; text-align: center; padding: 20px; }
        h1 { color: #0f0; text-shadow: 0 0 5px #0f0; }
        button { background: #0f0; color: #000; border: none; padding: 20px; font-size: 24px; border-radius: 50%; width: 80px; height: 80px; cursor: pointer; }
        #output { margin: 20px; font-size: 18px; line-height: 1.6; }
    </style>
</head>
<body>
    <h1>JARVIS</h1>
    <p>Tap mic to talk</p>
    <button onclick="start()">MIC</button>
    <div id="output">Ready.</div>

    <script>
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = false;
        recognition.lang = 'en-US';

        function start() {
            recognition.start();
            document.getElementById('output').innerHTML = 'Listening...';
        }

        recognition.onresult = function(e) {
            const text = e.results[0][0].transcript;
            document.getElementById('output').innerHTML = `You: ${text}<br>Thinking...`;
            
            fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({q: text})
            })
            .then(r => r.json())
            .then(d => {
                document.getElementById('output').innerHTML += `<br><strong>JARVIS:</strong> ${d.answer}`;
                if (d.audio) {
                    const audio = new Audio('data:audio/wav;base64,' + d.audio);
                    audio.play();
                }
            });
        };
    </script>
</body>
</html>
''')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('q', '').lower()
    
    if 'time' in question:
        answer = f"The time is {datetime.datetime.now().strftime('%I:%M %p')}, sir."
    elif 'date' in question:
        answer = f"Today is {datetime.datetime.now().strftime('%B %d, %Y')}, sir."
    else:
        answer = ask_llama(question)
    
    audio = speak(answer)
    
    return jsonify({
        "answer": answer,
        "audio": audio
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
