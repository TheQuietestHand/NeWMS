# Application Layer — katalog przypadków użycia (ACCEPTED)

| Use case | Minimalny input | Reguła / efekt |
|---|---|---|
| CreateWorkOrder | mode, target?, priority, deadline?, assignee?, workstation?, references[], items[] | `CREATE_WORK_ORDER`; status WAITING |
| AssignWorkOrder | work_order_id, worker_id?, workstation_id? | `ASSIGN_WORK_ORDER`; status bez zmian |
| StartWorkOrder | work_order_id | WAITING → IN_PROGRESS; DIRECT interwał, OPERATIONS bez interwału |
| PauseWorkOrder | work_order_id, reason | IN_PROGRESS → PAUSED; kaskada aktywnych Operation |
| ResumeWorkOrder | work_order_id | PAUSED → IN_PROGRESS, bez auto-resume dzieci |
| CompleteWorkOrder | work_order_id | permission zależne od trybu; dla OPERATIONS wszystkie terminalne i ≥1 ukończona |
| CancelWorkOrder | work_order_id, reason? | `CANCEL_WORK_ORDER`; kaskada niedokończonych Operation |
| CreateOperation | work_order_id, name, assignee?, workstation? | rodzic OPERATIONS; terminalny rodzic odrzucany |
| StartOperation | operation_id | rodzic IN_PROGRESS, dziecko WAITING |
| PauseOperation | operation_id | IN_PROGRESS → PAUSED |
| ResumeOperation | operation_id | rodzic IN_PROGRESS, dziecko PAUSED |
| CompleteOperation | operation_id | `COMPLETE_WORK`; nie kończy rodzica |
| CancelOperation | operation_id | `CANCEL_WORK_ORDER` w MVP, do późniejszego przeglądu |
| BlockMachine | machine_id, reason?, issue_id? | `BLOCK_MACHINE`; polityka zakładu, audyt, atomowe Pause |
| ReleaseMachineBlock | block_id | `RELEASE_MACHINE_BLOCK`; audyt i brak auto-resume |

## Kontrakt logiczny

Use case przyjmuje typowaną komendę, `actor_id`, Unit of Work; deduplikacja opiera się o `request_id`. API DTO może używać Pydantic, komenda aplikacyjna może być `@dataclass(frozen=True)`. Nie ustalono jeszcze finalnej postaci ścieżek HTTP ani schematów wszystkich DTO — poniższe są **kodami błędów aplikacyjnych**, a nie umową statusów HTTP:

`NOT_FOUND`, `PERMISSION_DENIED`, `INVALID_STATUS`, `INVALID_EXECUTION_MODE`, `TARGET_BLOCKED`, `VALIDATION_ERROR`, `CONFLICT`.

## Warunki, które muszą pozostać widoczne

- Nie każda komenda jest dozwolona ze wszystkich statusów.
- Przed zmianą Operation waliduje się WorkOrder, ponieważ jest jej agregatem.
- Blokada maszyny ma pierwszeństwo przed standardowym wykonaniem.
- Zaawansowane uprawnienia i kwalifikacje nie mogą być wprowadzane ukradkiem jako niewidoczne warunki MVP.
- Wszystkie odmowy są kontrolowane i nie zostawiają częściowo zmienionych encji.
