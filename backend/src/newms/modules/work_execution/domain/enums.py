from enum import StrEnum


class ExecutionMode(StrEnum):
    DIRECT = "DIRECT"
    OPERATIONS = "OPERATIONS"


class ExecutionStatus(StrEnum):
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    @property
    def is_terminal(self) -> bool:
        return self in (ExecutionStatus.COMPLETED, ExecutionStatus.CANCELLED)


class IntervalEndReason(StrEnum):
    PAUSED = "PAUSED"
    WORK_ORDER_PAUSED = "WORK_ORDER_PAUSED"
    OPERATION_PAUSED = "OPERATION_PAUSED"
    WORK_ORDER_COMPLETED = "WORK_ORDER_COMPLETED"
    OPERATION_COMPLETED = "OPERATION_COMPLETED"
    WORK_ORDER_CANCELLED = "WORK_ORDER_CANCELLED"
    OPERATION_CANCELLED = "OPERATION_CANCELLED"
    MACHINE_BLOCK = "MACHINE_BLOCK"


class OrderReferenceCategory(StrEnum):
    # Relacja do execution_mode (WORK_DIRECT / WORK_OPERATIONS) pozostaje OPEN (O-09).
    PICKING = "PICKING"
    WORK_DIRECT = "WORK_DIRECT"
    WORK_OPERATIONS = "WORK_OPERATIONS"
    TRANSPORT = "TRANSPORT"


class TargetType(StrEnum):
    MACHINE = "MACHINE"
