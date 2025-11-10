from flask import Flask, render_template_string, request, jsonify
import os
import datetime
import requests

app = Flask(__name__)

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
                const utter = new SpeechSynthesisUtterance(d.answer);
                utter.lang = 'en-GB';
                utter.rate = 0.9;
                window.speechSynthesis.speak(utter);
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
    
    return jsonify({"answer": answer})

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
