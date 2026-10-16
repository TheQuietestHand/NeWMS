# ADR-0001 — Modularny monolit

**Status:** Proposed / recommended  
**Stan ustaleń:** 2026-10-16

## Kontekst

Wiele modułów rozwijanych w pojedynczym projekcie; spójne transakcje między Assets i Work Execution.

## Decyzja

Jeden proces, wyraźne granice modułów i warstw DDD.

## Konsekwencje

Łatwiejsze testy i transakcje, potrzeba utrzymania granic importów.
