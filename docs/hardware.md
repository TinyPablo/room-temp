# Uruchomienie Pico 2 W

## Połączenia

Połączenia wykonywać przy odłączonym zasilaniu. Moduł SHT3x ma płytkę 12 × 12 mm i cztery piny. Numery fizyczne dotyczą Pico 2 W, oglądanego od strony elementów, z microUSB u góry.

| Moduł SHT3x | Pico 2 W | Numer fizyczny |
| --- | --- | --- |
| VCC | 3V3 OUT | 36 |
| GND | GND | 38 |
| SDA | GP0 / I2C0 SDA | 1 |
| SCL | GP1 / I2C0 SCL | 2 |

Użyć czterech przewodów żeńsko-żeńskich do wlutowanych pinów. Zasilanie Pico: ładowarka USB 5 V i przewód microUSB. Do programowania potrzebny jest przewód obsługujący transmisję danych. Moduł czujnika jest zasilany z 3V3 OUT, nie z VBUS ani VSYS.

Wi-Fi musi udostępniać sieć 2,4 GHz, a serwer i Pico muszą móc komunikować się w LAN. Izolacja klientów lub sieć gościnna może blokować odczyty.

## MicroPython i konfiguracja

1. Pobrać stabilny plik UF2 przeznaczony dla [RPI_PICO2_W](https://micropython.org/download/RPI_PICO2_W/).
2. Przytrzymać BOOTSEL podczas podłączania Pico przez USB. Skopiować UF2 na pojawiający się dysk. Pico uruchomi MicroPython.
3. Utworzyć lokalny plik konfiguracji:

   ```bash
   cp firmware/secrets.example.py firmware/secrets.py
   python3 -c 'import secrets; print(secrets.token_hex(32))'
   ```

4. Wpisać nazwę sieci w `WIFI_SSID`, hasło w `WIFI_PASSWORD`, wygenerowany klucz w `API_TOKEN` i pozostawić `WIFI_COUNTRY = "PL"`. Ten sam klucz będzie używany jako `PICO_TOKEN` przez backend. Nie umieszczać konfiguracji w repozytorium. Plik na Pico nie jest szyfrowany.
5. W Thonny wybrać interpreter MicroPython dla Raspberry Pi Pico i port USB urządzenia. Zapisać w katalogu głównym Pico pliki: `config.py`, `protocol.py`, `sht3x.py`, `secrets.py`, a na końcu `main.py`. Nie kopiować całego folderu `firmware` jako podkatalogu.
6. Odłączyć i ponownie podłączyć zasilanie. W konsoli USB pojawią się MAC oraz przydzielony adres IP. W routerze utworzyć rezerwację DHCP dla tego MAC i wybranego wolnego adresu. Adres z `.env.example` jest przykładem, nie rezerwacją.

Nieprawidłowa lub brakująca konfiguracja pozostawia urządzenie w konsoli USB bez uruchamiania watchdoga. Po poprawieniu pliku wykonać reset.

## Tryb serwisowy

Do spokojnego wgrywania plików po uruchomieniu watchdoga:

1. Odłączyć zasilanie.
2. Połączyć GP15 (pin fizyczny 20) z GND (np. pin 18) przewodem jumper.
3. Podłączyć Pico do komputera. Firmware nie uruchomi Wi-Fi ani watchdoga; LED pozostanie zgaszony.
4. Wgrać pliki, odłączyć zasilanie, usunąć jumper serwisowy i ponownie zasilić Pico.

Tryb serwisowy nie wymaga dodatkowego przycisku. BOOTSEL nadal służy do wgrania UF2. Samo przerwanie programu przez Ctrl+C po aktywacji watchdoga nie wyłącza jego odliczania.

## Test odczytu w LAN

Na komputerze w tej samej sieci uruchomić poniższy kod. Adres i klucz są podawane interaktywnie; klucz nie trafi do historii poleceń.

```bash
python3 - <<'PY'
import getpass
import ipaddress
import json
import urllib.request

ip = str(ipaddress.IPv4Address(input('Pico IP: ').strip()))
token = getpass.getpass('Pico API token: ')
request = urllib.request.Request(
    'http://' + ip + '/reading',
    headers={'Authorization': 'Bearer ' + token},
)
with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=5) as response:
    print(json.load(response))
PY
```

Odpowiedź zawiera `temperature_c` i `humidity_pct`. Kod 401 oznacza brak właściwego klucza, a 503 błąd czujnika lub CRC. Adresy I²C `0x44` i `0x45` są wykrywane automatycznie. Firmware nie identyfikuje konkretnego wariantu SHT30/31/35.

## Zachowanie i odbiór sprzętowy

- Start programu następuje automatycznie po podłączeniu zasilania.
- Podczas braku Wi-Fi LED błyska przez 100 ms co 5 s przez pierwszą minutę przerwy. Później gaśnie, ale ponawianie połączenia trwa nadal.
- Watchdog ma timeout 8 s. Zwykły brak Wi-Fi nie powoduje celowego restartu.
- Każde poprawnie uwierzytelnione żądanie `/reading` uruchamia nowy pomiar. Czujnik pracuje w trybie single-shot, bez grzałki; CRC jest sprawdzane osobno dla temperatury i wilgotności.
- Pico nie zapisuje historii. Backend odpytuje je raz na minutę; awarie i wyłączenie serwera pozostawiają luki. `/healthz` Pico potwierdza działanie serwera HTTP, a nie sprawność czujnika.
- API urządzenia używa HTTP z kluczem w sieci lokalnej. Nie przekierowywać portu Pico do internetu; publiczny dostęp ma wyłącznie aplikacja na serwerze.

Przed zamknięciem obudowy sprawdzić: pierwszy odczyt, start po zaniku zasilania, odłączenie Wi-Fi na ponad minutę i automatyczny powrót, odczyt po ponownym uruchomieniu backendu oraz kilka godzin stabilnej pracy. Przewody czujnika przepinać przy wyłączonym zasilaniu.

Porównać pomiar w otwartej i zamkniętej obudowie po ustabilizowaniu temperatury. Ewentualnego wpływu ciepła Pico nie kompensować stałą poprawką przed wykonaniem porównania.

## Dokumentacja techniczna

- [Pico 2 W: pinout, zasilanie i wymiary](https://datasheets.raspberrypi.com/picow/pico-2-w-datasheet.pdf)
- [MicroPython RP2: Wi-Fi i peryferia](https://docs.micropython.org/en/latest/rp2/quickref.html)
- [Sensirion SHT3x-DIS: komendy, przeliczenia i CRC](https://sensirion.com/media/documents/213E6A3B/63A5A569/Datasheet_SHT3x_DIS.pdf)
