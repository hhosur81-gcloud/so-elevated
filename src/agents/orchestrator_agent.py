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
                # Expired TTL -> initialize fresh session
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
        if re.search(r"\b(reset|start\s*over|logout|clear\s*session)\b", user_message.lower()):
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
            if re.search(r"\b(yes|confirm|proceed|submit|ok|sure|approve)\b", user_message.lower()):
                # Execute pending mutation
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

            elif re.search(r"\b(no|cancel|abort|stop|don't)\b", user_message.lower()):
                session.pending_confirmation = None
                resp_text = "The pending action has been cancelled. Let me know if you need anything else."
                self._record_turn(session, user_message, resp_text, "orchestrator", None, start_time)
                self._save_session(session)
                return {"success": True, "response": resp_text, "requires_confirmation": False}

        # 5. Intent Classification & Routing

        # A. WorkWeek PTO Leave Booking Request (Enters Confirmation Gate)
        booking_match = re.search(r"(\d+)\s*(?:hours|hrs|days|d)?\s*of\s*(pto|sick|leave|medical)", user_message.lower())
        if "pto" in user_message.lower() and ("take" in user_message.lower() or "request" in user_message.lower() or "book" in user_message.lower()):
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

        # B. WorkWeek PTO Balance Query
        if "pto" in user_message.lower() or "balance" in user_message.lower() or "hours" in user_message.lower():
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

        # C. Policy Q&A Inquiry
        p_res = self.policy_agent.answer_policy_query(user_message, employee_role="Employee")
        resp_text = p_res["answer"]
        if p_res.get("citation_label"):
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
