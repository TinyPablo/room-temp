import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.app import create_app, fetch_reading
from backend.storage import Store


class ApiTests(unittest.TestCase):
    def test_public_api_empty_data_failure_recovery_and_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "room.db"
            with TestClient(create_app(db_path=path, collect=False)) as client:
                result = client.get("/api/room")
                self.assertEqual(result.status_code, 200)
                self.assertIsNone(result.json()["latest"])
                self.assertEqual(result.headers["cache-control"], "no-store")
                self.assertEqual(client.get("/api/room?range=forever").status_code, 400)
                self.assertEqual(client.get("/api/health").status_code, 200)
                now = int(time.time())
                store = Store(path)
                store.record(now - 60, {"temperature_c": 23, "humidity_pct": 50})
                store.record(now, None)
                self.assertEqual(client.get("/api/room").json()["status"], "offline")
                store.record(now, {"temperature_c": 24, "humidity_pct": 51})
                data = client.get("/api/room").json()
                self.assertEqual(data["status"], "online")
                self.assertEqual(data["latest"]["temperature_c"], 24)
                self.assertNotIn("PICO_TOKEN", result.text)

    def test_bad_configuration_fails_startup(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                with TestClient(create_app(db_path=Path(tmp) / "room.db", device_ip="8.8.8.8", token="x" * 32)):
                    pass

    def test_fetch_uses_auth_bounded_payload_and_no_proxy(self):
        with patch("backend.app.build_opener") as factory:
            response = factory.return_value.open.return_value.__enter__.return_value
            response.read.return_value = b'{"temperature_c": 20.5, "humidity_pct": 43}'
            self.assertEqual(fetch_reading("192.168.1.210", "a" * 32)["temperature_c"], 20.5)
            request = factory.return_value.open.call_args.args[0]
            self.assertEqual(request.get_header("Authorization"), "Bearer " + "a" * 32)
            response.read.assert_called_once_with(2049)
            response.read.return_value = b"x" * 2049
            with self.assertRaises(ValueError):
                fetch_reading("192.168.1.210", "a" * 32)


if __name__ == "__main__":
    unittest.main()
