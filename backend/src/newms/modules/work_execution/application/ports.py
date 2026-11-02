from typing import Protocol
from uuid import UUID

from newms.modules.work_execution.domain.models import WorkOrder


class WorkOrderRepository(Protocol):
    def get_for_update(self, work_order_id: UUID) -> WorkOrder | None: ...
