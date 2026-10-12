# Wdrożenie room-temp

## Układ

| Element | Wartość |
| --- | --- |
| Serwer | `pawel@192.168.1.200` |
| Katalog | `/home/pawel/projects/room-temp` |
| Compose | projekt `room-temp`, plik `docker-compose.yml` |
| Obraz | budowany lokalnie z `Dockerfile`, tag `room-temp:<IMAGE_TAG>` |
| Dane | wolumen `room-temp_room_data`, baza `/data/room.db` |
| Port aplikacji w kontenerze | `8080` |
| Publikowany port serwera | `127.0.0.1:8765` |
| Pico | `192.168.1.205:80`, rezerwacja DHCP |
| Domena | `room.pawelzawada.dev` |

Backend i zbudowany frontend działają w jednym kontenerze. SQLite nie udostępnia portu sieciowego. Proces działa jako UID 10001. System plików kontenera jest tylko do odczytu, poza wolumenem danych i `/tmp`. Uvicorn uruchamia jeden worker, aby nie dublować kolektora pomiarów.

Planowany przepływ: DNS Cloudflare → istniejący tunel cloudflared → `http://127.0.0.1:8765` → aplikacja. Backend odpytuje Pico przez LAN. Caddy nie jest potrzebny na tej trasie; jego istniejąca obsługa Energylandii pozostaje bez zmian.

Inspekcja z 2026-10-12 potwierdziła katalog projektów, aktywne Compose i konfiguracje również nieuruchomionych projektów. Port 8765 nie występował w listenerach ani odczytanych deklaracjach portów. `room.pawelzawada.dev` nie zwrócił adresu przez resolver serwera i nie miał reguły ingress. Nie jest to rezerwacja portu ani pełny audyt konta DNS.

## Kontrola przed wdrożeniem

Wszystkie polecenia zmieniające serwer wykonuje administrator. Zmiany źródeł przechodzą przez PR do `develop`, a po weryfikacji przez osobny PR do `main`. Produkcję wdrażać z zatwierdzonego `main`.

Przez lokalne SSH:

```bash
ssh pawel@192.168.1.200
docker compose ls --all
docker ps -a --format '{{.Names}}\t{{.Ports}}'
ss -ltnu
find /home/pawel/projects -maxdepth 3 -type f \( -name '*compose*.yml' -o -name '*compose*.yaml' \) -exec grep -HnE 'ports:|8765|published:|127.0.0.1:' {} \;
```

Sprawdzić także wartości portów podstawiane ze zmiennych środowiskowych w znalezionych plikach, również dla zatrzymanych projektów. Nie publikować pełnego wyniku `docker compose config`, który może zawierać sekrety. W razie konfliktu zmienić `ROOM_PORT` i port reguły ingress razem.

## Pierwsze uruchomienie

Gdy zmiany są już na `main`, na serwerze:

```bash
cd /home/pawel/projects
git clone --branch main git@github.com:TinyPablo/room-temp.git room-temp
cd /home/pawel/projects/room-temp
umask 077
cp .env.example .env
nano .env
```

W `.env` ustawić:

- `PICO_IP=192.168.1.205`;
- `PICO_TOKEN`: ten sam klucz co `API_TOKEN` w `secrets.py` Pico;
- `ROOM_PORT=8765`, po ponownym sprawdzeniu portów;
- `IMAGE_TAG`: unikalny tag wydania, np. `v0.1.0`.

```bash
docker compose -p room-temp -f docker-compose.yml config --quiet
docker compose -p room-temp -f docker-compose.yml build app
docker compose -p room-temp -f docker-compose.yml up -d --no-build --pull never app
docker compose -p room-temp -f docker-compose.yml ps
curl --fail http://127.0.0.1:8765/api/health
curl --fail 'http://127.0.0.1:8765/api/room?range=24h'
curl --fail --output /dev/null http://127.0.0.1:8765/
```

`/api/health` oznacza sprawność kolektora i zapisu, nie obecność Pico. Przy wyłączonym Pico poprawnym stanem aplikacji jest HTTP 200, `status: offline` i brak nowego pomiaru. Po uruchomieniu Pico potwierdzić `online`, zmieniające się `measured_at` i przyrost próbek po kolejnych minutach. Kontener oznaczony jako unhealthy nie jest automatycznie restartowany przez samą politykę `unless-stopped`; sprawdzić wtedy logi i wolne miejsce na dysku.

## Domena i istniejący tunel

