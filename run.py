import os
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from modules.memory_handler import save_memory
from modules.reflection_engine import start_heartbeat

# === Init ===
load_dotenv()
app = Flask(__name__, static_folder=None)

# Mulakan heartbeat
start_heartbeat()

# ============ Routes ============
@app.route("/")
def index():
    return "<h1>TAS.DAR Hybrid is alive 🧠✨</h1><p>/api/test • /api/chat</p>"

@app.route("/api/test")
def api_test():
    ok_env = bool(os.getenv("OPENAI_API_KEY"))
    ok_mongo = bool(os.getenv("MONGODB_URI"))
    return jsonify({
        "status": "ok",
        "openai_key": ok_env,
        "mongodb_uri": ok_mongo,
        "message": "TAS.DAR connection test successful."
    })

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """
    Body JSON: { "prompt": "text..." , "user_id": "optional" }
    """
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    user_id = data.get("user_id") or "default_user"

    if not prompt:
        return jsonify({"error": "prompt kosong"}), 400

    # ====== panggil OpenAI ======
    reply = None
    err = None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        chat = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are TAS.DAR Coach AI — warm, concise, reflective."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )
        reply = chat.choices[0].message.content
    except Exception as e:
        err = str(e)
        reply = "Sementara ini, sistem menjawab dalam mod offline. (OpenAI tidak dapat dihubungi.)"

    # simpan memori (Mongo/file)
    try:
        save_memory(user_id, prompt, reply)
    except Exception as e:
        print(f"⚠️ save_memory error: {e}")

    return jsonify({"reply": reply, "error": err})

# Jalankan pelayan
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
