"""Run an isolated local preview with synthetic data, never the production database."""
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import uvicorn
from backend.app import create_app
from backend.storage import Store

path = Path("artifacts/preview.db")
store = Store(path)
now = int(time.time()) // 60 * 60
with store.connection() as db:
    db.execute("DELETE FROM readings")
    rows = []
    for i in range(1440):
        ts = now - (1439 - i) * 60
        temp = round(22.4 + 0.9 * math.sin(i / 220) + 0.14 * math.cos(i / 48), 2)
        humid = round(46 + 3.2 * math.cos(i / 250) + 0.8 * math.sin(i / 61), 2)
        if 610 <= i <= 650:
            temp = humid = None
        rows.append((ts, ts, temp, humid))
    db.executemany("INSERT INTO readings VALUES (?, ?, ?, ?)", rows)
print("Synthetic preview only: http://127.0.0.1:8765")
uvicorn.run(create_app(db_path=path, collect=False), host="127.0.0.1", port=8765)
