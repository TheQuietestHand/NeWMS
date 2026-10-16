# Zlecenia, referencje i granice przepływów

## Rozróżnienie poziomów — WAŻNE

Wcześniejsze rozmowy o całej platformie obejmowały `WarehouseOrder`, `InboundOrder`, `OutboundOrder`, `WorkshopOrder`, `TransportOrder`, `PickingOrder`. To **CONTEXT** dla docelowej platformy. Aktualny MVP skupia się na `WorkOrder` (DIRECT/OPERATIONS) i `Operation` — nie wolno utożsamiać tych nazw ani dodawać nieuzgodnionej hierarchii dziedziczenia w modelu Work Execution.

## Charakterystyka docelowa (CONTEXT)

- `WarehouseOrder`: wspólny kontekst fizycznego przepływu; może inicjować inne zlecenia lub kierować propozycje do zatwierdzenia.
- `InboundOrder`: przyjęcie maszyny lub części, w tym dane dostawy i wyjątki.
- `OutboundOrder`: wydanie i wysyłka.
- `WorkshopOrder`: zadanie przygotowania / montażu dla maszyny.
- `TransportOrder`: autoryzowane przemieszczanie; może mieć znaczenie przy blokadach.
- `PickingOrder`: kompletacja materiałów dla zadania/maszyny.

We wcześniejszych założeniach zlecenia miały identyfikator, datę utworzenia, termin, priorytet, wykonawcę, status wykonania i wyliczany status terminu oraz powiązania rodzic–dziecko; zakres wspólnej abstrakcji tych zleceń **nie jest zatwierdzonym modelem Work Execution v0.5**.

## OrderReference w Work Execution — ACCEPTED

`related_orders: list[OrderReference]` przechowuje odsyłacze do powiązań typu PICKING, WORK_DIRECT, WORK_OPERATIONS, TRANSPORT. Same referencje **nie** tworzą warunków poprzedzających start pracy i nie oznaczają hierarchii wykonania. Dokładna normalizacja typów tych referencji pozostaje OPEN.

## Docelowe zależności — bez przedwczesnego sprzężenia

Praca może zacząć się bez modułu Picking. `required_items[]` pozostają w modelu WorkOrder jako dane kontekstowe bez wymuszania kompletacji. Automatyczne tworzenie zleceń pickingowych i szczegółowe zależności części od pracy są poza MVP.
