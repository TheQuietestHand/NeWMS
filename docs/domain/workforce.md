# Workforce, permissions i kwalifikacje

## Worker — ustalony minimalny model

Worker: identyfikator, nazwa, `worker_type: WORKER|MANAGER`, `permissions[]`, `qualifications[]`, `active: bool`, `deactivated_at: datetime | None`. Niezmiennik: aktywny → `deactivated_at=None`; nieaktywny → data dezaktywacji. Nie usuwamy fizycznie Worker z historią WorkIntervals. Proces dezaktywacji jest poza MVP; pola pozostają w modelu.

Manager ma domyślnie możliwości pracownika oraz dodatkowe uprawnienia, ale konfiguracja permission ma mieć pierwszeństwo nad sztywnym warunkiem `is_manager`.

## Permission v0.1 — dokładny ustalony katalog

```python
class Permission(Enum):
    CREATE_WORK_ORDER = "CREATE_WORK_ORDER"
    ASSIGN_WORK_ORDER = "ASSIGN_WORK_ORDER"
    CANCEL_WORK_ORDER = "CANCEL_WORK_ORDER"
    COMPLETE_WORK = "COMPLETE_WORK"
    COMPLETE_OPERATIONS_WORK_ORDER = "COMPLETE_OPERATIONS_WORK_ORDER"
    BLOCK_MACHINE = "BLOCK_MACHINE"
    RELEASE_MACHINE_BLOCK = "RELEASE_MACHINE_BLOCK"
    MANAGE_PLANNING = "MANAGE_PLANNING"
    CREATE_PICKING_ORDER = "CREATE_PICKING_ORDER"
    CREATE_TRANSPORT_ORDER = "CREATE_TRANSPORT_ORDER"
    REVERSE_INVENTORY_TRANSACTION = "REVERSE_INVENTORY_TRANSACTION"
    MANAGE_WORKERS = "MANAGE_WORKERS"
    MANAGE_PERMISSIONS = "MANAGE_PERMISSIONS"
    MANAGE_QUALIFICATIONS = "MANAGE_QUALIFICATIONS"
```

`COMPLETE_WORK` upoważnia do kończenia DIRECT WorkOrder oraz pojedynczych Operation. `COMPLETE_OPERATIONS_WORK_ORDER` dotyczy zakończenia rodzica w OPERATIONS. `CancelOperation` używa w MVP `CANCEL_WORK_ORDER` — to tymczasowe rozstrzygnięcie podlegające ponownej ocenie.

Podstawowe Start/Pause/Resume, ReportIssue i ConfirmPick są dostępne pracownikowi zgodnie z regułami domenowymi; bez osobnego permission v0.1 dla każdej akcji. **Permission ≠ Qualification** — uprawnienie w systemie i umiejętność wykonania fizycznej pracy to różne zagadnienia.

## Kwalifikacje — CONTEXT / POST-MVP

Planowane zaznaczanie kwalifikacji dla inbound, outbound, warsztatu, lakierni, spawania, obsługi regałów i określonych modeli maszyn. Montaż powertilt w różnych modelach (np. KX27 i KX80) może wymagać odmiennych kompetencji. W przyszłości możliwe szkolenia i reguły automatycznych przydziałów. **Sprawdzanie kwalifikacji przy StartWorkOrder/StartOperation jest poza aktualnym MVP.**

## Workstation

Stanowisko pracy może mieć `devices[]` (skanery/tablety) i `equipment[]`. Przypisanie/skanowanie Workstation nie jest obowiązkowe do rozpoczęcia pracy; brak automatycznego przydziału wykonawcy przy starcie.
