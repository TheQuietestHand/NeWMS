from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal, Self
from uuid import UUID

from newms.modules.work_execution.domain.enums import (
    ExecutionMode,
    ExecutionStatus,
    IntervalEndReason,
    OrderReferenceCategory,
    TargetType,
)
from newms.modules.work_execution.domain.errors import (
    InvalidExecutionModeError,
    InvalidStatusError,
    OperationNotFoundError,
    WorkExecutionError,
)

type _Command = Literal["start", "pause", "resume", "complete", "cancel"]

# Statusy, z których wolno wykonać daną komendę. Kluczem jest komenda, a nie status docelowy:
# Start i Resume prowadzą do IN_PROGRESS, ale z różnych stanów. Wspólne dla WorkOrder i Operation.
_ALLOWED_FROM: dict[_Command, frozenset[ExecutionStatus]] = {
    "start": frozenset({ExecutionStatus.WAITING}),
    "pause": frozenset({ExecutionStatus.IN_PROGRESS}),
    "resume": frozenset({ExecutionStatus.PAUSED}),
    "complete": frozenset({ExecutionStatus.IN_PROGRESS}),
    "cancel": frozenset(
        {ExecutionStatus.WAITING, ExecutionStatus.IN_PROGRESS, ExecutionStatus.PAUSED}
    ),
}


def _assert_can(status: ExecutionStatus, command: _Command, subject: str) -> None:
    """Wspólna walidacja (status, komenda) dla WorkOrder i Operation."""

    if status not in _ALLOWED_FROM[command]:
        raise InvalidStatusError(f"{subject}: komenda {command} niedozwolona w statusie {status}")


@dataclass(frozen=True, slots=True)
class OrderReference:
    """Odsyłacz kontekstowy do zlecenia w innym module; nie tworzy zależności wykonania."""

    category: OrderReferenceCategory
    order_id: UUID


@dataclass(frozen=True, slots=True)
class RequiredItem:
    """Dane kontekstowe bez integracji z Inventory w MVP.

    Identyfikatory Item i jednostki miary są OPEN, stąd luźny `item_ref`.
    """

    item_ref: str
    quantity: Decimal


@dataclass(kw_only=True)
class WorkInterval:
    """Faktyczny przedział aktywnej pracy jednej osoby. Czasy w UTC, ustalane przez serwer."""

    id: UUID
    work_order_id: UUID
    operation_id: UUID | None  # None dla DIRECT
    worker_id: UUID
    started_at: datetime
    ended_at: datetime | None = None
    ended_by: UUID | None = None  # puste, gdy zamknięcie wykonał system
    end_reason: IntervalEndReason | None = None

    @property
    def is_open(self) -> bool:
        return self.ended_at is None


@dataclass(kw_only=True)
class Operation:
    """Child entity WorkOrder (ADR-0002); stan zmieniany wyłącznie przez rodzica."""

    id: UUID
    work_order_id: UUID
    operation_number: str
    status: ExecutionStatus = ExecutionStatus.WAITING
    assigned_worker_id: UUID | None = None
    workstation_id: UUID | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    completed_by: UUID | None = None
    cancelled_at: datetime | None = None
    cancelled_by: UUID | None = None


