# Wymagania biznesowe i zakres

## Cel produktu — CONTEXT / ACCEPTED

NeWMS ma ułatwiać pracę w magazynie maszyn ciężkich (koparki, ciągniki) i części: ograniczać skakanie między odrębnymi systemami, ułatwiać odnajdywanie kontekstu maszyny, zlecenia i części, wspierać koordynację działów i poprawiać ergonomię codziennych czynności.

Istotne założenia: prosta obsługa skanera Android (mały ekran, krótkie komunikaty, duże przyciski); rozbudowany web dla kierownika i pracownika; zachowanie papierowej karty jako fizycznego tokenu procesu; możliwość wdrożenia w różnych zakładach bez zaszywania zasad jednego magazynu na stałe.

## Zakres bieżącego MVP — ACCEPTED

| Kolejność | Moduł | Zakres |
|---|---|---|
| 1 | Work Execution: DIRECT | cykl życia WorkOrder, WorkInterval, aktorzy, zakończenie i audyt |
| 2 | Work Execution: OPERATIONS | podoperacje i równoległa praca, kaskady, spójność agregatu |
| 3 | MachineBlock | jedna blokada aktywna, audyt, atomowe zatrzymanie prac, brak auto-resume |
| 4 | Integracje | stopniowo, po ustabilizowaniu powyższych elementów |

**Poza obecnym MVP:** pełne sprawdzanie kwalifikacji dla modeli maszyn, zaawansowane Planning, automatyczne tworzenie PickingOrder, pełny Issue workflow, rozliczanie materiałów, `STALLED`, naprawy podczas blokady, kontrolowane zamykanie pracy podczas blokady, rozbudowana dezaktywacja kont.

## Zasady biznesowe

- Start pracy nie wymaga wstępnego przypisania pracownika ani stanowiska; rozpoczęcie nie przypisuje automatycznie pracownika.
- Pracownik może mieć tylko jeden otwarty interwał czasu pracy w całym systemie.
- DIRECT ma najwyżej jeden otwarty interwał na zlecenie; OPERATIONS dopuszcza wiele osób równocześnie na jednej Operation.
- Operacje nie kończą automatycznie swojego WorkOrder.
- Maszyna z aktywną blokadą nie dopuszcza standardowego startu, wznowienia ani zakończenia związanej pracy.
- Zdjęcie blokady nie uruchamia automatycznie niczego.
- Uprawnienia systemowe i kwalifikacje zawodowe są odrębne.

## Wymagania jakościowe — kierunek implementacji

Priorytetem jest spójność stanów i czytelne reguły domenowe, nawet kosztem przepustowości równoległych zapisów. Praca musi być audytowalna, zmiany atomowe, a ponowienia `request_id` nie mogą wywoływać podwójnego skutku. Testy obejmują domenę, PostgreSQL i scenariusze Behave.

Dokładne SLA, budżety opóźnień, liczebność instalacji, zasady bezpieczeństwa aplikacji i hosting pozostają **OPEN**.
