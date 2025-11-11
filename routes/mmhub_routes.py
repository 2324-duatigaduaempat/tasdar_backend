# backend/routes/mmhub_routes.py
from flask import Blueprint, request, jsonify
from modules.multimodel_hub import ask

mmhub_bp = Blueprint("mmhub", __name__)

@mmhub_bp.route("/ask", methods=["POST"])
def mmhub_ask():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    mode = data.get("mode", "fusion")
    topk = int(data.get("topk", 2))
    if not prompt:
        return jsonify({"error": "prompt kosong"}), 400
    return jsonify(ask(prompt, mode=mode, topk=topk)), 200
