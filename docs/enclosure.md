# Obudowa ROOM V01

[Model w Onshape](https://cad.onshape.com/documents/aecef7c3fa12d92e641628ec/w/bc25d654320418098ffac464/e/5b3820c344a89a19ee895212). Źródło: [`enclosure/room_v01.fs`](../enclosure/room_v01.fs).

## Konstrukcja

Trzy części: korpus, dolna pokrywa i mała blokada czujnika. Wymiary po złożeniu: 88 × 62 × 38 mm. Korpus ma ściany i zamkniętą powierzchnię grubości 2,4 mm, narożniki o promieniu 7 mm oraz zaokrąglone zewnętrzne krawędzie zamkniętych powierzchni. Śruby pokrywy znajdują się od spodu.

Pico jest mocowane przez cztery otwory, z rozstawem 47 × 11,4 mm. Otwór micro-USB ma 15 × 10 mm. Przegroda częściowo oddziela czujnik od elektroniki Pico; nad przegrodą znajduje się przejście na przewody. Kratka obok czujnika ma dziesięć szczelin 2,4 × 17 mm. Po przeciwnej stronie znajdują się dodatkowe otwory wentylacyjne.

Czujnik 12 × 12 mm wsuwa się w prowadnice i zabezpiecza osobną blokadą. Parametr `sensorEnvelope` wynosi 2,5 mm i opisuje podany wymiar płytki wraz z elementami, nie grubość samego laminatu. Prowadnice mają pionowy otwór 2,8 mm i boczny luz 0,25 mm na stronę. Pod środkową częścią modułu pozostaje 4,6 mm wolnej przestrzeni. Podane 5,5 mm całkowitego wymiaru wraz z headerem wymaga sprawdzenia w rzeczywistym ułożeniu: model nie zawiera dokładnych brył pinów ani wtyków jumperów. Prowadnice nie mogą naciskać na elementy elektroniczne.

## Elementy montażowe

| Element | Liczba | Zastosowanie |
| --- | ---: | --- |
| Insert M2 | 9 | 4 korpus, 4 Pico, 1 blokada czujnika |
| Śruba M2 × 4 mm pod łbem | 9 | Te same punkty mocowania |
| Przewód żeński do pinów | 4 | Zasilanie i I²C |

Otwory insertów mają średnicę 3,1 mm i głębokość 4,5 mm, zgodnie z wcześniejszym dopasowaniem insertów. Otwory przelotowe mają 2,3 mm. Gniazda łbów pokrywy mają średnicę 3,8 mm i głębokość 2,5 mm; pod łbem pozostaje 1,5 mm tworzywa. Przed drukiem sprawdzić średnicę rzeczywistych łbów.

## Eksport i druk

1. W Onshape otworzyć cechę `RoomEnclosureV01`. Pozostawić `assembled = false`, aby uzyskać rozłożone części w orientacji do druku. `assembled = true` służy do kontroli złożenia.
2. Wyeksportować trzy części jako STL w milimetrach, z dokładną siatką. Pliki STL nie są dołączone do repozytorium.
3. W slicerze K1C wybrać profil używanego PETG. Korpus drukować zamkniętą powierzchnią na stole, wnętrzem do góry; pokrywę zewnętrzną powierzchnią na stole, blokadę płasko.
4. Sprawdzić podgląd warstw, mosty nad szczelinami i prowadnice. Konstrukcja przewiduje krótkie mosty; rzeczywistą jakość bez podpór należy ocenić na pierwszym wydruku.

Zaokrąglenia są częścią geometrii. Suszarka nie jest potrzebna do uzyskania kształtu; ewentualne nierówności usuwać przed montażem elektroniki.

## Montaż i sprawdzenie

1. Osadzić inserty przed włożeniem elektroniki, bez deformowania słupków i prowadnic.
2. Przymierzyć Pico i przewód USB. Przykręcić płytkę czterema śrubami, bez wyginania laminatu.
3. Wsunąć moduł w prowadnice, sprawdzając luz elementów i pinów. Zamontować blokadę. Jeśli krawędzie modułu kolidują z prowadnicami, dopasować parametry przed ponownym wydrukiem.
4. Podłączyć cztery przewody według [planu połączeń](hardware.md). Ułożyć je bez naprężeń, z dala od anteny Pico i powierzchni czujnika. Sprawdzić miejsce na wtyki przed zamknięciem.
5. Założyć pokrywę i skręcić czterema śrubami. Ustawić urządzenie pokrywą do dołu, z odsłoniętą kratką.
6. Porównać ustabilizowane odczyty przy otwartej i zamkniętej obudowie w tym samym miejscu. Różnica pozwoli ocenić wpływ ciepła elektroniki i wentylacji.

Model jest prototypem zweryfikowanym geometrycznie. Dopasowanie wydruku, przewodów i komponentów oraz wpływ obudowy na pomiar pozostają do sprawdzenia fizycznego.
