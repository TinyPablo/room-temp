import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from firmware import config, protocol, sht3x


class DeviceRuntimeTests(unittest.TestCase):
    def setUp(self):
        modules = {name: types.ModuleType(name) for name in ("machine", "network", "rp2")}
        modules.update(config=config, protocol=protocol, sht3x=sht3x)
        with patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location("device_main", Path("firmware/main.py"))
            self.device = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.device)
        self.clock = patch.object(self.device, "time", Mock(ticks_ms=Mock(return_value=0), ticks_diff=lambda a, b: a-b))
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.token = "a" * 32

    def client(self, authenticated=True):
        client = Mock()
        auth = "Authorization: Bearer " + self.token + "\r\n" if authenticated else ""
        client.recv.return_value = ("GET /reading HTTP/1.1\r\n" + auth + "\r\n").encode()
        return client

    def test_unauthorized_request_never_measures(self):
        sensor = Mock()
        client = self.client(False)
        self.device.serve_client(client, self.token, sensor)
        sensor.measure.assert_not_called()
        self.assertTrue(client.write.call_args.args[0].startswith(b"HTTP/1.1 401"))

    def test_sensor_failure_returns_503_and_next_request_reinitializes(self):
        sensor = Mock()
        sensor.measure.side_effect = ValueError("CRC")
        failed = self.client()
        self.assertIsNone(self.device.serve_client(failed, self.token, sensor))
        self.assertTrue(failed.write.call_args.args[0].startswith(b"HTTP/1.1 503"))
        replacement = Mock()
        replacement.measure.return_value = (22.1, 48.2)
        self.device.machine.I2C = Mock()
        self.device.machine.Pin = Mock()
        with patch.object(self.device, "SHT3x", return_value=replacement):
            recovered = self.client()
            self.assertIs(self.device.serve_client(recovered, self.token, None), replacement)
        body = recovered.write.call_args.args[0].split(b"\r\n\r\n")[1]
        self.assertEqual(json.loads(body), {"temperature_c": 22.1, "humidity_pct": 48.2})

    def test_slow_headers_are_abandoned_without_reading_sensor(self):
        self.device.time.ticks_ms.side_effect = [0, 0, 1601]
        client = self.client()
        client.recv.return_value = b"G"
        sensor = Mock()
        self.device.serve_client(client, self.token, sensor)
        self.assertEqual(client.recv.call_count, 1)
        sensor.measure.assert_not_called()

    def test_oversized_headers_are_rejected(self):
        client = self.client()
        client.recv.return_value = b"a" * 256
        sensor = Mock()
        self.device.serve_client(client, self.token, sensor)
        self.assertTrue(client.write.call_args.args[0].startswith(b"HTTP/1.1 431"))
        sensor.measure.assert_not_called()

    def test_maintenance_mode_never_starts_wifi_or_watchdog(self):
        self.device.machine.Pin = Mock(return_value=Mock(value=Mock(return_value=0)))
        with patch.object(self.device, "run") as run:
            self.device.start()
        run.assert_not_called()

    def test_invalid_secrets_stay_in_console_without_reset(self):
        self.device.machine.Pin = Mock(return_value=Mock(value=Mock(return_value=1)))
        self.device.machine.reset = Mock()
        invalid = types.SimpleNamespace(API_TOKEN="short", WIFI_SSID="test", WIFI_PASSWORD="test", WIFI_COUNTRY="PL")
        with patch.dict(sys.modules, secrets=invalid), patch.object(self.device, "run") as run:
            self.device.start()
        run.assert_not_called()
        self.device.machine.reset.assert_not_called()


if __name__ == "__main__":
    unittest.main()
