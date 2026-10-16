# Strategia testowania i kryteria ukończenia

## Warstwy

**Unit / pytest:** przejścia stanów i niezmienniki bez ORM/bazy. **Integration / pytest + PostgreSQL:** repozytoria, UoW, migracje, rollback, constraints, wyścigi, idempotency. **Acceptance / Behave + Gherkin:** scenariusze procesowe opisujące zachowanie niezależnie od adaptera HTTP.

Pliki w `tests/features` to **szkice wykonywalnej specyfikacji**, ale bez napisanych step definitions nie są uruchamialnymi testami. Tagi `@mvp` / `@post_mvp` rozdzielają zakres.

## Priorytet testowy

1. Create/Start/Pause/Resume/Complete/Cancel DIRECT; brak niejawnego przypisania.
2. Historia niepokrywających się interwałów; przekazanie pracy po Pause; jeden otwarty interwał per Worker.
3. OPERATIONS: jawny Start rodzica, niezależność statusów, równoległe osoby na jednej Operation, Pause/Cancel kaskadowe, brak auto-resume.
4. Zakończenie rodzica wymaga wszystkich terminalnych i minimum jednej COMPLETED; zero dzieci nie przechodzi.
5. BlockMachine: jedna aktywna blokada, powtarzalne request_id, pełny audyt, atomowe zatrzymanie, zakaz standardowego Complete przy blokadzie.
6. Równoległe Start/Block, Pause/StartOperation; rollback w środku kaskady.
7. Próby nieprawidłowych przejść bez częściowych zapisów.

## Definition of Done — DIRECT MVP (z README v0.5)

- Poprawne przejścia stanów DIRECT.
- Start bez przypisanego Worker i Workstation.
- WorkInterval mierzy aktywną pracę; DIRECT nie ma nakładających się interwałów.
- Complete wymaga `COMPLETE_WORK`, zapisuje aktora.
- Błędne przejścia kończą się kontrolowanym błędem i bez częściowych zmian.
- Unit/integration lokalnie i CI, Behave dla DIRECT.
- Migracje uruchamiają się na pustej bazie; instrukcje startu testów znajdują się w repo README.

## Pierwszy sprint — kolejność z README v0.5

`uv init --package warehouse-platform` → zależności pytest/ruff/pyright/behave → domena DIRECT → unit tests → PostgreSQL + SQLAlchemy + Alembic → repo/UoW/use cases → testy integracyjne → Behave → cienkie FastAPI → OPERATIONS → MachineBlock i testy wyścigów.
