# Obudowa ROOM V02

[Model w Onshape](https://cad.onshape.com/documents/aecef7c3fa12d92e641628ec/w/ba0e46e05e1a01fc644142d7/e/5b3820c344a89a19ee895212). Źródło: [`enclosure/room_v02.fs`](../enclosure/room_v02.fs).

## Konstrukcja

Dwie części: korpus i dolna pokrywa. Wymiary po złożeniu: 88 × 62 × 38 mm. Korpus ma ściany i zamkniętą powierzchnię grubości 2,4 mm, narożniki o promieniu 7 mm oraz zaokrąglone zewnętrzne krawędzie zamkniętych powierzchni. Śruby pokrywy znajdują się od spodu.

Pico jest mocowane przez cztery otwory, z rozstawem 47 × 11,4 mm. Otwór micro-USB ma 15 × 10 mm. Przegroda częściowo oddziela czujnik od elektroniki Pico; nad przegrodą znajduje się przejście na przewody. Kratka obok czujnika ma dziesięć szczelin 2,4 × 17 mm. Po przeciwnej stronie znajdują się dodatkowe otwory wentylacyjne.

Czujnik 12 × 12 mm opuszcza się pionowo na dwa słupki i przykręca przez otwory płytki. Nie ma prowadnic, nawisu ani osobnej blokady. Otwory modułu mają średnicę 2 mm i rozstaw 9 mm; ich środki leżą 1,5 mm od bocznych krawędzi i 1,5 mm od krawędzi przeciwnej do headerów. Parametr `sensorPcbThickness` opisuje sam laminat: 1,5 mm. M2 × 4 mm przechodzi przez laminat i wchodzi nominalnie 2,5 mm w insert.

Płytka spoczywa 10 mm nad zewnętrzną powierzchnią korpusu, z 7,6 mm przestrzeni do jego wewnętrznej powierzchni. Elementy i headery są skierowane ku otwartej stronie korpusu podczas montażu. Słupki znajdują się po lewej stronie płytki w jej współrzędnych modelu; headery wychodzą w prawo, wzdłuż komory czujnika, zamiast w kierunku kratki lub przegrody. Za krawędzią płytki pozostaje sprawdzona geometrycznie przestrzeń długości 25 mm na zagięte headery i żeńskie złącza. Nie jest to pomiar rzeczywistych jumperów.

Model sprawdza pionową drogę opuszczania płytki, przestrzeń złączy oraz dostęp śrubokręta o średnicy 6 mm do obu śrub. Podane 2,5 mm z elementami i 5,5 mm z headerem nie są grubością laminatu ani wymiarem szczeliny montażowej. Dokładny przebieg przewodów wymaga fizycznej przymiarki.

## Kolejność wkładania czujnika

```text
otwarta obudowa, widok od góry

    otwory 9 mm między środkami
              ↓
        ┌────────────┐
        │ ○          ├── headery i złącza → wolna komora
        │            │
        │ ○          │
        └────────────┘

Płytka schodzi pionowo na słupki.
Dwie śruby wkłada się i dokręca od góry.
```

## Elementy montażowe

| Element | Liczba | Zastosowanie |
| --- | ---: | --- |
| Insert M2 | 10 | 4 korpus, 4 Pico, 2 czujnik |
| Śruba M2 × 4 mm pod łbem | 10 | Te same punkty mocowania |
| Przewód żeński do pinów | 4 | Zasilanie i I²C |

Otwory insertów mają średnicę 3,1 mm i głębokość 4,5 mm, zgodnie z wcześniejszym dopasowaniem insertów. Otwory przelotowe mają 2,3 mm. Gniazda łbów pokrywy mają średnicę 3,8 mm i głębokość 2,5 mm; pod łbem pozostaje 1,5 mm tworzywa. Przed drukiem sprawdzić średnicę rzeczywistych łbów.

## Eksport i druk

1. W Onshape otworzyć cechę `RoomEnclosureV02`. Pozostawić `assembled = false`, aby uzyskać rozłożone części w orientacji do druku. `assembled = true` służy do kontroli złożenia.
2. Wyeksportować dwie części jako STL w milimetrach, z dokładną siatką. Pliki STL nie są dołączone do repozytorium.
3. W slicerze K1C wybrać profil używanego PETG. Korpus drukować zamkniętą powierzchnią na stole, wnętrzem do góry; pokrywę zewnętrzną powierzchnią na stole.
4. Sprawdzić podgląd warstw, mosty nad szczelinami i słupki. Konstrukcja przewiduje krótkie mosty; rzeczywistą jakość bez podpór należy ocenić na pierwszym wydruku.

Zaokrąglenia są częścią geometrii. Suszarka nie jest potrzebna do uzyskania kształtu; ewentualne nierówności usuwać przed montażem elektroniki.

## Montaż i sprawdzenie

1. Osadzić inserty przed włożeniem elektroniki, bez deformowania słupków.
2. Przymierzyć Pico i przewód USB. Przykręcić płytkę czterema śrubami, bez wyginania laminatu.
3. Przed montażem sprawdzić, czy śruby M2 swobodnie przechodzą przez otwory czujnika Ø2 mm. Nie wkręcać ich na siłę w laminat. Sprawdzić, czy łby nie dotykają elementów lub odsłoniętych pól elektrycznych.
4. Podłączyć przewody do czujnika poza obudową, następnie opuścić moduł prosto na dwa słupki, stroną z elementami do góry i headerami w wolną część komory. Przykręcić dwiema śrubami M2 × 4 mm bez wyginania laminatu. Połączyć przewody z Pico według [planu połączeń](hardware.md), pozostawiając luz. Nie trzeba wsuwać płytki pod kątem ani przewlekać jej pod uchwytem.
5. Założyć pokrywę i skręcić czterema śrubami. Ustawić urządzenie pokrywą do dołu, z odsłoniętą kratką.
6. Porównać ustabilizowane odczyty przy otwartej i zamkniętej obudowie w tym samym miejscu. Różnica pozwoli ocenić wpływ ciepła elektroniki i wentylacji.

Model jest prototypem zweryfikowanym geometrycznie. Dopasowanie wydruku, przewodów i komponentów oraz wpływ obudowy na pomiar pozostają do sprawdzenia fizycznego.
