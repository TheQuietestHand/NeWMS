# Persistence, współbieżność i transakcje (ACCEPTED / OPEN w szczegółach)

## Granica transakcji

Komenda biznesowa jest atomowa. Dotyczy to zwłaszcza kaskady `PauseWorkOrder`, `CancelWorkOrder` oraz `BlockMachine` (blokada Assets i zatrzymanie pracy Work Execution w tej samej transakcji i bazie). Zdarzenia asynchroniczne nie zastępują tych gwarancji w MVP.

## Kolejność blokad

1. Dla celu Machine: uzyskaj blokadę wiersza Machine (współdzieloną przy standardowej pracy; wyłączną podczas BlockMachine).
2. Uzyskaj blokadę wiersza WorkOrder (`SELECT ... FOR UPDATE`) — powiązane zlecenia blokuj w deterministycznej kolejności, np. po ID.
3. Dopiero potem czytaj/zmieniaj powiązane Operation; waliduj warunki ponownie w transakcji.

Przy komendzie zawierającej tylko `operation_id` wykonaj wstępny nieblokujący odczyt niezmiennego `work_order_id`, następnie zablokuj rodzica, wczytaj i zweryfikuj Operation ponownie. Nie używaj problematycznego `joinedload` nullable relacji w zapytaniu FOR UPDATE; rodzica blokuj oddzielnym zapytaniem. `version` jest opcjonalnym uzupełnieniem, nie zamiennikiem blokady.

## Ograniczenia PostgreSQL

```sql
-- Jeden otwarty interwał na pracownika globalnie.
CREATE UNIQUE INDEX uq_open_interval_per_worker
  ON work_intervals(worker_id)
  WHERE ended_at IS NULL;

-- Jedna aktywna blokada na maszynę.
CREATE UNIQUE INDEX uq_active_machine_block
  ON machine_blocks(machine_id)
  WHERE released_at IS NULL;
```

**DIRECT:** dodatkowo najwyżej jeden otwarty interwał na WorkOrder. Dokładny schemat constraintu pozostaje OPEN: częściowy indeks na `operation_id IS NULL` nie musi dowodzić DIRECT bez trwałej informacji o trybie; sugerowany był np. `direct_work_order_id` lub `interval_scope`, ale niczego tu nie zatwierdzamy. Wymagana jest ochrona w DB lub odpowiednia atomowa blokada, nie sam `if` w Pythonie.

## Idempotency / request_id

Ponowienie identycznej komendy ma nie duplikować efektów. Klucz trwałej deduplikacji powinien rozróżniać aktora i typ komendy; dokładny schemat, okres przechowywania i polityka odpowiedzi są OPEN. Dla `BlockMachine` identyczne ponowienie daje poprzedni wynik; niezależne żądanie przy aktywnej blokadzie daje CONFLICT.

## Timestamps, historia, rollback

Znaczniki czasu są timezone-aware UTC z serwera. `completed_by`, przedziały pracy i historia blokad pozostają dostępne po zakończeniu. Wyjątek w trakcie kaskady powoduje rollback wszystkich jej zmian. Testy integracyjne mają uruchamiać równoległe transakcje na **prawdziwym PostgreSQL**.

## Otwarte kwestie techniczne

Mapowanie wszystkich WorkOrders do MachineBlock; locking szczególnych wielocelowych transakcji; definicja indeksu dla DIRECT; fizyczny schemat historii pauz; trwały klucz idempotencyjny i struktura pełnej historii zmian. Zobacz [Open questions](../decisions/open-questions.md).
