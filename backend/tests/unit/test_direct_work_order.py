import copy
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from newms.modules.work_execution.domain.enums import (
    ExecutionMode,
    ExecutionStatus,
    IntervalEndReason,
    OrderReferenceCategory,
    TargetType,
)
from newms.modules.work_execution.domain.errors import InvalidStatusError, WorkExecutionError
from newms.modules.work_execution.domain.models import OrderReference, RequiredItem, WorkOrder

T0 = datetime(2026, 10, 19, 8, 0, tzinfo=UTC)


def new_direct_work_order() -> WorkOrder:
    return WorkOrder.create(
        id=uuid4(),
        order_number="WO-1",
        execution_mode=ExecutionMode.DIRECT,
        created_by=uuid4(),
        created_at=T0,
    )


def direct_work_order_in(status: ExecutionStatus) -> WorkOrder:
    """Doprowadza zlecenie do zadanego statusu wyłącznie dozwolonymi komendami."""

    wo = new_direct_work_order()
    if status is ExecutionStatus.WAITING:
        return wo
    if status is ExecutionStatus.CANCELLED:
        wo.cancel_work_order(T0, uuid4())
        return wo

    wo.start_work_order(uuid4(), uuid4(), T0)
    if status is ExecutionStatus.PAUSED:
        wo.pause_work_order(T0, uuid4())
    elif status is ExecutionStatus.COMPLETED:
        wo.complete_work_order(T0, uuid4())
    return wo


def test_takeover_after_pause_keeps_history_and_records_completer() -> None:
    worker_a, worker_b, manager = uuid4(), uuid4(), uuid4()
    first_interval, second_interval = uuid4(), uuid4()
    wo = new_direct_work_order()

    wo.start_work_order(first_interval, worker_a, T0)
    wo.pause_work_order(T0 + timedelta(hours=1), worker_a)
    wo.resume_work_order(second_interval, worker_b, T0 + timedelta(hours=2))
    wo.complete_work_order(T0 + timedelta(hours=3), manager)

    assert wo.status is ExecutionStatus.COMPLETED
    assert wo.started_at == T0  # Resume nie nadpisuje pierwszego rozpoczęcia
    assert wo.completed_by == manager  # kończący nie musi być wykonawcą
    assert wo.completed_at == T0 + timedelta(hours=3)

    first, second = wo.intervals
    assert (first.id, first.worker_id, first.end_reason) == (
        first_interval,
        worker_a,
        IntervalEndReason.WORK_ORDER_PAUSED,
    )
    assert (second.id, second.worker_id, second.end_reason) == (
        second_interval,
        worker_b,
        IntervalEndReason.WORK_ORDER_COMPLETED,
    )
    assert second.ended_by == manager
    assert not any(interval.is_open for interval in wo.intervals)


COMMANDS: dict[str, Callable[[WorkOrder], None]] = {
    "start": lambda wo: wo.start_work_order(uuid4(), uuid4(), T0),
    "pause": lambda wo: wo.pause_work_order(T0, uuid4()),
    "resume": lambda wo: wo.resume_work_order(uuid4(), uuid4(), T0),
    "complete": lambda wo: wo.complete_work_order(T0, uuid4()),
    "cancel": lambda wo: wo.cancel_work_order(T0, uuid4()),
}

# Pary (status, komenda) z tabeli „DIRECT — przejścia” w docs/domain/work-execution.md.
ALLOWED = {
    (ExecutionStatus.WAITING, "start"),
    (ExecutionStatus.WAITING, "cancel"),
    (ExecutionStatus.IN_PROGRESS, "pause"),
    (ExecutionStatus.IN_PROGRESS, "complete"),
    (ExecutionStatus.IN_PROGRESS, "cancel"),
    (ExecutionStatus.PAUSED, "resume"),
    (ExecutionStatus.PAUSED, "cancel"),
}

FORBIDDEN = [
    (status, command)
    for status in ExecutionStatus
    for command in COMMANDS
    if (status, command) not in ALLOWED
]

NOT_TERMINAL = [status for status in ExecutionStatus if not status.is_terminal]


