import copy
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from newms.modules.work_execution.domain.enums import (
    ExecutionMode,
    ExecutionStatus,
    IntervalEndReason,
)
from newms.modules.work_execution.domain.errors import (
    InvalidExecutionModeError,
    InvalidStatusError,
    OperationNotFoundError,
    WorkExecutionError,
)
from newms.modules.work_execution.domain.models import Operation, WorkOrder

T0 = datetime(2026, 10, 19, 8, 0, tzinfo=UTC)

OP_COMMANDS: dict[str, Callable[[WorkOrder, UUID], None]] = {
    "start": lambda wo, op_id: wo.start_operation(op_id, uuid4(), uuid4(), T0),
    "pause": lambda wo, op_id: wo.pause_operation(op_id, T0, uuid4()),
    "resume": lambda wo, op_id: wo.resume_operation(op_id, uuid4(), uuid4(), T0),
    "complete": lambda wo, op_id: wo.complete_operation(op_id, T0, uuid4()),
    "cancel": lambda wo, op_id: wo.cancel_operation(op_id, T0, uuid4()),
}

OP_ALLOWED: dict[tuple[ExecutionStatus, str], ExecutionStatus] = {
    (ExecutionStatus.WAITING, "start"): ExecutionStatus.IN_PROGRESS,
    (ExecutionStatus.WAITING, "cancel"): ExecutionStatus.CANCELLED,
    (ExecutionStatus.IN_PROGRESS, "pause"): ExecutionStatus.PAUSED,
    (ExecutionStatus.IN_PROGRESS, "complete"): ExecutionStatus.COMPLETED,
    (ExecutionStatus.IN_PROGRESS, "cancel"): ExecutionStatus.CANCELLED,
    (ExecutionStatus.PAUSED, "resume"): ExecutionStatus.IN_PROGRESS,
    (ExecutionStatus.PAUSED, "cancel"): ExecutionStatus.CANCELLED,
}

OP_FORBIDDEN = [
    (status, command)
    for status in ExecutionStatus
    for command in OP_COMMANDS
    if (status, command) not in OP_ALLOWED
]


def new_operations_work_order() -> WorkOrder:
    return WorkOrder.create(
        id=uuid4(),
        order_number="WO-1",
        execution_mode=ExecutionMode.OPERATIONS,
        created_by=uuid4(),
        created_at=T0,
    )


def new_work_order_with_operations(n: int) -> tuple[WorkOrder, list[Operation]]:
    """Zlecenie OPERATIONS z n operacjami WAITING, już IN_PROGRESS."""

    wo = new_operations_work_order()
    operations = [wo.add_operation(uuid4(), f"OP-{i}", T0) for i in range(n)]
    wo.start_work_order(T0)
    return wo, operations


def drive_operations_work_order_to(status: ExecutionStatus) -> WorkOrder:
    """Doprowadza zlecenie do zadanego statusu wyłącznie dozwolonymi komendami.

    COMPLETED wymaga co najmniej jednej ukończonej Operation (O-02), więc w tym przypadku
    dodaje jedną i kończy ją przed zleceniem.
    """

    wo = new_operations_work_order()
    if status is ExecutionStatus.WAITING:
        return wo
    if status is ExecutionStatus.CANCELLED:
        wo.cancel_work_order(T0, uuid4())
        return wo

    done = wo.add_operation(uuid4(), "OP-DONE", T0) if status is ExecutionStatus.COMPLETED else None
    wo.start_work_order(T0)
    if status is ExecutionStatus.PAUSED:
        wo.pause_work_order(T0, uuid4())
    elif done is not None:
        drive_operation_to(wo, done.id, ExecutionStatus.COMPLETED)
        wo.complete_work_order(T0, uuid4())
    return wo


def drive_operation_to(order: WorkOrder, operation_id: UUID, status: ExecutionStatus) -> None:
    """Doprowadza Operation z WAITING do zadanego statusu dozwolonymi komendami.

    Zakłada rodzica IN_PROGRESS — operacje trzeba dodać wcześniej, bo add_operation
    działa tylko na zleceniu WAITING (O-03).
    """

    if status is ExecutionStatus.WAITING:
        return
    if status is ExecutionStatus.CANCELLED:
        order.cancel_operation(operation_id, T0, uuid4())
        return

    order.start_operation(operation_id, uuid4(), uuid4(), T0)
    if status is ExecutionStatus.PAUSED:
        order.pause_operation(operation_id, T0, uuid4())
    elif status is ExecutionStatus.COMPLETED:
        order.complete_operation(operation_id, T0, uuid4())


