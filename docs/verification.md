# Weryfikacja prototypu

## Oprogramowanie

Stan z 2026-10-12:

- 18 testów Python zakończonych powodzeniem: CRC i dekodowanie SHT3x, autoryzacja HTTP, limity żądań, ponowna inicjalizacja czujnika, tryb serwisowy, walidacja danych, retencja, luki i API.
- Produkcyjny build React/TypeScript zakończony powodzeniem. Vite zgłasza ostrzeżenie o rozmiarze głównego pliku JS (około 635 kB przed kompresją).
- Testy w lokalnym Chrome: widoki 1440 px i 390 px, brak poziomego overflow na telefonie, przełączanie obu pomiarów i czterech zakresów, przerwa na wykresie, błąd backendu, pusty stan i brak błędów JavaScript.
- Obraz Docker zbudowany lokalnie dla Linux ARM64; serwer docelowy zbuduje obraz dla własnej architektury.
- Test integracyjny kontenera z atrapą Pico o stałym IP: odczyt z autoryzacją, serwowanie strony, zachowanie historii po restarcie, luka przy HTTP 503 czujnika, poprawny healthcheck podczas awarii urządzenia i automatyczny powrót odczytów w kolejnym cyklu. Tymczasowe kontenery, sieć i wolumen testowy zostały usunięte po teście.
- Konfiguracja Compose zweryfikowana bez ujawniania sekretów.

Zrzuty lokalnego podglądu znajdują się w ignorowanym katalogu `artifacts/`. Przedstawiają syntetyczne dane. Playwright i skrypty sterujące lokalnym Chrome znajdują się poza repozytorium; nie są zależnością aplikacji.

## Obudowa

FeatureScript został skompilowany i wykonany w Onshape dla układu do druku oraz złożenia. Kontrole V02 potwierdziły dwie osobne, połączone wewnętrznie bryły o dodatniej objętości, brak przecięć z uproszczonym obrysem Pico, pionową drogą wkładania czujnika, przestrzenią złączy (25 mm za krawędzią PCB) i drogami śrubokręta Ø6 mm i brak nakładania się drukowanych części po złożeniu. Dopuszczone są powierzchnie styku. Model zapisano w osobnym workspace; odnośnik znajduje się w [instrukcji obudowy](enclosure.md).

Kontrola nie obejmuje dokładnych brył przewodów, wtyczki USB, headerów i elementów na module czujnika.

## Testy wymagające sprzętu i wdrożenia

- Wgranie firmware na konkretny Pico 2 W i odczyt rzeczywistego SHT3x.
- Zanik zasilania, przerwa Wi-Fi, działanie LED i watchdoga na urządzeniu.
- Potwierdzenie rezerwacji DHCP `192.168.1.205`.
- Fizyczne dopasowanie wydruku, jumperów, insertów i przewodu USB.
- Porównanie pomiaru w otwartej i zamkniętej obudowie.
- Wdrożenie na serwerze, konfiguracja DNS/ingress i test publicznej domeny.

Testy hostowe używają atrap interfejsów sprzętowych i nie stanowią weryfikacji firmware na MicroPythonie działającym na Pico. Sam poprawny model CAD nie potwierdza tolerancji konkretnego wydruku PETG.
