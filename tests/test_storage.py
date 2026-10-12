import tempfile
import unittest
from pathlib import Path

from backend.storage import RETENTION_SECONDS, Store, validate_reading


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "room.db"
        self.store = Store(self.path)
        self.now = 1_800_000_000
        self.reading = {"temperature_c": 22.5, "humidity_pct": 43.2}

    def test_outage_and_resume_preserve_gaps_and_last_good_value(self):
        self.store.record(self.now - 180, self.reading)
        self.store.record(self.now - 120, None)
        snapshot = self.store.snapshot(self.now, "24h")
        self.assertEqual(snapshot["status"], "offline")
        self.assertEqual(snapshot["latest"]["temperature_c"], 22.5)
        self.store.record(self.now, self.reading)
        snapshot = self.store.snapshot(self.now, "24h")
        last = snapshot["points"][-4:]
        self.assertEqual([p["temperature_c"] for p in last], [22.5, None, None, 22.5])
        self.assertEqual(snapshot["status"], "online")

    def test_stale_success_is_offline(self):
        self.store.record(self.now - 180, self.reading)
        self.assertEqual(self.store.snapshot(self.now, "24h")["status"], "offline")

    def test_retention_and_restart(self):
        self.store.record(self.now - RETENTION_SECONDS - 60, self.reading)
        self.store.record(self.now - 600, self.reading)
        self.store.record(self.now, self.reading)
        reopened = Store(self.path)
        with reopened.connection() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM readings").fetchone()[0], 2)

    def test_invalid_values_do_not_enter_database(self):
        for value in (True, float("nan"), float("inf"), "22", None, 150):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_reading({"temperature_c": value, "humidity_pct": 50})
        with self.assertRaises(ValueError):
            validate_reading({"temperature_c": 20, "humidity_pct": 101})

    def test_year_response_is_bounded_and_does_not_bridge_outage(self):
        self.store.record(self.now - 180, self.reading)
        self.store.record(self.now - 120, None)
        self.store.record(self.now, self.reading)
        result = self.store.snapshot(self.now, "1y")
        self.assertLessEqual(len(result["points"]), 1462)
        self.assertTrue(any(p["gap_before"] for p in result["points"]))


if __name__ == "__main__":
    unittest.main()
