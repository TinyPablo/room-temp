import unittest

from firmware.protocol import route
from firmware.sht3x import crc8, decode


class FirmwareTests(unittest.TestCase):
    def test_crc_datasheet_vector(self):
        self.assertEqual(crc8(bytes([0xBE, 0xEF])), 0x92)

    def test_decode_and_corrupt_frame(self):
        t, h = bytes([0x66, 0x66]), bytes([0x80, 0x00])
        frame = t + bytes([crc8(t)]) + h + bytes([crc8(h)])
        self.assertEqual(decode(frame), (25.0, 50.0))
        for index in range(6):
            broken = bytearray(frame)
            broken[index] ^= 1
            with self.assertRaises(ValueError):
                decode(broken)
        with self.assertRaises(ValueError):
            decode(b"short")

    def test_auth_and_routes(self):
        token = "a" * 32
        def request(path, headers=b"", method=b"GET"):
            return method + b" " + path + b" HTTP/1.1\r\n" + headers + b"\r\n"
        auth = b"authorization: Bearer " + token.encode() + b"\r\n"
        self.assertEqual(route(request(b"/reading", auth), token), (200, b"/reading"))
        self.assertEqual(route(request(b"/reading"), token)[0], 401)
        self.assertEqual(route(request(b"/reading", auth + auth), token)[0], 401)
        self.assertEqual(route(request(b"/reading", auth, b"POST"), token)[0], 405)
        self.assertEqual(route(request(b"/unknown", auth), token)[0], 404)


if __name__ == "__main__":
    unittest.main()
