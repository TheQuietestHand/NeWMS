# Mapa dokumentacji

Dokumentacja jest podzielona według odpowiedzialności: wymagania → kontekst operacyjny → model domenowy → interakcje aplikacyjne → infrastruktura/testy → historia decyzji. Ten układ rozbudowuje proponowane wcześniej `docs/architecture.md`, `docs/requirements.md`, `docs/domain/work-execution.md` i `docs/adr/` bez zmiany ich znaczenia.

## Kolejność czytania przy implementacji

1. [Requirements](requirements.md) — co i dlaczego budujemy.
2. [Architecture](architecture.md) — granice modułów i warstw.
3. [Work Execution](domain/work-execution.md) — agregaty i reguły.
4. [MachineBlock](domain/machine-block.md) — wpływ blokad na wykonanie.
5. [Use cases](architecture/use-cases.md) — operacje systemu.
6. [Persistence & concurrency](architecture/persistence-and-concurrency.md) — gwarancje spójności.
7. [Testing](testing/strategy.md) i [Gherkin](../tests/features/) — testy akceptacyjne.
8. [ADR](adr/) i [Open questions](decisions/open-questions.md) — uzasadnienie oraz niewiadome.

## Hierarchia źródeł

- Najnowsze zatwierdzone decyzje z 2026-10-16 oraz README v0.5: wiążące dla Work Execution i MachineBlock.
- Wcześniejsze ustalenia biznesowe: zachowane jako kontekst dla Inventory, Picking, Inbound, Outbound, Planning i interfejsów.
- Starsze BDD v0.2 i PDF, przywoływane w README v0.5: nie były dostępne w pełnej treści podczas budowy tej paczki; nie rekonstruowano ich słowo w słowo.
- Pytania otwarte mają własny rejestr i nie są rozstrzygane domysłami.

## Aktualna kolejność MVP

1. DIRECT WorkOrder.
2. OPERATIONS WorkOrder / Operation.
3. MachineBlock połączony atomowo z Work Execution.
4. Integracje z resztą domeny w następnych iteracjach.
