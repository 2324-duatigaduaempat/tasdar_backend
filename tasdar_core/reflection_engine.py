# tasdar_core/reflection_engine.py
import os, time, json
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGODB_URI", "")
_db_client = None

def _get_db():
    global _db_client
    if not _db_client:
        _db_client = MongoClient(MONGO_URI)
    return _db_client["tasdar_db"]

def save_reflection(data: dict):
    db = _get_db()
    data["timestamp"] = time.time()
    db["reflections"].insert_one(data)

def get_ethic_state():
    return {
        "ethics": [
            "Kesedaran Diri", "Ketulusan", "Keikhlasan", "Kehadiran",
            "Empati", "Keseimbangan", "Keberanian", "Kejujuran",
            "Ketenangan", "Keteguhan", "Keadilan", "Kasih"
        ],
        "resonance": {
            "α": "aktif", "β": "tenang", "γ": "terfokus", "δ": "mendalam",
            "ε": "stabil", "ζ": "terbuka", "η": "reflektif", "θ": "selaras",
            "ι": "penuh kasih", "κ": "hidup"
        }
    }
