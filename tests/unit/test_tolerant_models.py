"""Unit tests verifying Tolerant Reader pattern across domain models (ENG-0001)."""
from agent.models.workweek import EmployeeProfile, PTOBalances, LeaveRequest
from agent.models.itsm import IncidentTicket, TicketComment


def test_employee_profile_tolerant_reader():
    """Verify EmployeeProfile safely ignores unknown upstream API fields."""
    raw_api_payload = {
        "employee_id": "EMP1001",
        "name": "Alex Chen",
        "email": "alex.chen@altostrat.com",
        "role": "Senior Cloud Architect",
        "home_address": "10 Marina Boulevard, Singapore",
        "phone_number": "+65 9123 4567",
        "manager_id": "MGR2001",
        # Unexpected new upstream fields from Workday/WorkWeek API
        "badge_color": "Blue",
        "workstation_ip": "10.200.1.45",
        "cost_center_v2": {"code": "CC-901", "allocation": 100},
    }
    profile = EmployeeProfile.model_validate(raw_api_payload)
    assert profile.employee_id == "EMP1001"
    assert profile.name == "Alex Chen"
    assert not hasattr(profile, "badge_color")


def test_pto_balances_tolerant_reader():
    """Verify PTOBalances safely handles extra fields and defaults."""
    raw_api_payload = {
        "employee_id": "EMP1001",
        "vacation_days_remaining": 14.5,
        "sick_days_remaining": 12.0,
        "future_accrual_projection": 3.5,  # Unexpected field
    }
    balances = PTOBalances.model_validate(raw_api_payload)
    assert balances.employee_id == "EMP1001"
    assert balances.vacation_days_remaining == 14.5
    assert balances.vacation_days_accrued == 0.0  # Safe default


def test_incident_ticket_tolerant_reader():
    """Verify IncidentTicket ingests nested comments and ignores metadata fields."""
    raw_api_payload = {
        "ticket_id": "INC123456",
        "requested_by": "EMP1001",
        "category": "Hardware",
        "short_description": "Laptop screen flicker",
        "priority": "2 - High",
        "status": "In Progress",
        "cmdb_ci_item": "MacBook-Pro-M3",  # Unexpected field
        "comments": [
            {
                "comment_id": "CMT-1",
                "author": "IT Agent",
                "comment_text": "Diagnostics requested",
                "internal_sys_id": "99401-AA",  # Unexpected nested field
            }
        ],
    }
    ticket = IncidentTicket.model_validate(raw_api_payload)
    assert ticket.ticket_id == "INC123456"
    assert ticket.priority == "2 - High"
    assert len(ticket.comments) == 1
    assert ticket.comments[0].author == "IT Agent"
