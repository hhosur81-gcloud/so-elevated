"""Primary HR Orchestrator Agent (Vertex ADK Dispatcher, ADR-0007, ADR-0009)."""

import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.agents.policy_agent import PolicyAgent
from src.config.security import JWTManager
from src.mcp.serviceimmediately_server import ServiceImmediatelyMCPServer
from src.mcp.workweek_server import WorkWeekMCPServer
from src.models.session import ConversationTurn, PendingConfirmation, SessionState
from src.repositories.filestore_repository import FileStoreRepository
from src.services.guardrail_service import DLPFilter, ModelArmorGateway


class PrimaryHROrchestrator:
    """Root multi-agent supervisor and conversational orchestrator."""

    SESSION_STORE = "sessions/active.json"
    TTL_SECONDS = 900  # 15 minutes (ADR-0009)

    def __init__(
        self,
        jwt_manager: Optional[JWTManager] = None,
        repository: Optional[FileStoreRepository] = None,
        policy_dir: str = "fixtures/sample_policies"
    ):
        self.jwt_manager = jwt_manager or JWTManager()
        self.repo = repository or FileStoreRepository()
        self.guardrail = ModelArmorGateway()
        self.dlp = DLPFilter()
        self.policy_agent = PolicyAgent(policy_dir=policy_dir)
        self.workweek_server = WorkWeekMCPServer(jwt_manager=self.jwt_manager, repository=self.repo)
        self.itsm_server = ServiceImmediatelyMCPServer(jwt_manager=self.jwt_manager, repository=self.repo)

    def _get_or_create_session(self, session_id: str, employee_id: str) -> SessionState:
        """Retrieve existing active session state or initialize new one with TTL check."""
        now = time.time()
        raw_session = self.repo.load_record(self.SESSION_STORE, session_id)

        if raw_session:
            last_activity = raw_session.get("last_activity_at_ts", 0)
            if now - last_activity > self.TTL_SECONDS or raw_session.get("is_revoked", False):
                raw_session = None

        if not raw_session:
            new_session = SessionState(
                session_id=session_id,
                employee_id=employee_id,
                turns=[],
                pending_confirmation=None,
                is_revoked=False,
                created_at=datetime.now(timezone.utc).isoformat(),
                last_activity_at=datetime.now(timezone.utc).isoformat()
            )
            raw_dict = new_session.to_dict()
            raw_dict["last_activity_at_ts"] = now
            self.repo.save_record(self.SESSION_STORE, session_id, raw_dict)
            return new_session

        return SessionState.from_dict(raw_session)

    def _save_session(self, session: SessionState) -> None:
        """Persist session state to atomic FileStore."""
        s_dict = session.to_dict()
        s_dict["last_activity_at_ts"] = time.time()
        self.repo.save_record(self.SESSION_STORE, session.session_id, s_dict)

    def process_turn(self, session_id: str, employee_id: str, user_message: str) -> Dict[str, Any]:
        """Execute a conversational turn across Security Sentinel, Session Router, and Sub-agents."""
        start_time = time.perf_counter()
        lowered_msg = user_message.lower().strip()

        # 1. Layer 0 Security Sentinel Gate (Model Armor)
        inspection = self.guardrail.inspect_inbound_prompt(user_message, employee_id=employee_id)
        if not inspection.is_valid:
            return {
                "success": False,
                "error_code": "SECURITY_BLOCKED",
                "response": inspection.sanitized_text,
                "category": inspection.category
            }

        # 2. Session Context Resolution
        session = self._get_or_create_session(session_id, employee_id)

        # 3. Explicit Session Reset Command Check (ADR-0009)
        if re.search(r"\b(reset|start\s*over|logout|clear\s*session)\b", lowered_msg):
            session.turns.clear()
            session.pending_confirmation = None
            session.is_revoked = False
            self._save_session(session)
            return {
                "success": True,
                "response": "Session context has been reset. How may I assist you today?",
                "requires_confirmation": False
            }

        # 4. Confirmation Gate Check (ADR-0007, Q4)
        if session.pending_confirmation:
            if re.search(r"\b(yes|confirm|proceed|submit|ok|sure|approve)\b", lowered_msg):
                pending = session.pending_confirmation
                session.pending_confirmation = None
                
                if pending.target_system == "WORKWEEK" and pending.action_type == "SUBMIT_LEAVE":
                    token = self.jwt_manager.generate_delegated_token(employee_id, scopes=["hcm:write"])
                    p_load = pending.payload
                    booking_res = self.workweek_server.workweek_submit_leave_request(
                        employee_id=employee_id,
                        leave_type=p_load["leave_type"],
                        start_date=p_load["start_date"],
                        end_date=p_load["end_date"],
                        hours=p_load["hours"],
                        bearer_token=token,
                        idempotency_key=p_load.get("idempotency_key")
                    )
                    
                    if booking_res["success"]:
                        resp_text = f"Your leave request ({booking_res['data']['request_id']}) has been confirmed and submitted. Remaining PTO balance: {booking_res['data']['remaining_pto_hours']} hours."
                    else:
                        resp_text = f"Leave booking failed: {booking_res.get('error', 'Unknown error')}"

                    self._record_turn(session, user_message, resp_text, "workweek_agent", "workweek_submit_leave_request", start_time)
                    self._save_session(session)
                    return {"success": True, "response": resp_text, "requires_confirmation": False}

            elif re.search(r"\b(no|cancel|abort|stop|don't)\b", lowered_msg):
                session.pending_confirmation = None
                resp_text = "The pending action has been cancelled. Let me know if you need anything else."
                self._record_turn(session, user_message, resp_text, "orchestrator", None, start_time)
                self._save_session(session)
                return {"success": True, "response": resp_text, "requires_confirmation": False}

        # 5. Compensation / Salary Privacy Guardrail
        if "salary" in lowered_msg or "compensation" in lowered_msg or "pay rate" in lowered_msg:
            # Check if asking about someone else vs own
            names_or_titles = ["marcus", "jane", "john", "maria", "alex", "vp", "executive", "director", "manager", "other"]
            is_asking_about_others = any(n in lowered_msg for n in names_or_titles) and not ("my salary" in lowered_msg or "my compensation" in lowered_msg)
            
            if is_asking_about_others:
                resp_text = "Individual employee compensation and salary records are strictly confidential and not accessible through the HR Assistant."
            else:
                resp_text = "Your individual compensation, salary, and pay stubs are managed securely in the Workday Payroll portal. For privacy and compliance reasons, salary figures are not displayed in conversational chat."

            self._record_turn(session, user_message, resp_text, "orchestrator", "privacy_guardrail", start_time)
            self._save_session(session)
            return {"success": True, "response": resp_text, "requires_confirmation": False}

        # 6. Intent Classification & Routing

        # A. WorkWeek PTO Leave Booking Request (Enters Confirmation Gate)
        booking_match = re.search(r"(\d+)\s*(?:hours|hrs|days|d)?\s*of\s*(pto|sick|leave|medical)", lowered_msg)
        if "pto" in lowered_msg and ("take" in lowered_msg or "request" in lowered_msg or "book" in lowered_msg):
            hours = 16.0
            if booking_match:
                hours = float(booking_match.group(1))

            dates = re.findall(r"\d{4}-\d{2}-\d{2}", user_message)
            start_d = dates[0] if len(dates) > 0 else "2026-09-01"
            end_d = dates[1] if len(dates) > 1 else "2026-09-02"

            prompt_msg = f"Please confirm: You are requesting {hours} hours of PTO from {start_d} to {end_d}. Shall I proceed with submitting this request?"
            session.pending_confirmation = PendingConfirmation(
                action_type="SUBMIT_LEAVE",
                target_system="WORKWEEK",
                payload={"leave_type": "PTO", "start_date": start_d, "end_date": end_d, "hours": hours, "idempotency_key": str(uuid.uuid4())},
                prompt_message=prompt_msg,
                created_at=datetime.now(timezone.utc).isoformat()
            )
            self._record_turn(session, user_message, prompt_msg, "orchestrator", "enter_confirmation_gate", start_time)
            self._save_session(session)
            return {"success": True, "response": prompt_msg, "requires_confirmation": True}

        # B. WorkWeek PTO Balance Query (Explicit balance check)
        if ("pto" in lowered_msg and ("balance" in lowered_msg or "how many" in lowered_msg or "how much" in lowered_msg or "remaining" in lowered_msg or "available" in lowered_msg)) or \
           ("balance" in lowered_msg and "pto" in lowered_msg):
            token = self.jwt_manager.generate_delegated_token(employee_id, scopes=["hcm:read"])
            b_res = self.workweek_server.workweek_get_pto_balances(employee_id, token)
            if b_res["success"]:
                pto_h = b_res["data"]["pto_balance_hours"]
                sick_h = b_res["data"]["sick_leave_hours"]
                resp_text = f"You currently have {pto_h} hours of PTO and {sick_h} hours of sick leave available."
            else:
                resp_text = "I was unable to retrieve your PTO balances at this moment."

            self._record_turn(session, user_message, resp_text, "workweek_agent", "workweek_get_pto_balances", start_time)
            self._save_session(session)
            return {"success": True, "response": resp_text, "requires_confirmation": False}

        # C. General Leave Programs Overview (Ambiguous Leave Query)
        if re.search(r"how\s+many\s+(weeks|days|months)\s+of\s+leave", lowered_msg) or lowered_msg in ["what leave do i get", "what leaves are available", "leave entitlement"]:
            resp_text = """According to company policy, full-time employees are eligible for several leave programs:

• **Paid Time Off (PTO)**: 160 hours (20 business days / 4 weeks) accrued annually ([Section 3.1](https://intranet.company.com/policies/hr-2026-leave.pdf))
• **Parental Leave**: Up to 16 weeks fully paid within the first 12 months ([Section 3.3](https://intranet.company.com/policies/hr-2026-leave.pdf))
• **Short-Term Medical LOA**: Up to 12 weeks with 100% salary continuation upon medical certification ([Section 3.4](https://intranet.company.com/policies/hr-2026-leave.pdf))
• **Bereavement Leave**: Up to 5 consecutive paid business days for immediate family ([Section 3.2](https://intranet.company.com/policies/hr-2026-leave.pdf))"""

            self._record_turn(session, user_message, resp_text, "policy_agent", "leave_overview", start_time)
            self._save_session(session)
            return {"success": True, "response": resp_text, "requires_confirmation": False}

        # D. Policy Q&A Inquiry
                # Resolve employee role from WorkWeek for Query-time ACL
        profile = self.repo.load_record("workweek/employees.json", employee_id)
        emp_role = "Executive" if profile and profile.get("role") in ["VP of Engineering", "Executive", "VP"] else "Employee"
        
        p_res = self.policy_agent.answer_policy_query(user_message, employee_role=emp_role)
        resp_text = p_res["answer"]
        if p_res.get("citation_label") and p_res.get("citation_url"):
            resp_text += f"\n\nSource: [{p_res['citation_label']}]({p_res['citation_url']})"

        self._record_turn(session, user_message, resp_text, "policy_agent", "search_policies", start_time)
        self._save_session(session)
        return {"success": True, "response": resp_text, "requires_confirmation": False}

    def _record_turn(
        self,
        session: SessionState,
        user_input: str,
        response: str,
        agent: str,
        tool: Optional[str],
        start_time: float
    ) -> None:
        """Record turn history with DLP masking for audit safety."""
        latency = int((time.perf_counter() - start_time) * 1000.0)
        masked_input = self.dlp.redact_for_logs(user_input)
        masked_response = self.dlp.redact_for_logs(response)

        turn = ConversationTurn(
            turn_id=f"turn-{len(session.turns) + 1}",
            user_input=masked_input,
            agent_response=masked_response,
            acting_agent=agent,
            tool_invoked=tool,
            latency_ms=latency,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        session.turns.append(turn)
