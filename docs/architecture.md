# Architektura — RECOMMENDED / częściowo ACCEPTED

## Styl

Modularny monolit, pragmatyczne DDD. Warstwy: **Domain → Application → Infrastructure → API** (zależności kodu: warstwy zewnętrzne zależą od wewnętrznych, nie odwrotnie). Logika domenowa nie importuje FastAPI, Pydantic API DTO ani SQLAlchemy.

Domena definiuje encje, wartości, maszyny stanów i niezmienniki. Application uruchamia przypadki użycia, autoryzację, koordynację między modułami i Unit of Work. Infrastructure implementuje repozytoria/transakcje i integracje. API mapuje żądania/odpowiedzi oraz błędy.

## Granice modułów

| Moduł | Odpowiedzialność | Stan |
|---|---|---|
| Work Execution | WorkOrder, Operation, WorkInterval | MVP |
| Assets/Machines | Machine i MachineBlock | MVP dla blokad |
| Workforce | Worker, permission, qualification | minimalne dane w MVP, szersze zarządzanie później |
| Inventory | Item, StockPosition, InventoryTransaction, StockReservation, ExpectedSupply | kontekst / później |
| Picking/KitCart | kompletacja, pojemniki, obieg części | kontekst / później |
| Transport | transport i zlecenia przemieszczania | kontekst / później |
| Planning | kolejki i przydziały | kontekst / później |
| Inbound/Outbound | przyjęcia / wysyłki | kontekst / później |
| Reporting / Issues | raportowanie / zgłoszenia problemów | kontekst / później |

**Kluczowa granica:** Operation jest **encją potomną WorkOrder**, nie odrębnym Aggregate Root. Assets nie importuje modelu wewnętrznego Work Execution — integruje go koordynator aplikacyjny za pomocą portów.

## Technologia — rekomendacja z README v0.5

Python 3.13, FastAPI, Pydantic v2, PostgreSQL, SQLAlchemy 2.x, Alembic, pytest, Behave, Docker Compose, uv, Ruff, Pyright, GitHub Actions. Na początku implementacja synchroniczna. Bez wymogu Kafka, Redis, Celery, Kubernetes ani mikroserwisów w MVP. Ostateczną kompatybilność wersji weryfikuje się przy instalacji.

## Sposób implementacji

Application use case jako funkcja przyjmująca komendę, `actor_id` i `UnitOfWork`. Komendy mogą być immutable dataclasses. `StartWorkOrderCommand` to struktura danych, nie klasa wykonująca logikę. Reguły domenowe realizuje model; adapter API nie decyduje, czy przejście stanu jest dozwolone.

## Układ repo (propozycja z README v0.5)

```text
src/warehouse_platform/
  work_execution/
    domain/{models.py,enums.py,errors.py}
    application/{commands.py,use_cases.py,ports.py}
    infrastructure/{repositories.py,mappings.py}
    api/routes.py
  machines/
  workforce/
  shared/
migrations/
tests/{unit,integration,features}/
docs/{architecture.md,requirements.md,domain/,adr/}
```

Nie wymaga się pustych modułów na zapas.
