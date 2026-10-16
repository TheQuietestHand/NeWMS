# ADR-0006 — Atomowe blokowanie maszyny i zatrzymanie pracy

**Status:** Accepted (zasada; porty i selekcja OPEN)  
**Stan ustaleń:** 2026-10-16

## Kontekst

Blokada nie może współistnieć z normalnie aktywną pracą na maszynie.

## Decyzja

Application coordinator w jednej transakcji blokuje Machine i pauzuje powiązane WorkOrders/Operations; porządek Machine→WorkOrder→Operation.

## Konsekwencje

Brak eventual consistency w MVP; potrzebne deterministyczne locking i ponowna walidacja po blokadach.