Odczytana konfiguracja: `/etc/cloudflared/config.yml`, tunel `e8c8d886-cfe8-4d3b-b803-32a7854e0867`. Przed zmianą sprawdzić, że aktywny proces nadal korzysta z tego pliku. Dla restartu tunelu używać SSH po LAN, ponieważ tunel przenosi także zdalne SSH.

```bash
ps -C cloudflared -o args=
systemctl is-active cloudflared caddy
getent hosts room.pawelzawada.dev
sudo cp -a /etc/cloudflared/config.yml /etc/cloudflared/config.yml.before-room
sudoedit /etc/cloudflared/config.yml
```

Przed końcową regułą `http_status:404` dodać:

```yaml
  - hostname: room.pawelzawada.dev
    service: http://127.0.0.1:8765
```

Pozostałe trasy zachować, w szczególności SSH i Energylandię kierowaną na lokalny HTTPS. Nie dodawać dla Room reguły w Caddy.

```bash
sudo cloudflared tunnel --config /etc/cloudflared/config.yml ingress validate
sudo cloudflared tunnel --config /etc/cloudflared/config.yml ingress rule https://room.pawelzawada.dev
cloudflared tunnel route dns e8c8d886-cfe8-4d3b-b803-32a7854e0867 room.pawelzawada.dev
sudo systemctl restart cloudflared
systemctl is-active cloudflared
curl --fail https://room.pawelzawada.dev/api/health
curl --fail 'https://room.pawelzawada.dev/api/room?range=24h'
curl --fail --output /dev/null https://room.pawelzawada.dev/
curl --fail --output /dev/null https://pawelzawada.dev/
curl --fail --output /dev/null https://energylandia.pawelzawada.dev/
```

Polecenie `route dns` uruchamiać w istniejącym środowisku CLI z uprawnieniami do zarządzania DNS; plik credentials tunelu sam w sobie może ich nie zapewniać. Nie używać wymuszonego nadpisywania istniejących rekordów. W przypadku konfliktu najpierw sprawdzić rekord w Cloudflare.

## Aktualizacja, backup i rollback

Przed aktualizacją zapisać identyfikator starego obrazu, zrobić spójną kopię SQLite i zachować poprzednią konfigurację:

```bash
cd /home/pawel/projects/room-temp
mkdir -p backups
chmod 700 backups
docker inspect --format '{{.Image}}' "$(docker compose -p room-temp -f docker-compose.yml ps -q app)" > backups/previous-image-id.txt
docker image tag "$(cat backups/previous-image-id.txt)" room-temp:rollback
cp -p .env backups/env.previous
docker compose -p room-temp -f docker-compose.yml exec -T app python -c "import sqlite3; source=sqlite3.connect('/data/room.db'); backup=sqlite3.connect('/data/room.backup.db'); source.backup(backup); backup.close(); source.close()"
docker compose -p room-temp -f docker-compose.yml cp app:/data/room.backup.db backups/room-before-update.db
```

Katalog `backups` zawiera także konfigurację z kluczem; nie dodawać go do Gita. Dla kolejnych wydań zachowywać osobne kopie zamiast nadpisywać ostatnią potrzebną kopię.

Po pobraniu przez administratora zatwierdzonej wersji `main` ustawić nowy `IMAGE_TAG`, zbudować i uruchomić jak przy pierwszym wdrożeniu. Nie usuwać wolumenu. Test: odczyty, historia sprzed aktualizacji, restart kontenera i dalsze zbieranie próbek.

Rollback obrazu przy zgodnym schemacie bazy:

```bash
IMAGE_TAG=rollback docker compose -p room-temp -f docker-compose.yml up -d --no-build --pull never app
curl --fail http://127.0.0.1:8765/api/health
```

W razie potrzeby przywrócić także `backups/env.previous`. Ta wersja nie wykonuje migracji niszczących dane. Przed przyszłymi zmianami schematu określić zgodność i procedurę odtworzenia SQLite przy zatrzymanej aplikacji; nie kopiować samego aktywnego pliku `.db` z pominięciem WAL.

Rollback pierwszego udostępnienia domeny:

```bash
sudo cp -a /etc/cloudflared/config.yml.before-room /etc/cloudflared/config.yml
sudo cloudflared tunnel --config /etc/cloudflared/config.yml ingress validate
sudo systemctl restart cloudflared
cd /home/pawel/projects/room-temp
docker compose -p room-temp -f docker-compose.yml stop app
```

Przywrócenie całego pliku tunelu jest poprawne tylko jeśli nie dodano później innych tras; w przeciwnym razie usunąć wyłącznie wpis Room. Rekord DNS dodany dla Room usunąć osobno w używanym panelu/API Cloudflare. Nie używać `down -v`; historia pozostaje w wolumenie.
