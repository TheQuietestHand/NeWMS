# NeWMS — dokumentacja projektowa

**Stan na:** 2026-10-16 · **Status:** dokumentacja projektowa, nie opis działającego systemu · **Język:** polski.

NeWMS (Warehouse Operations Platform) jest projektowanym, modułowym systemem do koordynowania przepływu maszyn ciężkich, części i pracy w magazynie oraz warsztacie.

**Zasada źródeł:** aktualna uzgodniona specyfikacja Work Execution / MachineBlock (README v0.5 z 2026-10-16) ma pierwszeństwo przed wcześniejszymi szkicami. Szersze ustalenia z rozmów o procesach magazynowych są opisane oddzielnie jako kontekst. Nie zakładamy, że funkcje opisywane w dokumentach zostały zaimplementowane.

## Nawigacja

| Plik | Zawartość |
|---|---|
| [docs/index.md](docs/index.md) | Mapa dokumentacji i statusów |
| [docs/requirements.md](docs/requirements.md) | Cele, wymagania i granice MVP |
| [docs/architecture.md](docs/architecture.md) | Architektura aplikacji i modułów |
| [docs/domain/work-execution.md](docs/domain/work-execution.md) | Specyfikacja Work Execution |
| [docs/domain/machine-block.md](docs/domain/machine-block.md) | Specyfikacja blokad maszyn |
| [docs/domain/workforce.md](docs/domain/workforce.md) | Pracownicy, uprawnienia, kwalifikacje |
| [docs/domain/inventory.md](docs/domain/inventory.md) | Kontekst Inventory i części |
| [docs/domain/orders-and-flows.md](docs/domain/orders-and-flows.md) | Rodzaje zleceń i integracje |
| [docs/processes/warehouse.md](docs/processes/warehouse.md) | Zaobserwowane procesy magazynowe |
| [docs/processes/interfaces.md](docs/processes/interfaces.md) | Założenia UX skanera i web |
| [docs/architecture/persistence-and-concurrency.md](docs/architecture/persistence-and-concurrency.md) | Transakcje i baza danych |
| [docs/architecture/use-cases.md](docs/architecture/use-cases.md) | Przypadki użycia i błędy |
| [backend/testing/strategy.md](backend/testing/strategy.md) | Testy, BDD, DoD |
| [docs/decisions/open-questions.md](docs/decisions/open-questions.md) | Pytania nierozstrzygnięte |
| [docs/adr/](docs/adr/) | Decyzje architektoniczne |
| [tests/features/](tests/features/) | Scenariusze Gherkin (bez implementacji kroków) |

## Legendy

- **ACCEPTED** — zatwierdzone ustalenie.
- **RECOMMENDED** — uzgodniony kierunek / rekomendacja techniczna, niekoniecznie ostateczna decyzja wdrożeniowa.
- **CONTEXT** — obserwacja procesów lub wcześniejszy zakres produktu, niewymagany w bieżącym MVP.
- **OPEN** — wymaga kolejnej decyzji; nie wolno uznać za zaimplementowane wymaganie.
- **POST-MVP** — ustalony kierunek przyszłej funkcji, lecz poza bieżącym MVP.

Tagi `@mvp` / `@post_mvp` w plikach `.feature` określają zakres scenariuszy; nie są dowodem, że testy mają już napisane step definitions.