def test_start_operation_before_work_order() -> None:
    wo = new_operations_work_order()
    operation_id = uuid4()
    wo.add_operation(operation_id, "OP-1", T0)

    with pytest.raises(InvalidStatusError):
        wo.start_operation(operation_id, uuid4(), uuid4(), T0)  # Start operacji przed startem WO

    assert wo.status == ExecutionStatus.WAITING  # Próba nie wpływa na stany
    assert wo.get_operation(operation_id).status == ExecutionStatus.WAITING
    assert not wo.intervals


def test_start_operations_work_order_doesnt_start_interval() -> None:
    wo = new_operations_work_order()
    wo.start_work_order(T0)

    assert not wo.intervals


def test_resume_work_order_does_not_resume_operations() -> None:
    wo, [active, waiting] = new_work_order_with_operations(2)
    drive_operation_to(wo, active.id, ExecutionStatus.IN_PROGRESS)
    wo.pause_work_order(T0, uuid4())

    wo.resume_work_order(T0)

    assert wo.status is ExecutionStatus.IN_PROGRESS
    assert active.status is ExecutionStatus.PAUSED  # bez auto-resume (reguła 5)
    assert waiting.status is ExecutionStatus.WAITING
    assert not wo.has_open_intervals


def test_complete_operation_doesnt_change_parent_status() -> None:
    wo = new_operations_work_order()
    op_id = uuid4()
    wo.add_operation(op_id, "OP-1", T0, uuid4(), uuid4())
    wo.start_work_order(T0)
    before = copy.deepcopy(wo)

    drive_operation_to(wo, op_id, ExecutionStatus.COMPLETED)

    assert wo.get_operation(op_id).status == ExecutionStatus.COMPLETED
    assert before.get_operation(op_id).status is ExecutionStatus.WAITING
    assert wo.status == before.status


@pytest.mark.parametrize(
    "child_statuses",
    [
        [],  # zero operacji (O-02, test obowiązkowy)
        [ExecutionStatus.CANCELLED, ExecutionStatus.CANCELLED],  # brak COMPLETED
        [ExecutionStatus.COMPLETED, ExecutionStatus.WAITING],
        [ExecutionStatus.COMPLETED, ExecutionStatus.PAUSED],
        [ExecutionStatus.COMPLETED, ExecutionStatus.IN_PROGRESS],  # regresja B1
    ],
    ids=["zero", "only-cancelled", "waiting", "paused", "in-progress"],
)
def test_complete_work_order_rejected_and_changes_nothing(
    child_statuses: list[ExecutionStatus],
) -> None:
    wo, operations = new_work_order_with_operations(len(child_statuses))
    for operation, status in zip(operations, child_statuses, strict=True):
        drive_operation_to(wo, operation.id, status)
    before = copy.deepcopy(wo)

    with pytest.raises(InvalidStatusError):
        wo.complete_work_order(T0, uuid4())

    assert wo == before


def test_complete_work_order_with_completed_and_cancelled_children() -> None:
    wo, [done, dropped] = new_work_order_with_operations(2)
    drive_operation_to(wo, done.id, ExecutionStatus.COMPLETED)
    drive_operation_to(wo, dropped.id, ExecutionStatus.CANCELLED)
    manager = uuid4()

    wo.complete_work_order(T0, manager)

    assert wo.status is ExecutionStatus.COMPLETED
    assert wo.completed_by == manager


