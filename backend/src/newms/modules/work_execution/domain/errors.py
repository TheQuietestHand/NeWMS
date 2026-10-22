class WorkExecutionError(Exception):
    """Bazowy błąd domeny Work Execution."""

    code: str = "WORK_EXECUTION_ERROR"


class InvalidStatusError(WorkExecutionError):
    """Niedozwolone przejście stanu, w tym każda zmiana stanu terminalnego."""

    code = "INVALID_STATUS"


class InvalidExecutionModeError(WorkExecutionError):
    """Komenda niedostępna w trybie wykonania zlecenia."""

    code = "INVALID_EXECUTION_MODE"


class OperationNotFoundError(WorkExecutionError):
    """Operation o podanym id nie należy do tego zlecenia."""

    code = "NOT_FOUND"
