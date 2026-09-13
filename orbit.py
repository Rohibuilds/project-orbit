#!/usr/bin/env python3
import json
import os
import threading
import time
import webbrowser
from pathlib import Path

import cv2
from flask import Flask, Response, jsonify, render_template_string, request

from modules.speech import SpeechEngine
from modules.vision import VisionSystem
from modules.projects import ProjectManager
from modules.ai import AIEngine

BASE = Path(__file__).resolve().parent
CONFIG = json.loads((BASE / "config.json").read_text())
os.chdir(BASE)

headless = os.environ.get("ORBIT_HEADLESS") == "1"
speech = SpeechEngine(enabled=not headless)
projects = ProjectManager(os.environ.get("ORBIT_PROJECTS_DIR") or CONFIG.get("projects_dir", "projects"))
vision = VisionSystem(
    CONFIG.get("camera_index", 0),
    CONFIG.get("camera_width", 1280),
    CONFIG.get("camera_height", 720),
    CONFIG.get("recordings_fps", 20),
    disabled=headless,
)
ai = AIEngine(CONFIG.get("ai_backend", "ollama"), CONFIG.get("ollama_model", "qwen2.5:0.5b"))

state = {
    "running": True,
    "last_command": "",
    "last_response": "",
    "last_detection": {},
    "recording": False,
    "project": None,
}
last_frame = None
frame_lock = threading.Lock()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8192
command_lock = threading.RLock()

HTML = r'''
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ORBIT Console</title>
<style>
body{margin:0;background:#080c12;color:#eaf4ff;font-family:Arial,sans-serif}header{padding:14px 20px;background:#0e1622;border-bottom:1px solid #26384d;display:flex;justify-content:space-between}.brand{font-weight:800;letter-spacing:4px}.online{color:#8ef0b3}.grid{display:grid;grid-template-columns:2fr 1fr;gap:12px;padding:12px}.card{background:#101923;border:1px solid #26384d;border-radius:14px;padding:12px}.camera{width:100%;border-radius:10px}.title{font-size:12px;letter-spacing:2px;color:#8ba8c5;margin-bottom:8px}button{background:#17324b;color:white;border:1px solid #315b80;padding:10px 12px;border-radius:8px;margin:3px;cursor:pointer}input{width:70%;padding:10px;border-radius:8px;border:1px solid #315b80;background:#09131d;color:white}.big{font-size:22px;font-weight:700}.muted{color:#90a2b4}.event{padding:6px 0;border-bottom:1px solid #1e2b38}
@media(max-width:720px){.grid{grid-template-columns:1fr}input{width:60%}}</style></head><body>
<header><div class="brand">ORBIT</div><div class="online">● SYSTEM ONLINE</div></header>
<div class="grid"><div class="card"><div class="title">LIVE DESK</div><img class="camera" src="/video"></div>
<div><div class="card"><div class="title">CURRENT PROJECT</div><div id="project" class="big">None</div><div class="muted" id="recording">Recording: off</div></div>
<div class="card"><div class="title">VISION</div><div id="detection">No detection yet</div><button onclick="cmd('identify resistor')">Identify resistor</button><button onclick="cmd('take photo')">Take photo</button></div>
<div class="card"><div class="title">VOICE / COMMAND</div><input id="text" placeholder="Type a command or AI question"><button onclick="send()">Send</button><div class="event"><b>You:</b> <span id="lastcmd"></span></div><div class="event"><b>ORBIT:</b> <span id="lastresp"></span></div></div>
<div class="card"><div class="title">CAPTURE</div><button onclick="cmd('start recording')">Start recording</button><button onclick="cmd('stop recording')">Stop recording</button><button onclick="cmd('end project')">End project</button></div></div></div>
<script>
async function cmd(t){await fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});update()}
async function send(){let t=document.getElementById('text').value;if(t){await cmd(t);document.getElementById('text').value=''}}
async function update(){let s=await (await fetch('/state')).json();const el=id=>document.getElementById(id);el('project').textContent=s.project||'None';el('recording').textContent='Recording: '+(s.recording?'ON':'off');el('lastcmd').textContent=s.last_command||'';el('lastresp').textContent=s.last_response||'';let d=s.last_detection||{};el('detection').textContent=d.ok?(d.value_ohms+' ohm, ±'+d.tolerance_percent+'%, bands: '+d.bands.join(', ')):(d.reason||'No detection yet')}
setInterval(update,1000);update();
</script></body></html>
'''


def say(text):
    state["last_response"] = text
    speech.speak(text)


def current_frame():
    with frame_lock:
        return None if last_frame is None else last_frame.copy()


def handle_command(text: str):
    with command_lock:
        return _handle_command(text)

