"""WorkWeek Specialist Agent for HCM, Balances, and Leave Management (ADK Pattern)."""

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from src.config.settings import settings
from src.mcp.remote_mcp_client import RemoteWorkWeekClient
from src.models.session import PendingConfirmation
from src.repositories.filestore_repository import FileStoreRepository


class WorkWeekAgent:
    """Specialist sub-agent governing Human Capital Management (HCM) operations."""

    MONTHS_MAP = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12
    }

    def __init__(
        self,
        repository: Optional[FileStoreRepository] = None,
        mcp_client: Optional[RemoteWorkWeekClient] = None
    ):
        self.repo = repository or FileStoreRepository()
        self.mcp = mcp_client or RemoteWorkWeekClient(
            endpoint_url=settings.workweek_mcp_url,
            token=settings.workweek_mcp_token
        )

    def parse_natural_dates(self, text: str, default_year: int = 2026) -> List[str]:
        """Extract ISO, slash, and natural language dates (e.g. '16 sep', 'sep 16', '2026-09-01')."""
        # 1. ISO format: YYYY-MM-DD
        iso_dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        if iso_dates:
            return iso_dates

        # 2. Slash format: MM/DD/YYYY or MM/DD
        slash_dates = re.findall(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", text)
        if slash_dates:
            res = []
            for m, d, y in slash_dates:
                yr = int(y) if y else default_year
                if yr < 100:
                    yr += 2000
                res.append(f"{yr:04d}-{int(m):02d}-{int(d):02d}")
            return res

        # 3. Natural language formats
        month_keys = "|".join(self.MONTHS_MAP.keys())
        pattern_a = re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({month_keys})(?:\s+(\d{{4}}))?\b", re.IGNORECASE)
        pattern_b = re.compile(rf"\b({month_keys})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(\d{{4}}))?\b", re.IGNORECASE)

        extracted = []
        for m in pattern_a.finditer(text):
            day = int(m.group(1))
            month = self.MONTHS_MAP[m.group(2).lower()]
            yr = int(m.group(3)) if m.group(3) else default_year
            extracted.append((m.start(), f"{yr:04d}-{month:02d}-{day:02d}"))

        for m in pattern_b.finditer(text):
            month = self.MONTHS_MAP[m.group(1).lower()]
            day = int(m.group(2))
            yr = int(m.group(3)) if m.group(3) else default_year
            extracted.append((m.start(), f"{yr:04d}-{month:02d}-{day:02d}"))

        if extracted:
            extracted.sort(key=lambda x: x[0])
            return [d for _, d in extracted]

        return []

    def parse_duration(self, lowered_msg: str) -> Tuple[Optional[float], Optional[int]]:
        """Extract hours/days/weeks duration and calculate calendar span days."""
        hrs_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|hrs|hr|h)\b", lowered_msg)
        days_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:days|day|d)\b", lowered_msg)
        weeks_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:weeks|week|wks|wk)\b", lowered_msg)
        booking_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|hrs|days|d|weeks|week|wks|wk)?\s*of\s*(pto|sick|leave|medical|vacation|time\s*off)", lowered_msg)

        if hrs_match:
            hours = float(hrs_match.group(1))
            return hours, max(1, int(round(hours / 8.0)))
        elif days_match:
            d = float(days_match.group(1))
            return d * 8.0, max(1, int(round(d)))
        elif weeks_match:
            w = float(weeks_match.group(1))
            return w * 40.0, max(1, int(round(w * 7)))
        elif booking_match:
            val = float(booking_match.group(1))
            if val > 10:
                return val, max(1, int(round(val / 8.0)))
            else:
                return val * 8.0, max(1, int(round(val)))
        return None, None

    def get_balances(self, employee_id: str) -> Dict[str, Any]:
        """Fetch employee leave balances from live WorkWeek FastMCP server."""
        remote_res = self.mcp.get_employee_balances(employee_id)
        resp_text = remote_res.get("result", "Unable to retrieve balances from live WorkWeek server.")
        return {
            "success": True,
            "response": resp_text,
            "acting_agent": "workweek_agent",
            "tool_invoked": "workweek_get_pto_balances"
        }

    def process_leave_intent(
        self,
        user_message: str,
        employee_id: str
    ) -> Dict[str, Any]:
        """Evaluate PTO request parameters and generate elicitation prompt or confirmation gate."""
        lowered_msg = user_message.lower().strip()
        hours, calendar_span_days = self.parse_duration(lowered_msg)
        dates = self.parse_natural_dates(user_message)

        # 1. Missing both duration and dates
        if hours is None and not dates:
            resp_text = "I can help you submit a PTO request. How many hours or days would you like to take, and what are the start and end dates? (e.g., *'16 hours from 2026-09-01 to 2026-09-02'* or *'2 days from 2026-09-01 to 2026-09-02'*)"
            return {
                "success": True,
                "response": resp_text,
                "requires_confirmation": False,
                "acting_agent": "workweek_agent",
                "tool_invoked": "prompt_pto_details"
            }

        # 2. Missing dates only
        if hours is not None and not dates:
            resp_text = f"You'd like to request {hours:.1f} hours of PTO. What are the start and end dates for your time off? (e.g., *'from 2026-09-01 to 2026-09-02'* or *'starting 16 sep'*)"
            return {
                "success": True,
                "response": resp_text,
                "requires_confirmation": False,
                "acting_agent": "workweek_agent",
                "tool_invoked": "prompt_pto_details"
            }

        # 3. Dates provided (with or without explicit duration)
        if len(dates) >= 2:
            start_d = dates[0]
            end_d = dates[1]
            if hours is None:
                try:
                    s_dt = datetime.strptime(start_d, "%Y-%m-%d")
                    e_dt = datetime.strptime(end_d, "%Y-%m-%d")
                    days_count = max(1, (e_dt - s_dt).days + 1)
                    hours = float(days_count * 8.0)
                except Exception:
                    hours = 16.0
        else:
            start_d = dates[0]
            if hours is not None and calendar_span_days is not None:
                try:
                    s_dt = datetime.strptime(start_d, "%Y-%m-%d")
                    e_dt = s_dt + timedelta(days=calendar_span_days - 1)
                    end_d = e_dt.strftime("%Y-%m-%d")
                except Exception:
                    end_d = start_d
            else:
                hours = 8.0
                end_d = start_d

        leave_type = "Sick" if any(w in lowered_msg for w in ["sick", "medical", "illness"]) else "Vacation"

        prompt_msg = f"Please confirm: You are requesting {hours:.1f} hours of PTO from {start_d} to {end_d}. Shall I proceed with submitting this request?"
        pending = PendingConfirmation(
            action_type="SUBMIT_LEAVE",
            target_system="WORKWEEK",
            payload={
                "leave_type": leave_type,
                "start_date": start_d,
                "end_date": end_d,
                "hours": hours,
                "days": hours / 8.0,
                "idempotency_key": str(uuid.uuid4())
            },
            prompt_message=prompt_msg,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        return {
            "success": True,
            "response": prompt_msg,
            "requires_confirmation": True,
            "pending_confirmation": pending,
            "acting_agent": "workweek_agent",
            "tool_invoked": "enter_confirmation_gate"
        }

    def execute_confirmed_leave(
        self,
        employee_id: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute state mutation to live WorkWeek FastMCP server upon human approval."""
        raw_type = payload.get("leave_type", "Vacation")
        mapped_type = "Sick" if "sick" in str(raw_type).lower() or "medical" in str(raw_type).lower() else "Vacation"
        days_req = float(payload.get("days", payload.get("hours", 16.0) / 8.0))
        booking_res = self.mcp.request_time_off(
            employee_id=employee_id,
            start_date=payload["start_date"],
            end_date=payload["end_date"],
            leave_type=mapped_type,
            days=days_req
        )
        if booking_res.get("success", False):
            bal_res = self.mcp.get_employee_balances(employee_id)
            bal_text = bal_res.get("result", "")
            if bal_text:
                resp_text = f"Your leave request has been confirmed and submitted to WorkWeek.\n\n{bal_text}"
            else:
                resp_text = "Your leave request has been confirmed and submitted to WorkWeek. Remaining leave balances updated."
        else:
            resp_text = f"Leave booking failed: {booking_res.get('error', 'Unable to process time off request')}"

        return {
            "success": True,
            "response": resp_text,
            "requires_confirmation": False,
            "acting_agent": "workweek_agent",
            "tool_invoked": "workweek_submit_leave_request"
        }
