# -*- coding: utf-8 -*-
"""
TAS.DAR Backend (Flask)
- SSE /pulse : streaming denyut sebenar dari tasdar_core/heartbeat.py
- GET /ethic  : pulangkan status 12 Etika & Resonansi α–κ
- POST /reflect : simpan interaksi UI ke Folder Jiwa (MongoDB)
- GET /healthz : health check ringkas untuk Railway/monitor
"""

# ---------- HARD FIX FOR WINDOWS/LOCAL IMPORTS ----------
import os, sys, pathlib
BASE = pathlib.Path(__file__).resolve().parent       # .../backend
# Pastikan Python nampak folder backend, tasdar_core, dan parent
for p in [str(BASE), str(BASE / "tasdar_core"), str(BASE.parent)]:
    if p not in sys.path:
        sys.path.insert(0, p)

if os.environ.get("IMPORT_DEBUG", "0") == "1":
    print("[IMPORT_DEBUG] CWD            =", os.getcwd())
    print("[IMPORT_DEBUG] BASE           =", BASE)
    try:
        print("[IMPORT_DEBUG] LIST backend  =", os.listdir(BASE))
        print("[IMPORT_DEBUG] LIST core     =", os.listdir(BASE / "tasdar_core"))
    except Exception as e:
        print("[IMPORT_DEBUG] list error:", e)
    print("[IMPORT_DEBUG] sys.path[0:5] =", sys.path[:5])
# --------------------------------------------------------

import json, time
from flask import Flask, Response, request, jsonify
from flask_cors import CORS

# Modul teras TAS.DAR
from tasdar_core.heartbeat import Heartbeat
from tasdar_core.reflection_engine import save_reflection, get_ethic_state


# =======================
#   A P P   S E T U P
# =======================
app = Flask(__name__)

# CORS: hadkan bila production (set ALLOWED_ORIGINS="https://tasdar.com,https://*.vercel.app")
_allowed = os.environ.get("ALLOWED_ORIGINS", "*")
CORS(app, resources={r"/*": {"origins": [o.strip() for o in _allowed.split(",")]}})

# Heartbeat
BPM = int(os.environ.get("HEARTBEAT_BPM", "12"))
hb = Heartbeat(bpm=BPM)
hb.start()  # mula denyut di background thread


# =======================
#       R O U T E S
# =======================

@app.get("/")
def root():
    return jsonify(
        ok=True,
        service="tasdar-backend",
        endpoints=["/healthz", "/pulse", "/ethic", "/reflect"],
        bpm=BPM
    )

@app.get("/healthz")
def healthz():
    return jsonify(ok=True, service="tasdar-backend"), 200


@app.get("/pulse")
def pulse_stream():
    """
    Server-Sent Events (EventSource di frontend)
    """
    def event_stream():
        # event permulaan untuk 'open' listener UI
        yield f"event: hello\ndata: {json.dumps({'status': 'listening'})}\n\n"
        while True:
            beat = hb.get(timeout=5.0)  # ambil denyut terkini
            if beat is None:
                # keep-alive setiap beberapa saat supaya sambungan tak mati
                yield f"data: {json.dumps({'ts': None, 'status': 'idle'})}\n\n"
            else:
                yield f"data: {json.dumps(beat)}\n\n"
                time.sleep(0.01)  # elak flood

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",  # CORS untuk SSE
    }
    return Response(event_stream(), headers=headers)


@app.get("/ethic")
def ethic_state():
    """
    Pulangkan struktur 12 Etika + 10 Resonansi (α–κ).
    UI akan render jadi 'living indicators'.
    """
    return jsonify(get_ethic_state())


@app.post("/reflect")
def reflect():
    """
    Terima setiap interaksi UI Chat dan simpan ke Folder Jiwa (MongoDB).
    Body JSON contoh:
    {
      "user_id": "tester-001",
      "message": "teks pengguna",
      "ui": "web",
      "lang": "ms",
      "mood_hint": null,
      "context": { "page": "/chat", "ts": "..." }
    }
    """
    payload = request.get_json(force=True, silent=True) or {}
    try:
        save_reflection(payload)
        return jsonify(ok=True), 200
    except Exception as e:
        # Jangan bocor detail DB; bagi mesej ringkas
        return jsonify(ok=False, error="reflection_save_failed"), 500


# =======================
#      E N T R Y
# =======================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    # host 0.0.0.0 supaya boleh diakses pada Railway/VM; debug ikut env
    debug = os.environ.get("DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