def _handle_command(text: str):
    text = (text or "").strip()
    if not text:
        return "I didn't hear a command."
    low = text.lower()
    state["last_command"] = text

    if low.startswith("start project"):
        vision.stop_recording()
        state["recording"] = False
        name = text[len("start project"):].strip() or "New Project"
        folder = projects.start(name)
        state["project"] = folder.name
        return f"Project {name} started. I am ready."

    if low == "end project" or low.startswith("finish project"):
        vision.stop_recording()
        state["recording"] = False
        ended = projects.end()
        state["project"] = None
        return "Project session saved." if ended else "No project is currently active."

    if "take photo" in low or "capture photo" in low:
        frame = current_frame()
        folder = projects.ensure()
        state["project"] = folder.name
        path = vision.snapshot(folder / "photos", frame)
        if path:
            projects.log(f"Captured photo: {path.name}", "capture")
            return "Photo captured and saved to the project."
        return "Camera capture failed."

    if "start recording" in low:
        frame = current_frame()
        if frame is None:
            return "Camera is not ready."
        h, w = frame.shape[:2]
        folder = projects.ensure()
        state["project"] = folder.name
        path = vision.start_recording(folder / "videos", (w, h))
        if path is None:
            return "Video encoder could not start. Check the MP4 codec and output folder."
        state["recording"] = True
        projects.log(f"Video recording started: {Path(path).name}", "capture")
        return "Recording started."

    if "stop recording" in low:
        path = vision.stop_recording()
        state["recording"] = False
        if path:
            projects.log(f"Video recording stopped: {Path(path).name}", "capture")
            return "Recording stopped and saved."
        return "Recording was not active."

    if "identify resistor" in low or "resistor value" in low:
        frame = current_frame()
        if frame is None:
            return "Camera is not ready."
        result = vision.resistor(frame)
        state["last_detection"] = {k:v for k,v in result.items() if k != "annotated"}
        if result.get("annotated") is not None:
            folder = projects.ensure()
            state["project"] = folder.name
            out = folder / "photos" / f"resistor_{int(time.time())}.jpg"
            cv2.imwrite(str(out), result["annotated"])
        if result.get("ok"):
            value = result["value_ohms"]
            tol = result["tolerance_percent"]
            bands = ", ".join(result["bands"])
            projects.log(f"Resistor detected: {value} ohm +/-{tol}% ({bands})", "vision")
            return f"I detected approximately {value:g} ohms with {tol:g} percent tolerance. Please verify before using it in a critical circuit."
        return result.get("reason", "I could not identify the resistor.")

    if low.startswith("remember "):
        note = text[9:].strip()
        projects.log(note, "memory")
        state["project"] = projects.ensure().name
        return "I saved that to the current project memory."

    # Anything else is treated as an AI-assistant question.
    context = "You are ORBIT, a concise electronics workbench assistant. Prioritize electrical safety and practical debugging.\nUser: " + text
    answer = ai.ask(context)
    projects.log(f"Q: {text}\nA: {answer}", "assistant")
    state["project"] = projects.ensure().name
    return answer


def camera_loop():
    global last_frame
    while state["running"]:
        frame_start = time.monotonic()
        ok, frame = vision.read()
        if not ok:
            time.sleep(0.25)
            continue
        # Inspection guide box for resistor mode.
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (int(w*.2), int(h*.35)), (int(w*.8), int(h*.65)), (220,220,220), 1)
        cv2.putText(frame, "Place resistor horizontally inside box", (int(w*.2), int(h*.33)), cv2.FONT_HERSHEY_SIMPLEX, .6, (230,230,230), 1)
        with frame_lock:
            last_frame = frame
        time.sleep(max(0, 1/vision.fps - (time.monotonic()-frame_start)))


def voice_loop():
    wake_phrases = [p.lower() for p in CONFIG.get("wake_phrases", ["orbit"])]
    while state["running"]:
        heard = speech.listen_once(CONFIG.get("listen_timeout",5), CONFIG.get("phrase_time_limit",8))
        if not heard:
            time.sleep(0.1)
            continue
        if any(p in heard.lower() for p in wake_phrases):
            command = heard
            for p in wake_phrases:
                index = command.lower().find(p)
                if index >= 0:
                    command = (command[:index] + command[index+len(p):]).strip(" ,")
                if command != heard:
                    break
            if not command:
                say("Yes?")
                command = speech.listen_once(CONFIG.get("listen_timeout",5), CONFIG.get("phrase_time_limit",8)) or ""
            response = handle_command(command)
            say(response)


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/state")
def get_state():
    with command_lock:
        return jsonify(state)


@app.route("/command", methods=["POST"])
def command_api():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("text"), str):
        return jsonify({"ok": False, "error": "text must be a string"}), 400
    text = data["text"].strip()
    if not text or len(text) > 2000:
        return jsonify({"ok": False, "error": "text must contain 1-2000 characters"}), 400
    response = handle_command(text)
    say(response)
    return jsonify({"ok": True, "response": response})


@app.route("/video")
def video():
    if not vision.ok():
        return jsonify({"ok": False, "error": "Camera unavailable"}), 503
    def generate():
        while state["running"]:
            frame = current_frame()
            if frame is None:
                time.sleep(.1); continue
            ok, jpg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if ok:
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg.tobytes() + b'\r\n'
            time.sleep(.05)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


def run_web():
    app.run(host=CONFIG.get("web_host", "127.0.0.1"), port=int(CONFIG.get("web_port", 8080)), threaded=True, use_reloader=False)


if __name__ == "__main__":
    if not vision.ok():
        print("WARNING: Camera could not be opened. Check camera_index in config.json.")
    threading.Thread(target=camera_loop, daemon=True).start()
    threading.Thread(target=run_web, daemon=True).start()
    time.sleep(1.0)
    webbrowser.open("http://127.0.0.1:8080")
    say(f"Welcome back, {CONFIG.get('user_name','Rohi')}. ORBIT systems online. What shall we build today?")
    threading.Thread(target=voice_loop, daemon=True).start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        state["running"] = False
        with command_lock:
            vision.close()
            projects.end()
