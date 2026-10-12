# Room

Room temperature and humidity monitoring with a Raspberry Pi Pico 2 W, an SHT3x sensor and a React dashboard. A FastAPI backend polls the device every minute and stores up to 365 days of readings in SQLite. Missing readings remain gaps in the history.

## Hardware and firmware

Connect the sensor with power disconnected:

| SHT3x | Pico 2 W | Physical pin |
| --- | --- | --- |
| VCC | 3V3 OUT | 36 |
| GND | GND | 38 |
| SDA | GP0 | 1 |
| SCL | GP1 | 2 |

Install MicroPython for the Pico 2 W. Copy `firmware/secrets.example.py` to `firmware/secrets.py` and fill in the Wi-Fi credentials and `API_TOKEN`. Generate a token with:

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Check `STATIC_IPV4` in `firmware/config.py` against the local network; reserve the device address outside the DHCP pool. Use a 2.4 GHz Wi-Fi network accessible from the backend.

Upload `config.py`, `protocol.py`, `sht3x.py`, `secrets.py` and finally `main.py` from `firmware/` to the device root. For maintenance, connect GP15 to GND before powering on to disable Wi-Fi and the watchdog. Remove the jumper before normal operation. Keep the device HTTP API on the local network.

## Docker

```bash
cp .env.example .env
```

Set `PICO_IP` to the device address and `PICO_TOKEN` to the firmware's `API_TOKEN`. `ROOM_PORT` defaults to `8765`; `IMAGE_TAG` defaults to `local`.

```bash
docker compose config --quiet
docker compose up -d --build
curl --fail http://127.0.0.1:8765/api/health
```

Open `http://127.0.0.1:8765` on the Docker host. The application binds to host loopback and serves the frontend and API from container port `8080`. Remote access requires a separately configured proxy or tunnel.

Readings persist in the `room_data` volume at `/data/room.db`. Do not use `docker compose down -v` unless the history should be deleted. `/api/health` checks the collector and storage; an offline Pico is reported by `/api/room?range=24h`.

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python scripts/preview.py
```

The preview runs at `http://127.0.0.1:8765` using synthetic data in `artifacts/preview.db`, regenerated at each start. It does not connect to the Pico. Stop it with Ctrl+C.

Keep `.env`, `firmware/secrets.py` and databases out of version control.

## Enclosure

[`enclosure/room_v02.fs`](enclosure/room_v02.fs) contains the Onshape FeatureScript source for an 88 × 62 × 38 mm enclosure. Use `assembled = false` for printing and `true` to inspect the assembly. Export the body and lid as STL in millimetres; print with their outer closed faces on the bed.

Assembly uses ten M2 inserts and ten M2 × 4 mm screws: four each for the lid and Pico, and two for the sensor. Check component fit, screw clearance and ventilation on the physical print.
