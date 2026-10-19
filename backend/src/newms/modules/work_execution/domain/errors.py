class WorkExecutionError(Exception):
    """Bazowy błąd domeny Work Execution."""

    code: str = "WORK_EXECUTION_ERROR"


class InvalidStatusError(WorkExecutionError):
    """Niedozwolone przejście stanu, w tym każda zmiana stanu terminalnego."""

    code = "INVALID_STATUS"


class InvalidExecutionModeError(WorkExecutionError):
    """Niedozwolona zmiana trybu wykonania."""

    code = "INVALID_EXECUTION_MODE"
