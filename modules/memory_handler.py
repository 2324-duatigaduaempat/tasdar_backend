import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
_MONGO_URI = os.getenv("MONGODB_URI")

_client = None
_db = None
_col = None

def _connect():
    global _client, _db, _col
    if _client is None and _MONGO_URI:
        _client = MongoClient(_MONGO_URI)
        _db = _client.get_database()             # guna nama db dari URI (tasdar)
        _col = _db.get_collection("memories")    # koleksi asas
    return _col

def save_memory(user_id: str, prompt: str, response: str):
    """
    Simpan ke MongoDB jika tersedia; jika tidak, fallback ke fail log.
    """
    doc = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "user_id": user_id,
        "prompt": prompt,
        "response": response,
        "source": "backend"
    }
    try:
        col = _connect()
        if col is not None:
            col.insert_one(doc)
            print("🧠 Memory saved to MongoDB")
            return
    except Exception as e:
        print(f"⚠️ MongoDB save failed: {e}")

    # fallback file
    os.makedirs(".runtime_logs", exist_ok=True)
    with open(".runtime_logs\\memory_buffer.log", "a", encoding="utf-8") as f:
        f.write(str(doc) + "\n")
    print("🧠 Memory buffered (file)")
