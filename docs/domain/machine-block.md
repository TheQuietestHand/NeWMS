# MachineBlock — blokady maszyn (ACCEPTED)

## Semantyka

Blokada oznacza zakaz kontynuacji **normalnego** procesu pracy na maszynie bez upoważnienia. Nie jest równoznaczna z fizycznym zakazem każdego transportu w przyszłych specjalnych procedurach; szczegóły wyjątków transportowych są **POST-MVP**.

## Reguły

- Jedna aktywna blokada na maszynę: rekord aktywny ma `released_at IS NULL`; częściowy indeks unikalny w PostgreSQL.
- Nowe niezależne `BlockMachine` przy istniejącej blokadzie → `CONFLICT`.
- Ponowienie identycznego żądania z tym samym `request_id` musi zwrócić wcześniejszy rezultat bez powtórnego działania.
- W zakładzie konfigurowalne `require_reason` (domyślnie `true`), `require_issue` (domyślnie `false`). Powód lub Issue mogą być opcjonalne zgodnie z polityką; audyt nigdy.
- `ReportIssue` nie blokuje automatycznie maszyny.
- `BLOCK_MACHINE` i `RELEASE_MACHINE_BLOCK` to różne, konfigurowalne permissions; nie należy kodować ich wyłącznie dla roli managera.
- Utworzenie blokady, zapis historii i pauza wszystkich aktywnych powiązanych prac to jedna transakcja.
- Zdjęcie blokady zapisuje kto/kiedy/co i **nigdy nie wznawia** WorkOrder, Operation ani WorkInterval.

## Efekt BlockMachine

| Obiekt | Przed | Po |
|---|---|---|
| DIRECT WorkOrder | IN_PROGRESS | PAUSED; zamknij WorkInterval |
| DIRECT WorkOrder | WAITING | WAITING |
| OPERATIONS rodzic | IN_PROGRESS | PAUSED |
| Operation | IN_PROGRESS | PAUSED; zamknij wszystkie jej WorkIntervals |
| Operation | WAITING | WAITING |
| Praca terminalna | COMPLETED / CANCELLED | bez zmian |

Historia wymuszonej pauzy zachowuje `reason=MACHINE_BLOCK` i `block_id`; WorkInterval ma `end_reason=MACHINE_BLOCK`. `ended_by` może wskazać osobę blokującą. BlockMachine działa poprzez koordynator Application Layer ponad Assets i Work Execution, a nie bezpośredni import wewnętrznych encji pomiędzy domenami.

## Ochrona przed wyścigami

Stała kolejność blokad: **Machine → WorkOrder → Operation**. BlockMachine blokuje Machine wyłącznie, potem powiązane WorkOrders deterministycznie. Start, Resume i standardowe Complete związane z maszyną pobierają wcześniej współdzieloną blokadę Machine; po uzyskaniu blokad ponawiają walidację. Szczegóły wyszukiwania powiązanych WorkOrders pozostają OPEN.

## Zabronione w MVP

Przy aktywnej blokadzie standardowe `StartWorkOrder`, `ResumeWorkOrder`, `StartOperation`, `ResumeOperation`, `CompleteWorkOrder`, `CompleteOperation` dotyczące tej maszyny nie są dozwolone (`TARGET_BLOCKED`). Zatrzymanie przed potwierdzeniem ukończenia jest celowe.

## POST-MVP — zatwierdzona potrzeba, nie projekt techniczny

- **BR-BLOCK-04:** autoryzowane prace naprawcze przy utrzymanej blokadzie (mechanizm identyfikacji przyszłego zlecenia jeszcze niewybrany; nie dodawać przedwcześnie `WorkOrderType`, `is_corrective`, `resolves_block_id`).
- Robocze `COMPLETE_BLOCKED_WORK` — administracyjne zamknięcie zablokowanej pracy, **nie** jest częścią Permission v0.1.
- Specjalne transporty zablokowanych maszyn — reguły autoryzacji do opracowania.
