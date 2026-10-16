# ADR-0002 — Operation jako child entity WorkOrder

**Status:** Accepted (2026-10-16; zastępuje starszą propozycję osobnego Aggregate Root)  
**Stan ustaleń:** 2026-10-16

## Kontekst

Start/Resume Operation zależą od rodzica, a Pause/Cancel rodzica wymagają atomowych kaskad. Przepustowość zmian pojedynczych operacji nie jest obecnie priorytetem.

## Decyzja

WorkOrder jest Aggregate Root; Operation jest child entity przechowywanym w osobnej tabeli `operations` z wymaganym `work_order_id`; zmiany przez rodzica.

## Konsekwencje

Blokowanie rodzica może serializować równoległe zmiany dzieci, ale upraszcza ochronę niezmienników. Odczyty mogą być projekcjami.