def test_cascade_after_work_order_pause() -> None:
    wo = new_operations_work_order()
    operations = {
        status: wo.add_operation(uuid4(), f"OP-{status}", T0) for status in ExecutionStatus
    }
    wo.start_work_order(T0)
    for status, operation in operations.items():
        drive_operation_to(wo, operation.id, status)

    active = operations[ExecutionStatus.IN_PROGRESS]
    wo.open_interval_on_operation(active.id, uuid4(), uuid4(), T0)  # drugi współwykonawca

    paused_by = uuid4()
    paused_at = T0 + timedelta(hours=1)
    wo.pause_work_order(paused_at, paused_by)

    # Rodzic PAUSED; tylko aktywna Operation → PAUSED, reszta bez zmian (reguła 4, WE-INV-01).
    assert wo.status is ExecutionStatus.PAUSED
    for status, operation in operations.items():
        expected = ExecutionStatus.PAUSED if status is ExecutionStatus.IN_PROGRESS else status
        assert operation.status is expected, f"Operation doprowadzona do {status}"

    # Żaden interwał nie zostaje otwarty (WE-INV-08).
    assert not any(interval.is_open for interval in wo.intervals)

    # Kaskada zamknęła interwały obu współwykonawców, z powodem pauzy zlecenia.
    closed_by_cascade = [i for i in wo.intervals if i.operation_id == active.id]
    assert len(closed_by_cascade) == 2
    for interval in closed_by_cascade:
        assert interval.end_reason is IntervalEndReason.WORK_ORDER_PAUSED
        assert (interval.ended_at, interval.ended_by) == (paused_at, paused_by)

    # Interwały zamknięte wcześniej zachowują swój powód.
    reason_by_operation = {i.operation_id: i.end_reason for i in wo.intervals}
    paused_id = operations[ExecutionStatus.PAUSED].id
    completed_id = operations[ExecutionStatus.COMPLETED].id
    assert reason_by_operation[paused_id] is IntervalEndReason.OPERATION_PAUSED
    assert reason_by_operation[completed_id] is IntervalEndReason.OPERATION_COMPLETED


def test_cascade_after_work_order_cancel() -> None:
    wo = new_operations_work_order()
    operations = {
        status: wo.add_operation(uuid4(), f"OP-{status}", T0) for status in ExecutionStatus
    }
    wo.start_work_order(T0)
    for status, operation in operations.items():
        drive_operation_to(wo, operation.id, status)
    cancelled_by = uuid4()

    wo.cancel_work_order(T0, cancelled_by)

    assert wo.status is ExecutionStatus.CANCELLED
    for status, operation in operations.items():
        if status is ExecutionStatus.COMPLETED:
            assert operation.status is ExecutionStatus.COMPLETED  # terminalne bez zmian
            assert operation.cancelled_by is None
        elif status is ExecutionStatus.CANCELLED:
            assert operation.status is ExecutionStatus.CANCELLED
            assert operation.cancelled_by != cancelled_by  # anulowana wcześniej, kto inny
        else:
            assert operation.status is ExecutionStatus.CANCELLED, f"Operation z {status}"
            assert operation.cancelled_by == cancelled_by
    assert not wo.has_open_intervals
    active_id = operations[ExecutionStatus.IN_PROGRESS].id
    [cascade_closed] = [i for i in wo.intervals if i.operation_id == active_id]
    assert cascade_closed.end_reason is IntervalEndReason.WORK_ORDER_CANCELLED


@pytest.mark.parametrize(("status", "command"), list(OP_ALLOWED), ids=lambda v: str(v))
def test_allowed_operation_command_reaches_expected_status(
    status: ExecutionStatus, command: str
) -> None:
    wo, [operation] = new_work_order_with_operations(1)
    drive_operation_to(wo, operation.id, status)

    OP_COMMANDS[command](wo, operation.id)

    assert operation.status is OP_ALLOWED[(status, command)]
    assert wo.status is ExecutionStatus.IN_PROGRESS  # dziecko nie zmienia rodzica (reguła 3)


@pytest.mark.parametrize(("status", "command"), OP_FORBIDDEN, ids=lambda v: str(v))
def test_forbidden_operation_command_raises_invalid_status_and_changes_nothing(
    status: ExecutionStatus, command: str
) -> None:
    wo, [operation] = new_work_order_with_operations(1)
    drive_operation_to(wo, operation.id, status)
    before = copy.deepcopy(wo)

    with pytest.raises(InvalidStatusError) as exc_info:
        OP_COMMANDS[command](wo, operation.id)

    assert exc_info.value.code == "INVALID_STATUS"
    assert wo == before