@pytest.mark.parametrize("status", NOT_TERMINAL)
def test_cancel_every_non_terminal_status_works(status: ExecutionStatus) -> None:
    wo = direct_work_order_in(status)
    before = copy.deepcopy(wo)

    user = uuid4()
    wo.cancel_work_order(T0, user)

    assert wo.status is ExecutionStatus.CANCELLED
    assert wo.cancelled_at == T0
    assert wo.cancelled_by == user
    assert wo.completed_at is None
    assert wo.completed_by is None
    if before.status is ExecutionStatus.WAITING:
        assert not wo.intervals  # Nie powstaje żaden przedział pracy
    elif before.status is ExecutionStatus.IN_PROGRESS:
        assert len(wo.intervals) == 1  # Przedział pracy powstał w momencie rozpoczęcia zlecenia
        assert (
            wo.intervals[0].end_reason is IntervalEndReason.WORK_ORDER_CANCELLED
        )  # Przedział pracy został zamknięty w momencie anulowania zlecenia
        assert wo.intervals[0].ended_by == user
    elif before.status is ExecutionStatus.PAUSED:
        assert len(wo.intervals) == 1  # Przedział pracy powstał w momencie rozpoczęcia zlecenia
        assert (
            wo.intervals[0].end_reason is IntervalEndReason.WORK_ORDER_PAUSED
        )  # Anulacja nie zmienia statusu poprzedniego przedziału pracy
        assert (
            before.intervals[0].ended_by == wo.intervals[0].ended_by
        )  # Anulacja nie zmienia wykonawcy poprzedniego przedziału pracy


def test_at_most_one_open_interval_allowed_in_direct_mode() -> None:
    wo = new_direct_work_order()
    pairs = [("start", 1), ("pause", 0), ("resume", 1), ("pause", 0)]

    assert sum(interval.is_open for interval in wo.intervals) == 0

    for command, expected_open in pairs:
        COMMANDS[command](wo)
        assert sum(interval.is_open for interval in wo.intervals) == expected_open
        assert not wo.operations  # DIRECT nie ma Operation (WE-INV-03)


def test_work_order_create_function() -> None:
    with pytest.raises(WorkExecutionError, match="Numer zlecenia nie może być pusty"):
        WorkOrder.create(
            id=uuid4(),
            order_number=" ",
            execution_mode=ExecutionMode.DIRECT,
            created_by=uuid4(),
            created_at=T0,
        )

    with pytest.raises(WorkExecutionError, match="target_type i target_id muszą być podane razem"):
        WorkOrder.create(
            id=uuid4(),
            order_number="WO-1",
            execution_mode=ExecutionMode.DIRECT,
            created_by=uuid4(),
            created_at=T0,
            target_type=TargetType.MACHINE,
        )

    with pytest.raises(WorkExecutionError, match="target_type i target_id muszą być podane razem"):
        WorkOrder.create(
            id=uuid4(),
            order_number="WO-1",
            execution_mode=ExecutionMode.DIRECT,
            created_by=uuid4(),
            created_at=T0,
            target_id=uuid4(),
        )

    refs_items = [RequiredItem(item_ref="bolt", quantity=Decimal(10))]
    refs_orders = [OrderReference(category=OrderReferenceCategory.PICKING, order_id=uuid4())]
    wo = WorkOrder.create(
        id=uuid4(),
        order_number="WO-1",
        execution_mode=ExecutionMode.DIRECT,
        created_by=uuid4(),
        created_at=T0,
        related_orders=refs_orders,
        required_items=refs_items,
    )

    refs_orders.append(OrderReference(category=OrderReferenceCategory.TRANSPORT, order_id=uuid4()))
    refs_items.append(RequiredItem(item_ref="nut", quantity=Decimal(5)))

    assert len(wo.related_orders) == 1  # zmiana listy wejściowej nie zmienia zlecenia
    assert len(wo.required_items) == 1
    assert wo.status is ExecutionStatus.WAITING
    assert not wo.intervals and wo.started_at is None


def test_execution_mode_immutability() -> None:
    wo1 = new_direct_work_order()
    wo2 = WorkOrder.create(
        id=uuid4(),
        order_number="WO-2",
        execution_mode=ExecutionMode.OPERATIONS,
        created_by=uuid4(),
        created_at=T0,
    )
    before1 = copy.deepcopy(wo1)
    before2 = copy.deepcopy(wo2)

    with pytest.raises(AttributeError):
        wo1.execution_mode = ExecutionMode.OPERATIONS  # type: ignore[misc]
    assert wo1 == before1

    with pytest.raises(AttributeError):
        wo2.execution_mode = ExecutionMode.DIRECT  # type: ignore[misc]
    assert wo2 == before2


@pytest.mark.parametrize(("status", "command"), FORBIDDEN, ids=lambda v: str(v))
def test_forbidden_command_raises_invalid_status_and_changes_nothing(
    status: ExecutionStatus, command: str
) -> None:
    wo = direct_work_order_in(status)
    before = copy.deepcopy(wo)

    with pytest.raises(InvalidStatusError) as exc_info:
        COMMANDS[command](wo)

    assert exc_info.value.code == "INVALID_STATUS"
    assert wo == before


def test_start_operations_work_order() -> None:
    owo = WorkOrder.create(
        id=uuid4(),
        order_number="WO-1",
        execution_mode=ExecutionMode.OPERATIONS,
        created_by=uuid4(),
        created_at=T0,
    )
    owo.start_work_order(uuid4(), uuid4(), T0)  # NotImplementedError
    assert owo.status is ExecutionStatus.IN_PROGRESS
    assert not owo.intervals
