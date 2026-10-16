# Otwarte decyzje, ryzyka i granice poznania

**OPEN nie oznacza TODO do dowolnego zaprojektowania bez uzgodnienia.** Rejestr jest świadomym zabezpieczeniem przed dopisywaniem nieustalonych wymagań.

| ID | Pytanie / ryzyko | Obecnie ustalone |
|---|---|---|
| O-01 | Osobne permission dla `CancelOperation`? | MVP korzysta z `CANCEL_WORK_ORDER`; do przeglądu przy realnym use case. |
| O-02 | OPERATIONS z 0 Operation | Nie może się zakończyć przez warunek ≥1 COMPLETED; test obowiązkowy. |
| O-03 | Dodawanie Operation do rozpoczętego rodzica | Rodzic terminalny → INVALID_STATUS; reszta reguł nieustalona. |
| O-04 | Zidentyfikowanie wszystkich WorkOrders powiązanych z Machine | Wymagana atomowość blokady; porty i selekcja do projektu. |
| O-05 | `PauseReason` i historia kolejnych pauz | Powód wymagany w use case; dokładny model historii do dopracowania. |
| O-06 | Korekta danych i ręczna ingerencja w historię | Poza MVP. |
| O-07 | Prace naprawcze przy aktywnej blokadzie | BR-BLOCK-04 post-MVP; nie wybieramy teraz flag ani dodatkowego typu zlecenia. |
| O-08 | Dezaktywacja Worker | `active` i `deactivated_at` zatwierdzone; przypadki użycia później. |
| O-09 | Typy OrderReference a execution_mode | Uniknąć zbędnej duplikacji, schemat nieustalony. |
| O-10 | Constraint: jeden DIRECT interwał na WorkOrder | Wymóg ustalony, fizyczne DB enforcement do projektu. |
| O-11 | Durable request_id | Unikalność z uwzględnieniem aktora/komendy; format i ponowienia do ustalenia. |
| O-12 | Szczegółowe API HTTP | Nie zatwierdzono tras, DTO ani HTTP mapping. |
| O-13 | Inventory/Picking/Transport i inne moduły | Ustalono kontekst operacyjny, nie kompletną specyfikację implementacyjną. |
| O-14 | Kwalifikacje przy rozpoczęciu pracy | Post-MVP; brak walidacji w obecnym MVP. |
| O-15 | Kontrolowane Complete podczas blokady | Przyszłe robocze `COMPLETE_BLOCKED_WORK`. |
| O-16 | Operacyjny wyjątek transportu blokowanej maszyny | Przyszła autoryzowana procedura. |
| O-17 | `STALLED` | Późniejszy wyliczany wskaźnik, nie ExecutionStatus. |
| O-18 | Skalowanie i hosting | Nie ustalono SLA, deploymentu produkcyjnego, polityki retencji. |

## Rozbieżność zakresów historycznych

Starszy kontekst opisywał szeroką rodzinę zleceń (WarehouseOrder / PickingOrder itd.). Obecny Work Execution NIE dodaje do `WorkOrder` pola `WorkOrderType`. Nie przenosimy automatycznie statusów czy dziedziczenia między tymi poziomami.

Źródła starszych PDF i BDD v0.2 były przywołane w README v0.5, ale nie było ich pełnej zawartości dostępnej do rekonstrukcji. Szczegółowe wymagania z nich należy weryfikować, zanim trafią do formalnej specyfikacji.
