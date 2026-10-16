# Inventory — kontekst przyszłego modułu (CONTEXT)

> Nie jest to zatwierdzona specyfikacja implementacyjna Inventory. Rozmowy i README v0.5 potwierdzają nazwy koncepcji i problemy operacyjne, ale nie pełne atrybuty, API, politykę rezerwacji ani księgowania stanów.

## Pojęcia z planowanej domeny

`Item`, `StockPosition`, `InventoryTransaction`, `StockReservation`, `ExpectedSupply`. W procesie obsługiwane są maszyny oraz części; części mogą występować jako pozycje drobnicowe w pudełkach, workach, organizerach, na paletach lub jako ładunek ponadgabarytowy. Fizyczny typ opakowania i samą zawartość należy odróżniać w modelowaniu przyszłego przepływu.

## Zaobserwowane problemy

- Mechanicy nie mają pełnego dostępu do stanu magazynowego; dane części są w izolowanym rozwiązaniu i częściowo przez API.
- Części powiązane są ze zleceniami i maszynami; kompletacja jest organizowana poprzez picking.
- Skanery w istniejącym rozwiązaniu potrafią wyświetlać mało zrozumiałe błędy.
- Przewiduje się możliwość korekty błędów stanów z audytem, w tym permission `REVERSE_INVENTORY_TRANSACTION`, lecz dokładny proces korekt nie jest ustalony.

## Brakujące decyzje — OPEN

Jednostki miary, identyfikatory Item, granice transakcji, reguły rezerwacji, obsługa zamienników, zwroty, kity, ujemne stany, ewidencja opakowań zwrotnych, konkurencyjne pobrania, numeracja lokalizacji i struktura API nie są dostatecznie uzgodnione, by zamieniać je w niezmienniki implementacyjne.
