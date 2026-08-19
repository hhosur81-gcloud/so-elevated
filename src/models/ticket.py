"""ServiceImmediately ITSM Domain Models (FR-3.1 to FR-3.5)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from src.models.common import EnterpriseBaseModel


class PriorityEnum(str, Enum):
    """Incident priority levels."""
    P1 = "P1"  # Critical (System Outage / Security Incident)
    P2 = "P2"  # High (Department Blocked)
    P3 = "P3"  # Medium (Individual Impact)
    P4 = "P4"  # Low (General Inquiry)


class TicketStatusEnum(str, Enum):
    """Incident ticket lifecycle states."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_CUSTOMER = "PENDING_CUSTOMER"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


@dataclass
class TicketComment(EnterpriseBaseModel):
    """A comment or timeline update on an incident ticket."""
    author: str
    timestamp: str
    text: str


@dataclass
class IncidentTicket(EnterpriseBaseModel):
    """Core ITSM incident ticket model."""
    ticket_id: str
    employee_id: str
    category: str
    priority: PriorityEnum
    status: TicketStatusEnum
    title: str
    description: str
    created_at: str
    assigned_to: str = "IT-Support-L1"
    updated_at: Optional[str] = None
    comments: List[TicketComment] = field(default_factory=list)
    idempotency_key: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "IncidentTicket":
        clean = data.copy()
        if "priority" in clean and isinstance(clean["priority"], str):
            clean["priority"] = PriorityEnum(clean["priority"])
        if "status" in clean and isinstance(clean["status"], str):
            clean["status"] = TicketStatusEnum(clean["status"])
        if "comments" in clean and isinstance(clean["comments"], list):
            clean["comments"] = [
                TicketComment.from_dict(c) if isinstance(c, dict) else c
                for c in clean["comments"]
            ]
        return super().from_dict(clean)
