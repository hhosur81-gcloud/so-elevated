"""Unit tests for domain models and Tolerant Reader schema evolution (ENG-0001)."""

import unittest
from datetime import datetime


class TestDomainModels(unittest.TestCase):
    """Test suite verifying domain model serialization, validation, and tolerance."""

    def test_employee_profile_tolerant_reader(self):
        """Verify EmployeeProfile ingests extra unmapped upstream fields without error."""
        from src.models.employee import EmployeeProfile

        raw_payload = {
            "employee_id": "EMP-1001",
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@enterprise.com",
            "department": "Engineering",
            "role": "Senior Cloud Engineer",
            "pto_balance_hours": 120.0,
            "sick_leave_hours": 40.0,
            # Upstream WorkWeek API added new fields
            "future_workweek_attribute": "experimental_v3",
            "cost_center_code": 90812,
            "office_badge_id": "BADGE-88"
        }

        profile = EmployeeProfile.from_dict(raw_payload)
        self.assertEqual(profile.employee_id, "EMP-1001")
        self.assertEqual(profile.first_name, "Jane")
        self.assertEqual(profile.pto_balance_hours, 120.0)
        self.assertEqual(profile.department, "Engineering")

        # Verify serialization round-trip
        data = profile.to_dict()
        self.assertEqual(data["employee_id"], "EMP-1001")
        self.assertNotIn("future_workweek_attribute", data)

    def test_leave_request_validation(self):
        """Verify LeaveRequest models and calculations."""
        from src.models.employee import LeaveRequest, LeaveTypeEnum, LeaveStatusEnum

        leave = LeaveRequest(
            request_id="LOA-9081",
            employee_id="EMP-1001",
            leave_type=LeaveTypeEnum.MEDICAL,
            start_date="2026-09-01",
            end_date="2026-09-14",
            hours_requested=80.0,
            status=LeaveStatusEnum.CONFIRMED,
            idempotency_key="550e8400-e29b-41d4-a716-446655440000"
        )
        self.assertEqual(leave.leave_type, LeaveTypeEnum.MEDICAL)
        self.assertEqual(leave.status, LeaveStatusEnum.CONFIRMED)
        self.assertEqual(leave.hours_requested, 80.0)

    def test_incident_ticket_tolerant_reader(self):
        """Verify IncidentTicket model and PriorityEnum validation."""
        from src.models.ticket import IncidentTicket, PriorityEnum, TicketStatusEnum

        ticket_payload = {
            "ticket_id": "INC-10001",
            "employee_id": "EMP-1001",
            "category": "Hardware",
            "priority": "P3",
            "status": "OPEN",
            "title": "Broken Laptop Screen",
            "description": "Flickering display",
            "created_at": "2026-08-19T10:00:00Z",
            "assigned_to": "IT-Support-L1",
            "comments": [],
            # Extra upstream ITSM field
            "servicenow_sys_id": "sys_98712398412"
        }

        ticket = IncidentTicket.from_dict(ticket_payload)
        self.assertEqual(ticket.ticket_id, "INC-10001")
        self.assertEqual(ticket.priority, PriorityEnum.P3)
        self.assertEqual(ticket.status, TicketStatusEnum.OPEN)

    def test_session_state_and_turn_history(self):
        """Verify SessionState and TurnHistory models for multi-turn dialogues."""
        from src.models.session import SessionState, ConversationTurn

        turn = ConversationTurn(
            turn_id="turn-1",
            user_input="How many days of PTO do I have?",
            agent_response="You currently have 120 hours of PTO available.",
            acting_agent="workweek_agent",
            tool_invoked="workweek_get_pto_balance",
            latency_ms=320
        )

        session = SessionState(
            session_id="sess-abc-123",
            employee_id="EMP-1001",
            turns=[turn],
            pending_confirmation=None,
            is_revoked=False
        )

        self.assertEqual(session.session_id, "sess-abc-123")
        self.assertEqual(len(session.turns), 1)
        self.assertEqual(session.turns[0].tool_invoked, "workweek_get_pto_balance")
        self.assertFalse(session.is_revoked)


if __name__ == "__main__":
    unittest.main()
