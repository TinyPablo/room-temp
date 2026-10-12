import asyncio
import ipaddress
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.storage import RANGES, Store, validate_reading

logger = logging.getLogger("room")


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_reading(ip, token):
    request = Request("http://%s/reading" % ip, headers={"Authorization": "Bearer " + token})
    # Never forward the device token to an HTTP proxy or a redirected host.
    opener = build_opener(ProxyHandler({}), NoRedirects())
    with opener.open(request, timeout=5) as response:
        payload = response.read(2049)
        if len(payload) > 2048:
            raise ValueError("Device response too large")
        return validate_reading(json.loads(payload))


def create_app(db_path=None, device_ip=None, token=None, collect=True, static_dir=None):
    path = db_path or os.environ.get("DATABASE_PATH", "data/room.db")
    ip = device_ip or os.environ.get("PICO_IP", "")
    secret = token or os.environ.get("PICO_TOKEN", "")
    static = Path(static_dir or os.environ.get("STATIC_DIR", "frontend/dist"))
    state = {"last_cycle": None, "task": None, "store": None}

    async def collector():
        while True:
            reading = None
            try:
                reading = await asyncio.to_thread(fetch_reading, ip, secret)
            except (OSError, URLError, HTTPError, ValueError, UnicodeError):
                logger.warning("Device unavailable or invalid reading; leaving a gap")
            try:
                await asyncio.to_thread(state["store"].record, int(time.time()), reading)
                state["last_cycle"] = time.monotonic()
            except Exception:
                logger.exception("Cannot persist measurement")
            await asyncio.sleep(60 - time.time() % 60)

    @asynccontextmanager
    async def lifespan(app):
        if collect:
            address = ipaddress.ip_address(ip)
            if address.version != 4 or not address.is_private or address.is_loopback:
                raise ValueError("PICO_IP must be a private LAN IPv4 address")
            if len(secret) < 32 or not secret.isascii() or not secret.isalnum():
                raise ValueError("PICO_TOKEN must contain at least 32 ASCII letters/digits")
        state["store"] = Store(path)
        state["last_cycle"] = time.monotonic()
        if collect:
            state["task"] = asyncio.create_task(collector())
        yield
        if state["task"]:
            state["task"].cancel()
            try:
                await state["task"]
            except asyncio.CancelledError:
                pass

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    def health(response: Response):
        task = state["task"]
        healthy = (not collect or (task is not None and not task.done() and
                                   time.monotonic() - state["last_cycle"] < 150))
        response.status_code = 200 if healthy else 503
        return {"ok": healthy}

    @app.get("/api/room")
    def room(range: str = Query("24h")):
        if range not in RANGES:
            raise HTTPException(400, "Invalid range")
        return state["store"].snapshot(int(time.time()), range)

    @app.get("/")
    def index():
        if not (static / "index.html").is_file():
            raise HTTPException(503, "Frontend build unavailable")
        return FileResponse(static / "index.html", headers={"Cache-Control": "no-cache"})

    @app.get("/favicon.svg")
    def favicon():
        return FileResponse(static / "favicon.svg")

    app.mount("/assets", StaticFiles(directory=static / "assets", check_dir=False), name="assets")
    return app


app = create_app()
