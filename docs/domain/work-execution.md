# Work Execution — specyfikacja domenowa (ACCEPTED)

**Źródło rozstrzygnięć:** README v0.5, 2026-10-16. W pierwszej kolejności wdrażany jest DIRECT, potem OPERATIONS.

## Ubiquitous language

- **WorkOrder** — agregat wykonania pracy; `execution_mode=DIRECT|OPERATIONS`.
- **Operation** — pojedynczy element wykonania w rodzicu typu OPERATIONS; child entity agregatu WorkOrder.
- **WorkInterval** — faktyczny przedział aktywnej pracy konkretnej osoby; odrębny od planowanego czasu pracy.
- **WAITING, IN_PROGRESS, PAUSED, COMPLETED, CANCELLED** — wartości ExecutionStatus.
- **OrderReference** — typowany odsyłacz do zlecenia w innym module, **bez zależności wykonania**.

## WorkOrder — Aggregate Root

| Pole | Typ/rola | Uwagi |
|---|---|---|
| id | UUID | identyfikator |
| order_number | string | numer biznesowy |
| execution_mode | DIRECT / OPERATIONS | niezmienny po starcie |
| status | ExecutionStatus | maszyna stanów poniżej |
| target_type, target_id | opcjonalne | obiekt docelowy, np. maszyna |
| priority, deadline | priorytet / opcjonalny termin | bez ustalonej skali priorytetów |
| assigned_worker_id, workstation_id | opcjonalne | nieobowiązkowe do rozpoczęcia |
| related_orders | lista OrderReference | kontekst, nie wymuszają wykonania |
| required_items | lista | bez obowiązkowej integracji Inventory w MVP |
| created_by, created_at | autor i czas | historia |
| started_at | opcjonalny czas | pierwsze rozpoczęcie |
| completed_at, completed_by | opcjonalne | audyt zakończenia |

Nie wprowadzamy w tym modelu `WorkOrderType` ani `order_type_id`. Referencje mogą mieć kategorie PICKING, WORK_DIRECT, WORK_OPERATIONS, TRANSPORT; znaczenie i ewentualna redundancja z `execution_mode` pozostają do doprecyzowania.

## Operation — child entity

`id`, obowiązkowe `work_order_id`, `name`, `status`, opcjonalnie `assigned_worker_id`, `workstation_id`, oraz `created_at`, `started_at?`, `completed_at?`, `completed_by?`.

- Występuje wyłącznie pod rodzicem OPERATIONS.
- Nie jest osobnym agregatem, nawet jeśli `operations` jest osobną tabelą.
- Stan Operation zmieniamy **przez WorkOrder**, np. `work_order.start_operation(operation_id, actor_id)`.
- Nie dublujemy `operation_ids` jako przechowywanej listy w wierszu WorkOrder.
- Odczyt szczegółów może użyć projekcji `WorkOrderDetails` bez ładowania wszystkich dzieci do każdego zapytania.

## WorkInterval

`id`, `work_order_id`, `operation_id?`, `worker_id`, `started_at`, `ended_at?`, `ended_by?`, `end_reason?`.

`end_reason ∈ {PAUSED, COMPLETED, CANCELLED, MACHINE_BLOCK}`; czas w UTC, ustalany po stronie serwera. W DIRECT `operation_id=NULL`; w OPERATIONS interwał dotyczy konkretnej Operation. Przy zakończeniu przez system `ended_by` może być puste, natomiast powód musi pozostać.

**Niezmienniki:** najwyżej jeden otwarty WorkInterval na Worker globalnie; najwyżej jeden otwarty interwał na DIRECT WorkOrder; wiele jednoczesnych interwałów na jednej Operation jest dozwolone, jeżeli dotyczą różnych niepracujących gdzie indziej osób. Roboczogodziny = suma odcinków wszystkich osób; czas kalendarzowy ≠ roboczogodziny.

## DIRECT — przejścia

| Przed | Komenda | Po | Interwał |
|---|---|---|---|
| WAITING | StartWorkOrder | IN_PROGRESS | otwórz |
| WAITING | CancelWorkOrder | CANCELLED | brak |
| IN_PROGRESS | PauseWorkOrder | PAUSED | zamknij: PAUSED |
| IN_PROGRESS | CompleteWorkOrder | COMPLETED | zamknij: COMPLETED |
| IN_PROGRESS | CancelWorkOrder | CANCELLED | zamknij: CANCELLED |
| PAUSED | ResumeWorkOrder | IN_PROGRESS | nowy |
| PAUSED | CancelWorkOrder | CANCELLED | brak otwartego |

