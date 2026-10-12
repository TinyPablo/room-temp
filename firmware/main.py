import gc
import json
import network
import machine
import rp2
import select
import socket
import time

import config
from protocol import route
from sht3x import SHT3x


def respond(client, status, payload):
    body = json.dumps(payload).encode()
    reasons = {200: "OK", 400: "Bad Request", 401: "Unauthorized", 404: "Not Found",
               405: "Method Not Allowed", 431: "Request Header Fields Too Large",
               503: "Service Unavailable"}
    header = "HTTP/1.1 %d %s\r\nContent-Type: application/json\r\nContent-Length: %d\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n" % (status, reasons[status], len(body))
    client.write(header.encode() + body)


def serve_client(client, token, sensor):
    client.settimeout(1)
    request = b""
    started = time.ticks_ms()
    # Bound total header time as well as each socket read to protect the watchdog.
    while b"\r\n\r\n" not in request:
        if time.ticks_diff(time.ticks_ms(), started) > 1500:
            return sensor
        chunk = client.recv(256)
        if not chunk:
            return sensor
        request += chunk
        if len(request) > 2048:
            respond(client, 431, {"error": "headers_too_large"})
            return sensor
    status, path = route(request, token)
    if status != 200:
        respond(client, status, {"error": "request_rejected"})
    elif path == b"/healthz":
        respond(client, 200, {"ok": True})
    else:
        try:
            if sensor is None:
                bus = machine.I2C(config.I2C_ID, sda=machine.Pin(config.SDA_PIN),
                                  scl=machine.Pin(config.SCL_PIN), freq=config.I2C_FREQUENCY,
                                  timeout=50_000)
                sensor = SHT3x(bus)
            temperature, humidity = sensor.measure()
            respond(client, 200, {"temperature_c": temperature, "humidity_pct": humidity})
        except (OSError, ValueError):
            sensor = None
            respond(client, 503, {"error": "sensor_unavailable"})
    return sensor


def run(settings):
    rp2.country(settings.WIFI_COUNTRY)
    led = machine.Pin("LED", machine.Pin.OUT, value=0)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print("MAC:", ":".join("%02x" % b for b in wlan.config("mac")))
    wdt = machine.WDT(timeout=config.WATCHDOG_MS)
    listener = None
    poller = select.poll()
    sensor = None
    outage_started = time.ticks_ms()
    retry_at = time.ticks_ms()
    was_connected = False
    announced_ip = None
    while True:
        now = time.ticks_ms()
        connected = wlan.isconnected()
        if not connected:
            if was_connected:
                outage_started = now
                retry_at = now
            if listener is not None:
                poller.unregister(listener)
                listener.close()
                listener = None
            elapsed = time.ticks_diff(now, outage_started) if outage_started is not None else 60_000
            if elapsed >= 60_000:
                outage_started = None  # Do not blink again when the ticks counter wraps.
            led.value(elapsed < 60_000 and elapsed % 5000 < 100)
            if time.ticks_diff(now, retry_at) >= 0:
                try:
                    wlan.disconnect()
                    wlan.connect(settings.WIFI_SSID, settings.WIFI_PASSWORD)
                except OSError:
                    pass
                retry_at = time.ticks_add(now, config.RECONNECT_MS)
        else:
            led.off()
            ip = wlan.ifconfig()[0]
            if ip != announced_ip:
                print("IP:", ip)
                announced_ip = ip
            if listener is None:
                listener = socket.socket()
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                listener.bind(("0.0.0.0", config.HTTP_PORT))
                listener.listen(2)
                listener.setblocking(False)
                poller.register(listener, select.POLLIN)
            if poller.poll(0):
                client = None
                try:
                    client, _ = listener.accept()
                    sensor = serve_client(client, settings.API_TOKEN, sensor)
                except OSError:
                    pass
                finally:
                    if client is not None:
                        client.close()
                    gc.collect()
        was_connected = connected
        wdt.feed()
        time.sleep_ms(25)


def start():
    led = machine.Pin("LED", machine.Pin.OUT, value=0)
    if not machine.Pin(config.MAINTENANCE_PIN, machine.Pin.IN, machine.Pin.PULL_UP).value():
        print("Maintenance mode: Wi-Fi and watchdog disabled")
        return
    try:
        import secrets as settings
        token = settings.API_TOKEN
        if (not settings.WIFI_SSID or not settings.WIFI_PASSWORD or len(token) < 32 or
                any(not ("a" <= c <= "z" or "A" <= c <= "Z" or "0" <= c <= "9") for c in token)):
            raise ValueError("Invalid configuration")
        if len(settings.WIFI_COUNTRY) != 2:
            raise ValueError("Invalid country code")
    except (ImportError, AttributeError, TypeError, ValueError):
        print("Configure secrets.py, then reset. Watchdog is disabled.")
        return
    try:
        run(settings)
    except KeyboardInterrupt:
        led.off()
        print("Stopped; power-cycle for normal operation. Active watchdog may reset the board.")
    except Exception as error:
        # Avoid writing secrets to serial output; the watchdog or explicit reset recovers.
        print("Startup/runtime failure:", type(error).__name__)
        time.sleep_ms(2000)
        machine.reset()


if __name__ == "__main__":
    start()
