import time


def crc8(data):
    crc = 0xFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def decode(data):
    if len(data) != 6 or crc8(data[:2]) != data[2] or crc8(data[3:5]) != data[5]:
        raise ValueError("Invalid SHT3x CRC or response length")
    temperature = -45 + 175 * ((data[0] << 8) | data[1]) / 65535
    humidity = 100 * ((data[3] << 8) | data[4]) / 65535
    return round(temperature, 2), round(humidity, 2)


class SHT3x:
    def __init__(self, i2c):
        self.i2c = i2c
        found = i2c.scan()
        self.address = next((a for a in (0x44, 0x45) if a in found), None)
        if self.address is None:
            raise OSError("SHT3x not found")
        i2c.writeto(self.address, b"\x30\xa2")
        time.sleep_ms(3)
        i2c.writeto(self.address, b"\x30\x66")  # Keep the heater disabled.

    def measure(self):
        self.i2c.writeto(self.address, b"\x24\x00")
        time.sleep_ms(20)
        return decode(self.i2c.readfrom(self.address, 6))
