"""ServiceImmediately ITSM Domain Models adhering to Tolerant Reader Pattern (ENG-0001)."""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from .workweek import TolerantBaseModel


class TicketComment(TolerantBaseModel):
    """Activity timeline comment record."""
    comment_id: Optional[str] = None
    ticket_id: Optional[str] = None
    author: str
    comment_text: str
    created_at: Optional[str] = None


class IncidentTicket(TolerantBaseModel):
    """ServiceImmediately incident ticket schema."""
    ticket_id: str
    requested_by: str
    category: str
    short_description: str
    priority: str = Field(default="3 - Medium")
    status: str = Field(default="New")
    assignment_group: str = Field(default="Service Desk")
    created_at: Optional[str] = None
    comments: List[TicketComment] = Field(default_factory=list)


class TicketCreateInput(TolerantBaseModel):
    """Input payload for logging a new support ticket."""
    requested_by: str
    category: str
    short_description: str
    priority: str = "3 - Medium"
    assignment_group: str = "Service Desk"
    idempotency_key: Optional[str] = None


class TicketStatusUpdateInput(TolerantBaseModel):
    """Input payload for transitioning ticket state."""
    ticket_id: str
    status: str
    resolution_notes: str = ""
    updated_by: str = "System"