def test_two_workers_on_one_operation_and_no_duplicates() -> None:
    wo, [first, second] = new_work_order_with_operations(2)
    worker_a, worker_b = uuid4(), uuid4()
    wo.start_operation(first.id, uuid4(), worker_a, T0)

    wo.open_interval_on_operation(first.id, uuid4(), worker_b, T0)

    assert {i.worker_id for i in wo.open_intervals(first.id)} == {worker_a, worker_b}

    before = copy.deepcopy(wo)
    with pytest.raises(WorkExecutionError):  # ten sam pracownik drugi raz na tej Operation
        wo.open_interval_on_operation(first.id, uuid4(), worker_a, T0)
    with pytest.raises(WorkExecutionError):  # ani na innej Operation tego zlecenia
        wo.start_operation(second.id, uuid4(), worker_a, T0)
    assert wo == before


def test_close_interval_on_operation_pauses_only_after_last_worker() -> None:
    wo, [operation] = new_work_order_with_operations(1)
    worker_a, worker_b = uuid4(), uuid4()
    wo.start_operation(operation.id, uuid4(), worker_a, T0)
    wo.open_interval_on_operation(operation.id, uuid4(), worker_b, T0)

    wo.close_interval_on_operation(operation.id, worker_a, T0, worker_a, IntervalEndReason.PAUSED)
    assert operation.status is ExecutionStatus.IN_PROGRESS  # B nadal pracuje
    assert [i.worker_id for i in wo.open_intervals(operation.id)] == [worker_b]

    wo.close_interval_on_operation(operation.id, worker_b, T0, worker_b, IntervalEndReason.PAUSED)
    # ponowny odczyt: mypy po pierwszej asercji zawęża operation.status do IN_PROGRESS
    assert wo.get_operation(operation.id).status is ExecutionStatus.PAUSED  # ostatni zamknięty
    assert not wo.has_open_intervals


def test_close_interval_for_worker_without_open_interval_changes_nothing() -> None:
    wo, [operation] = new_work_order_with_operations(1)
    wo.start_operation(operation.id, uuid4(), uuid4(), T0)
    before = copy.deepcopy(wo)

    with pytest.raises(WorkExecutionError):
        wo.close_interval_on_operation(operation.id, uuid4(), T0, None, IntervalEndReason.PAUSED)

    assert wo == before


def test_pause_operation_closes_all_co_workers() -> None:
    wo, [operation] = new_work_order_with_operations(1)
    wo.start_operation(operation.id, uuid4(), uuid4(), T0)
    wo.open_interval_on_operation(operation.id, uuid4(), uuid4(), T0)
    paused_by = uuid4()

    wo.pause_operation(operation.id, T0, paused_by)

    closed = [i for i in wo.intervals if i.operation_id == operation.id]
    assert len(closed) == 2
    assert all(i.end_reason is IntervalEndReason.OPERATION_PAUSED for i in closed)
    assert all(i.ended_by == paused_by for i in closed)


def test_resume_operation_opens_new_interval_and_keeps_first_start() -> None:
    wo, [operation] = new_work_order_with_operations(1)
    later = T0 + timedelta(hours=2)
    drive_operation_to(wo, operation.id, ExecutionStatus.PAUSED)
    resumed_by = uuid4()

    wo.resume_operation(operation.id, uuid4(), resumed_by, later)

    assert operation.started_at == T0  # pierwsze rozpoczęcie bez zmian
    [first, second] = [i for i in wo.intervals if i.operation_id == operation.id]
    assert not first.is_open and second.is_open
    assert (second.worker_id, second.started_at) == (resumed_by, later)


def test_resume_operation_requires_parent_in_progress() -> None:
    wo, [operation] = new_work_order_with_operations(1)
    drive_operation_to(wo, operation.id, ExecutionStatus.IN_PROGRESS)
    wo.pause_work_order(T0, uuid4())  # Operation → PAUSED przez kaskadę
    before = copy.deepcopy(wo)

    with pytest.raises(InvalidStatusError):
        wo.resume_operation(operation.id, uuid4(), uuid4(), T0)

    assert wo == before


