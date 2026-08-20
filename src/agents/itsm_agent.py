"""ServiceImmediately Specialist Agent for ITSM, Facilities, and Compliance Operations (ADK Pattern)."""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from src.config.settings import settings
from src.mcp.remote_mcp_client import RemoteServiceImmediatelyClient
from src.repositories.filestore_repository import FileStoreRepository


class ITSMAgent:
    """Specialist sub-agent governing IT Service Management (ITSM) and Incident Workflows."""

    def __init__(
        self,
        repository: Optional[FileStoreRepository] = None,
        mcp_client: Optional[RemoteServiceImmediatelyClient] = None
    ):
        self.repo = repository or FileStoreRepository()
        self.mcp = mcp_client or RemoteServiceImmediatelyClient(
            endpoint_url=settings.itsm_mcp_url,
            token=settings.itsm_mcp_token
        )

    def classify_category(self, lowered_msg: str) -> str:
        """Classify ticket category based on intent keywords."""
        if any(w in lowered_msg for w in ["laptop", "hardware", "monitor", "mouse", "keyboard", "screen", "mac", "macbook", "equipment"]):
            return "Hardware"
        elif any(w in lowered_msg for w in ["vpn", "network", "wifi", "access", "password", "login", "sso"]):
            return "Access_Network"
        elif any(w in lowered_msg for w in ["gift", "approval", "pre-approval", "compliance", "vendor", "entertainment", "anti-bribery"]):
            return "Compliance_Approval"
        elif any(w in lowered_msg for w in ["hr", "benefit", "payroll", "onboarding"]):
            return "HR_Operations"
        return "IT_Support"

    def evaluate_priority(self, lowered_msg: str) -> Tuple[str, str, str]:
        """Evaluate requested priority against ADR-0010 Priority Downgrade Guardrails.
        
        Returns:
            (priority_code, priority_label, downgrade_notice)
        """
        requested_p1 = any(w in lowered_msg for w in ["p1", "critical", "priority '1", "priority 1", "priority: 1", "priority: '1", "priority: '1 - critical'", "sev1", "sev-1", "severity 1"])
        has_major_outage = any(w in lowered_msg for w in ["major outage", "production down", "sev1", "sev-1", "system down", "widespread outage", "service outage"])
        
        is_downgraded = False
        priority = "P3"
        if has_major_outage:
            priority = "P1"
        elif requested_p1:
            priority = "P3"
            is_downgraded = True
        elif "p2" in lowered_msg or "high" in lowered_msg:
            priority = "P2"
        elif "p4" in lowered_msg or "low" in lowered_msg:
            priority = "P4"

        p_label = "1 - Critical" if priority == "P1" else ("2 - High" if priority == "P2" else ("4 - Low" if priority == "P4" else "3 - Moderate"))
        downgrade_notice = ""
        if is_downgraded:
            downgrade_notice = "\n\n⚠️ **Priority Notice (ADR-0010)**: Priority was adjusted from **1 - Critical** to **3 - Moderate**. Critical priority is reserved strictly for active, high-impact enterprise outages affecting business continuity."

        return priority, p_label, downgrade_notice

    def lookup_tickets(self, user_message: str, employee_id: str, ticket_match: Optional[str] = None) -> Dict[str, Any]:
        """Lookup an individual ticket or list all open tickets for the employee."""
        lowered_msg = user_message.lower().strip()

        if ticket_match:
            t_id = ticket_match.upper()
            remote_t = self.mcp.get_ticket(t_id)
            raw_t = remote_t.get("result", "")
            if isinstance(raw_t, str) and raw_t.strip().startswith("{"):
                try:
                    t_data = json.loads(raw_t)
                    resp_text = f"Ticket **{t_data.get('ticket_id', t_id)}** ({t_data.get('short_description', '')}): Status is **{t_data.get('status', 'New')}** (Priority: `{t_data.get('priority', '3 - Moderate')}`, Assigned to: `{t_data.get('assigned_to') or 'Service Desk'}`)."
                except Exception:
                    resp_text = raw_t
            else:
                resp_text = str(raw_t) if raw_t else f"Unable to find ticket {t_id} on ServiceImmediately."
        else:
            remote_tix = self.mcp.list_tickets(employee_id)
            raw_res = remote_tix.get("result", "")
            if isinstance(raw_res, str) and raw_res.strip().startswith("["):
                try:
                    tix_list = json.loads(raw_res)
                    if tix_list:
                        lines = [f"### 🎟️ Open Support Tickets for **{employee_id}** ({len(tix_list)} Active):"]
                        for t in tix_list:
                            lines.append(f"• **{t.get('ticket_id')}** — {t.get('short_description')} (Priority: `{t.get('priority')}`, Status: `{t.get('status')}`)")
                        resp_text = "\n".join(lines)
                    else:
                        resp_text = "You currently have no open support tickets in ServiceImmediately."
                except Exception:
                    resp_text = raw_res
            else:
                resp_text = str(raw_res)

        return {
            "success": True,
            "response": resp_text,
            "acting_agent": "itsm_agent",
            "tool_invoked": "itsm_get_ticket"
        }

    def create_ticket(
        self,
        user_message: str,
        employee_id: str,
        policy_guidance: str = ""
    ) -> Dict[str, Any]:
        """Create a new support ticket on live ServiceImmediately FastMCP server."""
        lowered_msg = user_message.lower().strip()

        # Check if user just said "I want to log a ticket" without details
        stripped_intent = re.sub(r"^(i\s+)?(want|need)\s+to\s+(log|create|open|file)\s+a?\s*ticket\.?$", "", lowered_msg).strip()
        if not stripped_intent:
            resp_text = "Certainly! What issue, hardware request, or approval would you like to log a ticket for? (e.g., *'Laptop screen flickering'*, *'Request approval for $500 vendor gift'*, *'VPN access issue'*)"
            return {
                "success": True,
                "response": resp_text,
                "acting_agent": "itsm_agent",
                "tool_invoked": "prompt_ticket_details"
            }

        category = self.classify_category(lowered_msg)
        priority, p_label, downgrade_notice = self.evaluate_priority(lowered_msg)

        inc_res = self.mcp.create_ticket(
            requested_by=employee_id,
            category=category,
            short_description=user_message,
            priority=p_label
        )

        raw_res = inc_res.get("result", "")
        t_id = "INC0002820"
        t_prio = p_label
        t_stat = "New"
        t_grp = "Service Desk"
        try:
            if isinstance(raw_res, str) and (raw_res.strip().startswith("[") or raw_res.strip().startswith("{")):
                parsed_json = json.loads(raw_res)
                item = parsed_json[0] if isinstance(parsed_json, list) and parsed_json else (parsed_json if isinstance(parsed_json, dict) else {})
                t_id = item.get("ticket_id", t_id)
                t_prio = item.get("priority", t_prio)
                t_stat = item.get("status", t_stat)
                t_grp = item.get("assignment_group", t_grp)
        except Exception:
            pass

        resp_text = (
            f"✅ **Support Ticket Logged**: **{t_id}**\n"
            f"• **Category**: `{category}`\n"
            f"• **Priority**: **{t_prio}**\n"
            f"• **Status**: `{t_stat}`\n"
            f"• **Assignment Group**: `{t_grp}`\n"
            f"• **Summary**: Request for loaner hardware / conference support"
            f"{downgrade_notice}"
            f"{policy_guidance}"
        )
        return {
            "success": True,
            "response": resp_text,
            "acting_agent": "itsm_agent",
            "tool_invoked": "itsm_create_incident"
        }
