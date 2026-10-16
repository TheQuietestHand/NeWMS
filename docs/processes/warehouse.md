# Procesy magazynowe — zapis obserwacji i planowanych zachowań (CONTEXT)

> Poniższy materiał pochodzi z wcześniejszych rozmów o fizycznym magazynie jako przypadku użycia. Nie jest gotową specyfikacją wdrożeniową i nie powinien wymuszać konfiguracji jednego zakładu na innych.

## Dwa istotne przepływy

**Maszyny:** przyjęcie, identyfikacja i parkowanie, wyszukiwanie po atrybutach, przemieszczenie, wydanie do warsztatu, wykonanie prac, odstawienie do magazynu lub strefy wydania, wysyłka. Dopuszcza się ręczne zmiany adresowania przy zachowaniu kontroli.

**Części:** przyjęcie opakowań, lokowanie na regałach, rezerwacja/kompletacja pod zlecenie, przekazanie do warsztatu, możliwe zwroty i rozliczenie pojemników. Dostęp do informacji ma być możliwy z kontekstu maszyny/zlecenia.

## Inbound — planowany kontekst

Awizacja: dane kierowcy i pojazdu, typ dostawy (maszyny/części), import danych z JSON, API, Excel lub ręcznie, druk etykiety/kodu przy identyfikacji. Dla maszyn: model/typ, numer ramy i dane identyfikacyjne; dla części: pudełka/palety/oversize. Wyjątki mają zawierać opis, blokować normalny proces maszyny do wyjaśnienia, umożliwiać wydruk oświadczenia dla stron oraz przesłanie kontekstu do analizy. Dokładny proces obsługi sporu z przewoźnikiem był określony jako poza zakresem.

## Lokalizacje maszyn i problem dokładności

W jednym obserwowanym zakładzie oznaczenia typu `10-07` wskazują sekcję i alejkę, a słupy są numerowane oddzielnie. Skan lokalizacji obejmuje często tylko sekcję/alejkę, podczas gdy fizyczny słup wpisuje się manualnie. Maszyny parkuje się elastycznie, a nie w stałych pojedynczych miejscach, przez co kopiowanie starych lokalizacji i przeciwległa strona alejki bywają źródłem błędów. Proponowano wizualny podział powierzchni między słupami, ale nie ustalono sztywnego algorytmu slottingu. Przykłady modeli/sekcji (KX/U27, KX80, U008) są danymi przykładowymi konkretnego zakładu.

## Picking (zaobserwowany proces)

Istniejący system skanuje m.in. kod zamówienia maszyny, lokalizację/partię i pozycje towaru; zlecenie trafia do zasobnika pickera części. `TO` oznacza Transfer Order. W projektowanym NeWMS kontekst operatora ma zaczynać się od skanu maszyny (odwrotnie niż wiele obecnych ścieżek), a nie od nawigacji po abstrakcyjnym menu SAP.

## Warsztat

Kierownik decyduje o zwolnieniu do pracy. Możliwe jest częściowe przygotowanie maszyny przy oczekiwaniu na pozostałe części (np. demontaż osłon). Praca może trwać dłużej niż jeden dzień; przerwy należy odróżnić od aktywnego czasu pracy. Pracownik może zgłosić problem. Fizyczna karta pracy pozostaje elementem procesu.

## Handover/Putaway i MOVE_MACHINE

`Putaway` oznacza odstawienie po zakończonej pracy do magazynu lub strefy wysyłki. `MOVE_MACHINE` oznacza wolne przemieszczenie na terenie zakładu, gdy maszyna nie jest blokowana ani w aktywnym procesie pracy. Przy blokadzie mogą istnieć wyjątkowe zlecenia transportowe autoryzowane przez managera — poza aktualnym MVP.

## Kitting i opakowania

Kity i części mogą mieć typ opakowania. Niektóre pojemniki są zwrotne i zbierane pod koniec zmiany; porównanie zwrotów fizycznych z systemowymi pozostaje zamierzeniem przyszłego modułu.