@dataclass(kw_only=True)
class WorkOrder:
    """Aggregate Root Work Execution."""

    id: UUID
    order_number: str
    _execution_mode: ExecutionMode
    status: ExecutionStatus = ExecutionStatus.WAITING
    target_type: TargetType | None = None
    target_id: UUID | None = None
    priority: int = 0  # skala priorytetów nieustalona
    deadline: datetime | None = None
    assigned_worker_id: UUID | None = None
    workstation_id: UUID | None = None
    related_orders: list[OrderReference] = field(default_factory=list)
    required_items: list[RequiredItem] = field(default_factory=list)
    created_by: UUID
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    completed_by: UUID | None = None
    cancelled_at: datetime | None = None
    cancelled_by: UUID | None = None

    # Dzieci ładowane razem z agregatem; nie są utrwalane jako lista ID w wierszu WorkOrder.
    operations: list[Operation] = field(default_factory=list)
    # Interwały należą do granicy spójności, bo Pause/Cancel rodzica zamyka je atomowo.
    intervals: list[WorkInterval] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        order_number: str,
        execution_mode: ExecutionMode,
        created_by: UUID,
        created_at: datetime,
        target_type: TargetType | None = None,
        target_id: UUID | None = None,
        priority: int = 0,
        deadline: datetime | None = None,
        assigned_worker_id: UUID | None = None,
        workstation_id: UUID | None = None,
        related_orders: Sequence[OrderReference] = (),
        required_items: Sequence[RequiredItem] = (),
    ) -> Self:
        """Utworzenie nowego zlecenia w stanie WAITING.

        Konstruktor służy do odtworzenia zapisanego stanu (repozytorium).
        """

        if not order_number.strip():
            raise WorkExecutionError("Numer zlecenia nie może być pusty.")
        if (target_type is None) != (target_id is None):
            raise WorkExecutionError("target_type i target_id muszą być podane razem.")

        return cls(
            id=id,
            order_number=order_number,
            _execution_mode=execution_mode,
            target_type=target_type,
            target_id=target_id,
            priority=priority,
            deadline=deadline,
            assigned_worker_id=assigned_worker_id,
            workstation_id=workstation_id,
            related_orders=list(related_orders),
            required_items=list(required_items),
            created_by=created_by,
            created_at=created_at,
        )

    @property
    def execution_mode(self) -> ExecutionMode:
        """Tryb wykonania zlecenia (DIRECT lub OPERATIONS)."""

        return self._execution_mode

    def _assert_can(self, command: _Command) -> None:
        """Walidacja przejścia statusu dla komendy w kontekście zlecenia."""

        _assert_can(self.status, command, f"WorkOrder {self.order_number}")

    def _require_mode(self, mode: ExecutionMode) -> None:
        """Walidacja trybu wykonania zlecenia."""

        if self.execution_mode is not mode:
            raise InvalidExecutionModeError(
                f"Komenda wymaga trybu {mode}, zlecenie jest w trybie {self.execution_mode}."
            )

    def _require_in_progress(self) -> None:
        """Start/Resume/dołączenie do Operation wymagają rodzica IN_PROGRESS."""

        if self.status is not ExecutionStatus.IN_PROGRESS:
            raise InvalidStatusError(
                f"WorkOrder {self.order_number}: wymagany status IN_PROGRESS, jest {self.status}"
            )

    def _return_operation(self, operation_id: UUID) -> Operation:
        """Pobranie operacji po ID; wyjątek, jeśli nie istnieje."""

        for operation in self.operations:
            if operation.id == operation_id:
                return operation
        raise OperationNotFoundError(
            f"Brak Operation {operation_id} w zleceniu {self.order_number}."
        )

    def _return_open_intervals(self, operation_id: UUID | None = None) -> list[WorkInterval]:
        """Otwarte interwały całego zlecenia albo, gdy podano operation_id, jednej Operation."""

        return [
            interval
            for interval in self.intervals
            if interval.is_open and (operation_id is None or interval.operation_id == operation_id)
        ]

    def _has_open_intervals(self) -> bool:
        """Sprawdzenie, czy istnieją otwarte przedziały pracy."""

        return bool(self._return_open_intervals())

    def _open_interval(
        self,
        interval_id: UUID,
        worker_id: UUID,
        started_at: datetime,
        operation_id: UUID | None = None,
    ) -> None:
        """Otwiera interwał pracy."""

        # Tylko w obrębie agregatu; globalny WE-INV-04 pilnuje warstwa aplikacji i indeks w DB.
        if any(interval.worker_id == worker_id for interval in self._return_open_intervals()):
            raise WorkExecutionError("Pracownik ma już otwarty przedział pracy w tym zleceniu.")
        self.intervals.append(
            WorkInterval(
                id=interval_id,
                work_order_id=self.id,
                operation_id=operation_id,
                worker_id=worker_id,
                started_at=started_at,
            )
        )

    @staticmethod
    def _close_intervals(
        intervals: list[WorkInterval],
        ended_at: datetime,
        ended_by: UUID | None,
        reason: IntervalEndReason,
    ) -> None:
        """Zamyka podane interwały pracy."""

        for interval in intervals:
            interval.ended_at = ended_at
            interval.ended_by = ended_by
            interval.end_reason = reason

    def start_work_order(self, interval_id: UUID, worker_id: UUID, started_at: datetime) -> None:
        """Rozpoczyna work order.
        WAITING → IN_PROGRESS. DIRECT otwiera interwał; OPERATIONS nie (interval_id i
        worker_id są wtedy pomijane)."""

        self._assert_can("start")
        if not self._has_open_intervals():
            if self.execution_mode is ExecutionMode.DIRECT:
                self._open_interval(interval_id, worker_id, started_at)
            self.status = ExecutionStatus.IN_PROGRESS
            self.started_at = started_at
        else:
            raise WorkExecutionError(
                "Nieprzewidziane zachowanie: zlecenie WAITING z otwartymi interwałami pracy; "
                "Operacja przerwana"
            )  # Do przemyślenia jak obsłużyć ten błąd

    def pause_work_order(self, ended_at: datetime, ended_by: UUID) -> None:
        """Wstrzymuje work order.
        IN_PROGRESS → PAUSED. OPERATIONS: aktywne Operation → PAUSED, Operation WAITING
        i terminalne bez zmian. Zamyka wszystkie otwarte interwały."""

        self._assert_can("pause")
        self._close_intervals(
            self._return_open_intervals(), ended_at, ended_by, IntervalEndReason.WORK_ORDER_PAUSED
        )
        for operation in self.operations:
            if operation.status is ExecutionStatus.IN_PROGRESS:
                operation.status = ExecutionStatus.PAUSED
        self.status = ExecutionStatus.PAUSED

    def resume_work_order(self, interval_id: UUID, worker_id: UUID, started_at: datetime) -> None:
        """Wznawia work order.
        PAUSED -> IN_PROGRESS. DIRECT otwiera nowy interwał; OPERATIONS bez auto-resume dzieci."""

        self._assert_can("resume")
        if not self._has_open_intervals():
            if self.execution_mode is ExecutionMode.DIRECT:
                self._open_interval(interval_id, worker_id, started_at)
            self.status = ExecutionStatus.IN_PROGRESS
        else:
            raise WorkExecutionError(
                "Nieprzewidziane zachowanie: zlecenie PAUSED z otwartymi interwałami pracy; "
                "Operacja przerwana"
            )

    def complete_work_order(self, completed_at: datetime, completed_by: UUID) -> None:
        """Zakańcza aktywny work order.
        IN_PROGRESS -> COMPLETED. OPERATIONS: wszystkie Operation terminalne, >=1 COMPLETED."""

        self._assert_can("complete")
        if self.execution_mode is ExecutionMode.OPERATIONS:
            statuses = [operation.status for operation in self.operations]
            if not all(status.is_terminal for status in statuses):
                raise InvalidStatusError("Nie wszystkie Operation są zakończone lub anulowane.")
            if ExecutionStatus.COMPLETED not in statuses:  # obejmuje też zero operacji (O-02)
                raise InvalidStatusError("Wymagana co najmniej jedna ukończona Operation.")

        self._close_intervals(
            self._return_open_intervals(),
            completed_at,
            completed_by,
            IntervalEndReason.WORK_ORDER_COMPLETED,
        )
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = completed_at
        self.completed_by = completed_by

    def cancel_work_order(self, cancelled_at: datetime, cancelled_by: UUID) -> None:
        """Anuluje WorkOrder.
        ...-> CANCELLED. OPERATIONS: nieterminalne Operation -> CANCELLED, terminalne bez zmian."""

        self._assert_can("cancel")
        self._close_intervals(
            self._return_open_intervals(),
            cancelled_at,
            cancelled_by,
            IntervalEndReason.WORK_ORDER_CANCELLED,
        )
        for operation in self.operations:
            if not operation.status.is_terminal:
                operation.status = ExecutionStatus.CANCELLED
                operation.cancelled_at = cancelled_at
                operation.cancelled_by = cancelled_by
        self.status = ExecutionStatus.CANCELLED
        self.cancelled_at = cancelled_at
        self.cancelled_by = cancelled_by

    def add_operation(
        self,
        operation_id: UUID,
        operation_number: str,
        created_at: datetime,
        assigned_worker_id: UUID | None = None,
        workstation_id: UUID | None = None,
    ) -> Operation:
        """Dodanie nowej operacji do zlecenia w trybie OPERATIONS. Stan początkowy WAITING."""

        self._require_mode(ExecutionMode.OPERATIONS)
        # O-03: dodawanie do rozpoczętego rodzica jest nieustalone, więc na razie tylko WAITING.
        if self.status is not ExecutionStatus.WAITING:
            raise InvalidStatusError(
                f"Operation można dodać tylko do zlecenia WAITING, aktualny status: {self.status}."
            )
        if not operation_number.strip():
            raise WorkExecutionError("Numer operacji nie może być pusty.")

        operation = Operation(
            id=operation_id,
            work_order_id=self.id,
            operation_number=operation_number,
            assigned_worker_id=assigned_worker_id,
            workstation_id=workstation_id,
            created_at=created_at,
        )
        self.operations.append(operation)
        return operation

    def start_operation(
        self,
        operation_id: UUID,
        interval_id: UUID,
        worker_id: UUID,
        started_at: datetime,
    ) -> None:
        """Rozpoczyna operację.
        WAITING -> IN_PROGRESS. Wymaga, by rodzic był IN_PROGRESS (start/resume WorkOrder)."""

        self._require_mode(ExecutionMode.OPERATIONS)
        self._require_in_progress()

        operation = self._return_operation(operation_id)
        _assert_can(operation.status, "start", f"Operation {operation.operation_number}")

        self._open_interval(interval_id, worker_id, started_at, operation.id)
        operation.status = ExecutionStatus.IN_PROGRESS
        operation.started_at = started_at

    def pause_operation(self, operation_id: UUID, ended_at: datetime, ended_by: UUID) -> None:
        """Wstrzymuje aktywną operację. IN_PROGRESS -> PAUSED."""

        self._require_mode(ExecutionMode.OPERATIONS)
        operation = self._return_operation(operation_id)
        _assert_can(operation.status, "pause", f"Operation {operation.operation_number}")

        self._close_intervals(
            self._return_open_intervals(operation_id),
            ended_at,
            ended_by,
            IntervalEndReason.OPERATION_PAUSED,
        )
        operation.status = ExecutionStatus.PAUSED

    def resume_operation(
        self,
        operation_id: UUID,
        interval_id: UUID,
        worker_id: UUID,
        started_at: datetime,
    ) -> None:
        self._require_mode(ExecutionMode.OPERATIONS)
        self._require_in_progress()
        operation = self._return_operation(operation_id)
        _assert_can(operation.status, "resume", f"Operation {operation.operation_number}")

        self._open_interval(interval_id, worker_id, started_at, operation_id)
        operation.status = ExecutionStatus.IN_PROGRESS

    def complete_operation(
        self, operation_id: UUID, completed_at: datetime, completed_by: UUID
    ) -> None:
        """Kończy operację.
        Nie kończy rodzica - CompleteWorkOrder jest zawsze jawną komendą."""

        self._require_mode(ExecutionMode.OPERATIONS)
        operation = self._return_operation(operation_id)
        _assert_can(operation.status, "complete", f"Operation {operation.operation_number}")

        self._close_intervals(
            self._return_open_intervals(operation_id),
            completed_at,
            completed_by,
            IntervalEndReason.OPERATION_COMPLETED,
        )

        operation.status = ExecutionStatus.COMPLETED
        operation.completed_at = completed_at
        operation.completed_by = completed_by

    def cancel_operation(
        self, operation_id: UUID, cancelled_at: datetime, cancelled_by: UUID
    ) -> None:
        """Anuluje operację. WAITING/IN_PROGRESS/PAUSED -> CANCELLED."""

        self._require_mode(ExecutionMode.OPERATIONS)
        operation = self._return_operation(operation_id)
        _assert_can(operation.status, "cancel", f"Operation {operation.operation_number}")
        self._close_intervals(
            self._return_open_intervals(operation.id),
            cancelled_at,
            cancelled_by,
            IntervalEndReason.OPERATION_CANCELLED,
        )

        operation.status = ExecutionStatus.CANCELLED
        operation.cancelled_at = cancelled_at
        operation.cancelled_by = cancelled_by

    def open_interval_on_operation(
        self,
        operation_id: UUID,
        interval_id: UUID,
        worker_id: UUID,
        started_at: datetime,
    ) -> None:
        """Dołącza kolejnego pracownika do Operation IN_PROGRESS (nowy interwał pracy)."""

        self._require_mode(ExecutionMode.OPERATIONS)
        self._require_in_progress()
        operation = self._return_operation(operation_id)
        if operation.status is not ExecutionStatus.IN_PROGRESS:
            raise InvalidStatusError(
                f"Operation {operation.operation_number}: wymagany IN_PROGRESS, "
                f"obecny status: {operation.status}"
            )
        self._open_interval(interval_id, worker_id, started_at, operation.id)

    def close_interval_on_operation(
        self,
        operation_id: UUID,
        worker_id: UUID,
        ended_at: datetime,
        ended_by: UUID | None,
        reason: IntervalEndReason,
    ) -> None:
        """Zamyka interwał jednego pracownika; ostatni zamknięty → Operation PAUSED."""

        self._require_mode(ExecutionMode.OPERATIONS)
        operation = self._return_operation(operation_id)
        open_intervals = self._return_open_intervals(operation.id)
        worker_intervals = [i for i in open_intervals if i.worker_id == worker_id]
        if not worker_intervals:
            raise WorkExecutionError("Pracownik nie ma otwartego przedziału pracy w tej Operation.")

        self._close_intervals(worker_intervals, ended_at, ended_by, reason)
        if len(worker_intervals) == len(open_intervals):
            operation.status = ExecutionStatus.PAUSED
