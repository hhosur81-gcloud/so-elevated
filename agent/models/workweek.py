"""WorkWeek HCM Domain Models adhering to SemVer 2.0.0 & Tolerant Reader Pattern (ENG-0001)."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TolerantBaseModel(BaseModel):
    """Base model enforcing Tolerant Reader pattern: ignores unexpected upstream API fields."""
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=True,
    )


class EmployeeProfile(TolerantBaseModel):
    """Employee metadata profile schema."""
    employee_id: str
    name: str
    email: str
    role: str = Field(default="Employee")
    home_address: Optional[str] = None
    phone_number: Optional[str] = None
    manager_id: Optional[str] = None


class PTOBalances(TolerantBaseModel):
    """Employee PTO and Sick Leave balance ledger."""
    employee_id: str
    vacation_days_accrued: float = 0.0
    vacation_days_used: float = 0.0
    vacation_days_remaining: float = 0.0
    sick_days_accrued: float = 0.0
    sick_days_used: float = 0.0
    sick_days_remaining: float = 0.0


class LeaveRequest(TolerantBaseModel):
    """Leave submission record."""
    request_id: Optional[int] = None
    employee_id: str
    start_date: str
    end_date: str
    leave_type: str
    days: float
    status: str = "Pending"
    idempotency_key: Optional[str] = None


class LeaveRequestInput(TolerantBaseModel):
    """Input payload for requesting time off."""
    start_date: str
    end_date: str
    leave_type: str
    days: float


class ProfileUpdateInput(TolerantBaseModel):
    """Input payload for updating contact details."""
    address: str
    phone: str