@pytest.mark.parametrize("command", list(OP_COMMANDS))
def test_operation_commands_on_direct_raise_invalid_execution_mode(command: str) -> None:
    wo = WorkOrder.create(
        id=uuid4(),
        order_number="WO-D",
        execution_mode=ExecutionMode.DIRECT,
        created_by=uuid4(),
        created_at=T0,
    )
    wo.start_work_order(T0, interval_id=uuid4(), worker_id=uuid4())

    with pytest.raises(InvalidExecutionModeError) as exc_info:
        OP_COMMANDS[command](wo, uuid4())

    assert exc_info.value.code == "INVALID_EXECUTION_MODE"


def test_add_operation_on_direct_raises_invalid_execution_mode() -> None:
    wo = WorkOrder.create(
        id=uuid4(),
        order_number="WO-D",
        execution_mode=ExecutionMode.DIRECT,
        created_by=uuid4(),
        created_at=T0,
    )

    with pytest.raises(InvalidExecutionModeError):
        wo.add_operation(uuid4(), "OP-1", T0)
    assert not wo.operations


@pytest.mark.parametrize("command", list(OP_COMMANDS))
def test_unknown_operation_id_raises_not_found(command: str) -> None:
    wo, _ = new_work_order_with_operations(1)

    with pytest.raises(OperationNotFoundError) as exc_info:
        OP_COMMANDS[command](wo, uuid4())

    assert exc_info.value.code == "NOT_FOUND"


@pytest.mark.parametrize(
    "parent_status",
    [s for s in ExecutionStatus if s is not ExecutionStatus.WAITING],
)
def test_add_operation_only_while_parent_waiting(parent_status: ExecutionStatus) -> None:
    wo = drive_operations_work_order_to(parent_status)
    before = copy.deepcopy(wo)

    with pytest.raises(InvalidStatusError):
        wo.add_operation(uuid4(), "OP-1", T0)
    assert wo == before


def test_add_operation_rejects_blank_number() -> None:
    wo = new_operations_work_order()

    with pytest.raises(WorkExecutionError, match="Numer operacji nie może być pusty"):
        wo.add_operation(uuid4(), "  ", T0)
    assert not wo.operations


def test_add_operation_rejects_duplicate_number() -> None:
    wo = new_operations_work_order()
    wo.add_operation(uuid4(), "OP-1", T0)

    with pytest.raises(WorkExecutionError):
        wo.add_operation(uuid4(), "OP-1", T0)
    assert len(wo.operations) == 1


@pytest.mark.parametrize(
    "reason",
    [r for r in IntervalEndReason if r is not IntervalEndReason.PAUSED],
)
def test_close_interval_rejects_reserved_reasons(reason: IntervalEndReason) -> None:
    wo, [operation] = new_work_order_with_operations(1)
    worker = uuid4()
    wo.start_operation(operation.id, uuid4(), worker, T0)
    before = copy.deepcopy(wo)

    with pytest.raises(WorkExecutionError):
        wo.close_interval_on_operation(operation.id, worker, T0, worker, reason)
    assert wo == before


@pytest.mark.parametrize(
    "extra",
    [
        {"interval_id": uuid4(), "worker_id": uuid4()},
        {"interval_id": uuid4()},
        {"worker_id": uuid4()},
    ],
    ids=["both", "interval", "worker"],
)
@pytest.mark.parametrize("status", [ExecutionStatus.WAITING, ExecutionStatus.PAUSED])
def test_operations_start_and_resume_reject_interval_args(
    status: ExecutionStatus, extra: dict[str, UUID]
) -> None:
    wo = drive_operations_work_order_to(status)
    before = copy.deepcopy(wo)
    command = wo.start_work_order if status is ExecutionStatus.WAITING else wo.resume_work_order

    with pytest.raises(WorkExecutionError, match="nie otwiera interwału"):
        command(T0, **extra)

    assert wo == before


def test_collections_cannot_be_changed_from_outside() -> None:
    wo = new_operations_work_order()
    wo.add_operation(uuid4(), "OP-1", T0)
    before = copy.deepcopy(wo)

    with pytest.raises(AttributeError):
        wo.operations.clear()  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        wo.intervals.clear()  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        wo.operations = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        wo.intervals = ()  # type: ignore[misc]

    assert wo == before
