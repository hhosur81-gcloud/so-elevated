"""WorkWeek HCM Domain Models (FR-2.1 to FR-2.5)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from src.models.common import EnterpriseBaseModel


class LeaveTypeEnum(str, Enum):
    """Supported leave types in WorkWeek HCM."""
    PTO = "PTO"
    SICK = "SICK"
    MEDICAL = "MEDICAL"
    PARENTAL = "PARENTAL"
    BEREAVEMENT = "BEREAVEMENT"
    UNPAID = "UNPAID"


class LeaveStatusEnum(str, Enum):
    """Lifecycle status for a leave request."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


@dataclass
class LeaveRequest(EnterpriseBaseModel):
    """Represents an employee leave booking record."""
    request_id: str
    employee_id: str
    leave_type: LeaveTypeEnum
    start_date: str
    end_date: str
    hours_requested: float
    status: LeaveStatusEnum = LeaveStatusEnum.PENDING
    idempotency_key: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "LeaveRequest":
        clean = data.copy()
        if "leave_type" in clean and isinstance(clean["leave_type"], str):
            clean["leave_type"] = LeaveTypeEnum(clean["leave_type"])
        if "status" in clean and isinstance(clean["status"], str):
            clean["status"] = LeaveStatusEnum(clean["status"])
        return super().from_dict(clean)


@dataclass
class PTOBalance(EnterpriseBaseModel):
    """Employee PTO and sick leave hour balance."""
    employee_id: str
    pto_balance_hours: float
    sick_leave_hours: float
    floating_holiday_hours: float = 16.0
    last_accrual_date: Optional[str] = None


@dataclass
class EmployeeProfile(EnterpriseBaseModel):
    """Core employee profile in WorkWeek HCM."""
    employee_id: str
    first_name: str
    last_name: str
    email: str
    department: str
    role: str
    pto_balance_hours: float = 0.0
    sick_leave_hours: float = 0.0
    manager_id: Optional[str] = None
    leave_requests: List[LeaveRequest] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "EmployeeProfile":
        clean = data.copy()
        if "leave_requests" in clean and isinstance(clean["leave_requests"], list):
            clean["leave_requests"] = [
                LeaveRequest.from_dict(req) if isinstance(req, dict) else req
                for req in clean["leave_requests"]
            ]
        return super().from_dict(clean)
