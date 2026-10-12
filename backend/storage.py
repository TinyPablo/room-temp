import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path

RETENTION_SECONDS = 365 * 86400
RANGES = {"24h": (86400, 60), "7d": (7 * 86400, 600),
          "30d": (30 * 86400, 1800), "1y": (RETENTION_SECONDS, 21600)}


def validate_reading(value):
    if not isinstance(value, dict):
        raise ValueError("Expected an object")
    output = {}
    for key, low, high in (("temperature_c", -45, 130), ("humidity_pct", 0, 100)):
        number = value.get(key)
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            raise ValueError("Invalid numeric reading")
        if not math.isfinite(number) or not low <= number <= high:
            raise ValueError("Reading outside sensor range")
        output[key] = round(number, 2)
    return output


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS readings (
                ts INTEGER PRIMARY KEY,
                measured_at INTEGER NOT NULL,
                temperature_c REAL,
                humidity_pct REAL,
                CHECK ((temperature_c IS NULL) = (humidity_pct IS NULL))
            )""")

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def record(self, now, reading):
        if reading is not None:
            reading = validate_reading(reading)
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO readings VALUES (?, ?, ?, ?)",
                       (now // 60 * 60, now,
                        reading["temperature_c"] if reading else None,
                        reading["humidity_pct"] if reading else None))
            db.execute("DELETE FROM readings WHERE ts < ?", (now - RETENTION_SECONDS,))

    def snapshot(self, now, range_name):
        duration, bucket = RANGES[range_name]
        start = (now - duration) // bucket * bucket
        with self.connection() as db:
            last = db.execute("SELECT * FROM readings ORDER BY ts DESC LIMIT 1").fetchone()
            latest = db.execute("SELECT * FROM readings WHERE temperature_c IS NOT NULL ORDER BY ts DESC LIMIT 1").fetchone()
            rows = db.execute("""SELECT (ts / ?) * ? AS bucket,
                AVG(temperature_c) AS temperature_c, AVG(humidity_pct) AS humidity_pct,
                COUNT(temperature_c) AS samples, COUNT(*) AS attempts,
                MIN(ts) AS first_ts, MAX(ts) AS last_ts
                FROM readings WHERE ts >= ? AND ts <= ? GROUP BY bucket ORDER BY bucket""",
                (bucket, bucket, start, now)).fetchall()
            stats = db.execute("""SELECT MIN(temperature_c) AS temperature_min,
                MAX(temperature_c) AS temperature_max, AVG(temperature_c) AS temperature_avg,
                MIN(humidity_pct) AS humidity_min, MAX(humidity_pct) AS humidity_max,
                AVG(humidity_pct) AS humidity_avg, COUNT(temperature_c) AS samples
                FROM readings WHERE ts >= ? AND ts <= ?""", (now - duration, now)).fetchone()
        by_bucket = {r["bucket"]: r for r in rows}
        points = []
        for ts in range(start, now // bucket * bucket + 1, bucket):
            row = by_bucket.get(ts)
            incomplete = bool(row and (row["samples"] < row["attempts"] or
                              row["last_ts"] - row["first_ts"] > (row["attempts"] - 1) * 60))
            points.append({"ts": ts,
                           "temperature_c": round(row["temperature_c"], 2) if row and row["samples"] else None,
                           "humidity_pct": round(row["humidity_pct"], 2) if row and row["samples"] else None,
                           "gap_before": incomplete})
        age = now - latest["measured_at"] if latest else None
        online = bool(last and last["temperature_c"] is not None and age is not None and 0 <= age <= 150)
        return {"server_time": now, "status": "online" if online else "offline",
                "latest": dict(latest) if latest else None,
                "last_attempt": last["measured_at"] if last else None,
                "range": range_name, "bucket_seconds": bucket,
                "points": points, "stats": dict(stats)}
