# ADR-0003 — Jawne rozpoczęcie rodzica OPERATIONS

**Status:** Accepted  
**Stan ustaleń:** 2026-10-16

## Kontekst

Nie chcemy niejawnej zmiany statusu rodzica z komend dzieci.

## Decyzja

StartWorkOrder musi poprzedzać StartOperation; dzieci nie zmieniają statusu rodzica automatycznie.

## Konsekwencje

Przejrzyste stany i jawna odpowiedzialność za CompleteWorkOrder.