COMPLETED i CANCELLED są terminalne: każda próba zmiany cyklu życia → `INVALID_STATUS`. `CompleteWorkOrder` wymaga `COMPLETE_WORK`; kończący manager może nie być wykonawcą — zapisujemy `completed_by`. Przejęcie przez innego pracownika odbywa się po Pause; poprzednie interwały pozostają.

## OPERATIONS — reguły rodzica

1. `StartWorkOrder`: WAITING → IN_PROGRESS, **bez** WorkInterval.
2. `StartOperation` wymaga rodzica IN_PROGRESS i Operation WAITING.
3. Stan dziecka **nigdy automatycznie** nie zmienia stanu rodzica.
4. `PauseWorkOrder`: IN_PROGRESS → PAUSED; aktywne Operation → PAUSED; WAITING i terminalne pozostają bez zmian; zamknij wszystkie otwarte interwały.
5. `ResumeWorkOrder`: PAUSED → IN_PROGRESS; operacje pozostają PAUSED/WAITING, żadnego auto-resume.
6. `CancelWorkOrder`: wszystkie nieterminalne Operation → CANCELLED, terminalne bez zmian; aktywne interwały zamknij.
7. `CompleteWorkOrder`: tylko rodzic IN_PROGRESS; **wszystkie** Operation terminalne (`COMPLETED|CANCELLED`) i **co najmniej jedna** COMPLETED; jawna komenda z `COMPLETE_OPERATIONS_WORK_ORDER`. Zero operacji nie spełnia warunku.

## Operation — przejścia

| Przed | Komenda | Po |
|---|---|---|
| WAITING | StartOperation | IN_PROGRESS |
| WAITING | CancelOperation | CANCELLED |
| IN_PROGRESS | PauseOperation | PAUSED |
| IN_PROGRESS | CompleteOperation | COMPLETED |
| IN_PROGRESS | CancelOperation | CANCELLED |
| PAUSED | ResumeOperation | IN_PROGRESS |
| PAUSED | CancelOperation | CANCELLED |

COMPLETED/CANCELLED → `INVALID_STATUS` dla zmian cyklu życia. `CompleteOperation` nie działa z WAITING lub PAUSED. Start i Resume otwierają interwał wykonawcy; Resume tworzy **nowy** interwał. Pause, Complete, Cancel zamykają wszystkie aktywne interwały tej Operation, również przy wielu współwykonawcach. `CompleteOperation` wymaga `COMPLETE_WORK`. Start/Resume wymagają IN_PROGRESS u rodzica oraz braku blokady targetu. Kaskady rodzica są wyraźnymi wyjątkami do reguły lokalnych komend.

## Invariants (WE-INV)

| ID | Reguła |
|---|---|
| 01 | Gdy WorkOrder ≠ IN_PROGRESS, żadna Operation nie może być IN_PROGRESS. |
| 02 | Operation ma dokładnie jednego rodzica w trybie OPERATIONS. |
| 03 | DIRECT nie ma Operation i ma co najwyżej jeden otwarty WorkInterval. |
| 04 | Worker ma co najwyżej jeden globalnie otwarty WorkInterval. |
| 05 | Jedna Operation może mieć wielu pracujących równolegle ludzi. |
| 06 | Terminalna Operation nie wraca do pracy. |
| 07 | Ukończenie OPERATIONS wymaga wszystkich dzieci terminalnych, ≥1 COMPLETED; brak auto-complete rodzica. |
| 08 | Po PauseWorkOrder wszystkie powiązane aktywne WorkIntervals są zamknięte. |
| 09 | Maszyna ma najwyżej jeden aktywny MachineBlock. |
| 10 | Zablokowana maszyna nie ma normalnie wykonywanej pracy; zakończenie pracy przy blokadzie jest zabronione w MVP. |
| 11 | ReleaseMachineBlock nie wznawia prac. |
| 12 | Blokada i zatrzymanie powiązanych prac są atomowe. |

## Uwaga o granicach

Dopuszczanie nowych Operation po rozpoczęciu rodzica, dokładny model powodu Pause i uprawnienie CancelOperation są **OPEN** — patrz [rejestr](../decisions/open-questions.md). Nie implementować arbitralnej polityki.
