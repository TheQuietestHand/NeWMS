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
from newms.modules.work_execution.domain.errors import InvalidStatusError, WorkExecutionError

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
        return self._execution_mode

    def _assert_can(self, command: _Command) -> None:
        """Walidacja, czy komenda jest dozwolona w bieżącym statusie."""

        if self.status not in _ALLOWED_FROM[command]:
            raise InvalidStatusError(f"Komenda {command} niedozwolona w statusie {self.status}")

    def _has_open_intervals(self) -> bool:
        """Sprawdzenie, czy istnieją otwarte przedziały pracy."""

        return any(interval.is_open for interval in self.intervals)

    def _close_open_intervals(
        self, ended_at: datetime, ended_by: UUID | None, reason: IntervalEndReason
    ) -> None:
        """Zamknięcie wszystkich otwartych przedziałów pracy."""

        for interval in self.intervals:
            if interval.is_open:
                interval.ended_at = ended_at
                interval.ended_by = ended_by
                interval.end_reason = reason

    def start_work_order(self, interval_id: UUID, worker_id: UUID, started_at: datetime) -> None:
        """Rozpoczęcie zlecenia bezpośredniego (DIRECT)."""

        if self.execution_mode == ExecutionMode.DIRECT:
            self._assert_can("start")
            if self._has_open_intervals():
                raise WorkExecutionError(
                    "Nie można rozpocząć zlecenia, gdy istnieją otwarte przedziały pracy."
                )

            interval = WorkInterval(
                id=interval_id,
                work_order_id=self.id,
                operation_id=None,  # Brak operacji dla DIRECT
                worker_id=worker_id,
                started_at=started_at,
            )
            self.status = ExecutionStatus.IN_PROGRESS
            self.started_at = started_at
            self.intervals.append(interval)
        else:
            raise NotImplementedError()

    def pause_work_order(self, ended_at: datetime, ended_by: UUID) -> None:
        """Wstrzymanie zlecenia bezpośredniego (DIRECT)."""

        if self.execution_mode == ExecutionMode.DIRECT:
            self._assert_can("pause")
            if not self._has_open_intervals():
                raise WorkExecutionError(
                    "Nie można wstrzymać zlecenia, gdy nie istnieją otwarte przedziały pracy."
                )

            self._close_open_intervals(ended_at, ended_by, IntervalEndReason.WORK_ORDER_PAUSED)
            self.status = ExecutionStatus.PAUSED
        else:
            raise NotImplementedError()

    def resume_work_order(self, interval_id: UUID, worker_id: UUID, started_at: datetime) -> None:
        """Wznowienie zlecenia bezpośredniego (DIRECT)."""

        if self.execution_mode == ExecutionMode.DIRECT:
            self._assert_can("resume")
            if self._has_open_intervals():
                raise WorkExecutionError(
                    "Nie można wznowić zlecenia, gdy istnieją otwarte przedziały pracy."
                )

            interval = WorkInterval(
                id=interval_id,
                work_order_id=self.id,
                operation_id=None,  # Brak operacji dla DIRECT
                worker_id=worker_id,
                started_at=started_at,
            )
            self.status = ExecutionStatus.IN_PROGRESS
            self.intervals.append(interval)
        else:
            raise NotImplementedError()

    def complete_work_order(self, completed_at: datetime, completed_by: UUID) -> None:
        """Zakończenie zlecenia bezpośredniego (DIRECT)."""

        if self.execution_mode == ExecutionMode.DIRECT:
            self._assert_can("complete")
            if not self._has_open_intervals():
                raise WorkExecutionError(
                    "Nie można zakończyć zlecenia, gdy nie istnieją otwarte przedziały pracy."
                )

            self._close_open_intervals(
                completed_at, completed_by, IntervalEndReason.WORK_ORDER_COMPLETED
            )
            self.status = ExecutionStatus.COMPLETED
            self.completed_at = completed_at
            self.completed_by = completed_by
        else:
            raise NotImplementedError()

    def cancel_work_order(self, cancelled_at: datetime, cancelled_by: UUID) -> None:
        """Anulowanie zlecenia bezpośredniego (DIRECT)."""

        if self.execution_mode == ExecutionMode.DIRECT:
            self._assert_can("cancel")
            self._close_open_intervals(
                cancelled_at, cancelled_by, IntervalEndReason.WORK_ORDER_CANCELLED
            )
            self.status = ExecutionStatus.CANCELLED
            self.cancelled_at = cancelled_at
            self.cancelled_by = cancelled_by
        else:
            raise NotImplementedError()
