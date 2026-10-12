# Room

Pomiar temperatury i wilgotności jednego pokoju: Raspberry Pi Pico 2 W, moduł SHT3x przez I²C, MicroPython oraz publiczny panel React z shadcn/ui.

Pico udostępnia świeży pomiar przez HTTP w LAN. Backend FastAPI pobiera go co minutę i zapisuje w SQLite. Historia obejmuje 365 dni, a domyślny widok ostatnie 24 godziny. Przerwy w dostępności pozostają lukami. Strona nie wymaga logowania; klucz dostępu do Pico pozostaje w backendzie.

## Elementy projektu

- `firmware/`: MicroPython, Wi-Fi, sterownik SHT3x z CRC, watchdog, tryb serwisowy.
- `backend/`: kolektor, baza i publiczne API.
- `frontend/`: responsywny panel temperatury i wilgotności.
- `enclosure/`: model obudowy w FeatureScript.
- [Podłączenie i uruchomienie Pico](docs/hardware.md).
- [Obudowa, druk i montaż](docs/enclosure.md).
- [Docker, serwer i domena](docs/deployment.md).
- [Weryfikacja prototypu](docs/verification.md).

## Testy i lokalny podgląd

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python scripts/preview.py
```

Podgląd jest dostępny pod `http://127.0.0.1:8765`. Używa wyłącznie syntetycznych danych w `artifacts/preview.db`, w tym przykładowej przerwy w pomiarach. Nie łączy się z Pico i nie jest trybem produkcyjnym. Zakończenie: Ctrl+C. Dane podglądu są generowane na nowo przy uruchomieniu.

## Konfiguracja rzeczywistych odczytów

Na Pico: `firmware/secrets.py` utworzony z przykładu, zapisany na urządzeniu jako `secrets.py`. Na serwerze: `.env` utworzony z `.env.example`. `API_TOKEN` Pico i `PICO_TOKEN` backendu muszą być identyczne. Docelowy adres Pico to `192.168.1.205`, ustawiany statycznie przez `STATIC_IPV4` w `firmware/config.py`.

Uruchomienie przez Docker i konfigurację istniejącego tunelu opisuje instrukcja wdrożenia. W repozytorium nie przechowuje się haseł Wi-Fi, tokenów ani rzeczywistych baz danych.
