from datetime import datetime, timezone
from pymongo import MongoClient
import os

_mongo_client = None

def _db():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(os.environ.get("MONGODB_URI"))
    return _mongo_client["tasdar_db"]

def save_reflection(payload: dict):
    payload = dict(payload)
    payload["ts"] = datetime.now(timezone.utc).isoformat()
    return _db()["folder_jiwa"].insert_one(payload)

def get_ethic_state():
    """
    Pulangkan keadaan Etika & Resonansi semasa.
    12 Etika Tetap (E1..E12)
    10 Resonansi (alpha..kappa)
    Nilai contoh 0..1 (atau boolean utk aktif)
    """
    sample = {
        "ethics": [
            {"code": f"E{i+1:02d}", "label": f"Etika {i+1}", "active": True if i%3!=0 else False, "value": (i+1)/12}
            for i in range(12)
        ],
        "resonance": [
            {"code": c, "value": v}
            for c, v in zip(["α","β","γ","δ","ε","ζ","η","θ","ι","κ"], [0.72,0.35,0.88,0.41,0.63,0.53,0.44,0.77,0.58,0.66])
        ],
    }
    return sample
