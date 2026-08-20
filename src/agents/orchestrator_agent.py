"""Primary HR Orchestrator Agent (Vertex ADK Supervisor Pattern, ADR-0005, ADR-0007, ADR-0009)."""

import json
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.agents.itsm_agent import ITSMAgent
from src.agents.policy_agent import PolicyAgent
from src.agents.workweek_agent import WorkWeekAgent
from src.config.security import JWTManager
from src.services.guardrail_service import DLPFilter, ModelArmorGateway
from src.models.session import ConversationTurn, PendingConfirmation, SessionState
from src.repositories.filestore_repository import FileStoreRepository


class PrimaryHROrchestrator:
    """Root multi-agent supervisor orchestrating sub-agents (WorkWeek, ITSM, Policy, Security)."""

    SESSION_STORE = "sessions/active.json"
    TTL_SECONDS = 900  # 15 minutes (ADR-0009)

    def __init__(
        self,
        jwt_manager: Optional[JWTManager] = None,
        repository: Optional[FileStoreRepository] = None,
        policy_dir: str = "fixtures/sample_policies",
        workweek_agent: Optional[WorkWeekAgent] = None,
        itsm_agent: Optional[ITSMAgent] = None,
        policy_agent: Optional[PolicyAgent] = None
    ):
        self.jwt_manager = jwt_manager or JWTManager()
        self.repo = repository or FileStoreRepository()
        self.guardrail = ModelArmorGateway()
        self.dlp = DLPFilter()
        
        # Dedicated Specialist Sub-Agents (Hierarchical ADK Pattern)
        self.policy_agent = policy_agent or (PolicyAgent(policy_dir=policy_dir) if policy_dir else PolicyAgent())
        self.workweek_agent = workweek_agent or WorkWeekAgent(repository=self.repo)
        self.itsm_agent = itsm_agent or ITSMAgent(repository=self.repo)

        # Backward compatibility aliases for direct MCP access if referenced
        self.remote_workweek = self.workweek_agent.mcp
        self.remote_itsm = self.itsm_agent.mcp

    def _parse_natural_dates(self, text: str, default_year: int = 2026) -> List[str]:
        """Delegate date extraction to WorkWeek specialist."""
        return self.workweek_agent.parse_natural_dates(text, default_year=default_year)

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

    AGENT_METADATA = {
        "workweek_agent": {
            "name": "WorkWeek Agent",
            "short_name": "WorkWeek",
            "badge": "💼 WorkWeek Agent",
            "role": "HCM & Time-off Specialist"
        },
        "itsm_agent": {
            "name": "ITSM Agent",
            "short_name": "ITSM",
            "badge": "🎫 ITSM Agent",
            "role": "ServiceImmediately Specialist"
        },
        "policy_agent": {
            "name": "Policy Specialist",
            "short_name": "Policy",
            "badge": "📖 Policy Specialist",
            "role": "OKF Grounding Specialist"
        },
        "orchestrator": {
            "name": "HR Supervisor",
            "short_name": "Supervisor",
            "badge": "👑 HR Supervisor",
            "role": "Root Multi-Agent Orchestrator"
        },
        "security_sentinel": {
            "name": "Security Sentinel",
            "short_name": "Security",
            "badge": "🛡️ Security Sentinel",
            "role": "Layer 0 Model Armor Guardrail"
        }
    }

    def _format_result(self, result: Dict[str, Any], acting_agent: str = "orchestrator") -> Dict[str, Any]:
        """Enrich turn response with standardized agent branding and badges for Web/API consumers."""
        meta = self.AGENT_METADATA.get(acting_agent, self.AGENT_METADATA["orchestrator"])
        result["acting_agent"] = acting_agent
        result["agent_name"] = meta["name"]
        result["agent_badge"] = meta["badge"]
        result["agent_short_name"] = meta["short_name"]
        return result

    def process_turn(self, session_id: str, employee_id: str, user_message: str) -> Dict[str, Any]:
        """Execute a conversational turn across Security Sentinel, Session Router, and Sub-agents."""
        start_time = time.perf_counter()
        lowered_msg = user_message.lower().strip()

        # 1. Layer 0 Security Sentinel Gate (Model Armor)
        inspection = self.guardrail.inspect_inbound_prompt(user_message, employee_id=employee_id)
        if not inspection.is_valid:
            return self._format_result({
                "success": False,
                "error_code": "SECURITY_BLOCKED",
                "response": inspection.sanitized_text,
                "category": inspection.category,
                "requires_confirmation": False
            }, acting_agent="security_sentinel")

        # 2. Session Context Resolution
        session = self._get_or_create_session(session_id, employee_id)

        # 3. Explicit Session Reset Command Check (ADR-0009)
        if re.search(r"\b(reset|start\s*over|logout|clear\s*session)\b", lowered_msg):
            session.turns.clear()
            session.pending_confirmation = None
            session.is_revoked = False
            self._save_session(session)
            return self._format_result({
                "success": True,
                "response": "Session context has been reset. How may I assist you today?",
                "requires_confirmation": False
            }, acting_agent="orchestrator")

        # 4. Confirmation Gate Check (ADR-0007, Q4)
        if session.pending_confirmation:
            dates = self.workweek_agent.parse_natural_dates(user_message)
            has_dates = len(dates) > 0
            has_duration = bool(re.search(r"\d+(?:\.\d+)?\s*(?:hours|hrs|hr|h|days|day|d|weeks|week|wks|wk)\b", lowered_msg))
            is_revision_attempt = (
                has_dates
                or has_duration
                or any(w in lowered_msg for w in ["revise", "change", "instead", "make it", "update to", "mean", "meant", "actually", "prefer"])
            )

            if re.search(r"\b(yes|confirm|proceed|submit|ok|sure|approve)\b", lowered_msg) and not re.search(r"\b(no|cancel|abort|revise|change|instead|don't)\b", lowered_msg):
                pending = session.pending_confirmation
                session.pending_confirmation = None
                
                if pending.target_system == "WORKWEEK" and pending.action_type == "SUBMIT_LEAVE":
                    res = self.workweek_agent.execute_confirmed_leave(employee_id, pending.payload)
                    self._record_turn(session, user_message, res["response"], res.get("acting_agent", "workweek_agent"), res.get("tool_invoked", "workweek_submit_leave_request"), start_time)
                    self._save_session(session)
                    return self._format_result(res, acting_agent="workweek_agent")

            elif is_revision_attempt:
                session.pending_confirmation = None
                # Intentionally fall through so revised parameters are processed below

            elif re.search(r"\b(no|cancel|abort|stop|don't|dont|nevermind|nope|nah)\b", lowered_msg):
                session.pending_confirmation = None
                resp_text = "The pending action has been cancelled. Let me know if you need anything else."
                self._record_turn(session, user_message, resp_text, "orchestrator", None, start_time)
                self._save_session(session)
                return self._format_result({"success": True, "response": resp_text, "requires_confirmation": False}, acting_agent="orchestrator")

        # 5. Compensation / Salary Privacy Guardrail
        if "salary" in lowered_msg or "compensation" in lowered_msg or "pay rate" in lowered_msg:
            names_or_titles = ["marcus", "jane", "john", "maria", "alex", "vp", "executive", "director", "manager", "other"]
            is_asking_about_others = any(n in lowered_msg for n in names_or_titles) and not ("my salary" in lowered_msg or "my compensation" in lowered_msg)
            
            if is_asking_about_others:
                resp_text = "Individual employee compensation and salary records are strictly confidential and not accessible through the HR Assistant."
                self._record_turn(session, user_message, resp_text, "orchestrator", "privacy_guardrail", start_time)
                self._save_session(session)
                return self._format_result({"success": True, "response": resp_text, "requires_confirmation": False}, acting_agent="orchestrator")
            elif "my salary" in lowered_msg or "how much do i make" in lowered_msg:
                resp_text = "Your individual compensation, salary, and pay stubs are managed securely in the Workday Payroll portal. For privacy and compliance reasons, salary figures are not displayed in conversational chat."
                self._record_turn(session, user_message, resp_text, "orchestrator", "privacy_guardrail", start_time)
                self._save_session(session)
                return self._format_result({"success": True, "response": resp_text, "requires_confirmation": False}, acting_agent="orchestrator")

        # 6. Intent Classification & Routing

        # Greetings & Help Intent (Supervisor Level)
        is_greeting = bool(re.search(r"\b(hello|hi|hey|good\s*(morning|afternoon|evening)|howdy|greetings|help|help\s*me|who\s*are\s*you|what\s*(else\s*)?can\s*you\s*(do|help\s*with)|what\s*(else\s*)?do\s*you\s*do|what\s*are\s*your\s*capabilities|what\s*services\s*do\s*you\s*offer|what\s*can\s*i\s*ask|capabilities|features|menu)\b", lowered_msg))
        if is_greeting:
            profile = self.repo.load_record("workweek/employees.json", employee_id)
            first_name = profile.get("first_name", "") if profile else ""
            greeting_name = f", {first_name}" if first_name else ""
            resp_text = f"""Hello{greeting_name}! 👋 I am your Enterprise HR & IT Assistant powered by Vertex AI and FastMCP.

Here is a full breakdown of what I can help you with:

### 🌴 1. WorkWeek HCM (Time Off & Leave)
• **Check Balances**: Look up your current vacation and sick leave days remaining.
• **Book Time Off**: Request PTO, vacation, or medical leave (with multi-step confirmation gates).
• **Manage Leaves**: View your leave request history or cancel pending time-off.

### 🎫 2. ServiceImmediately ITSM (IT Support & Hardware)
• **Submit Support Tickets**: Request loaner laptops, monitors, replacement accessories, VPN/SSO access, or facilities orders.
• **Track Tickets**: Check real-time ticket status, assigned groups, and technician updates.
• **Priority Guardrails**: Automatic ADR-0010 triage and downgrade protection for non-critical requests.

### 📖 3. Policy Specialist (Enterprise Knowledge Base)
• **Leave Programs**: Bereavement, baby bonding, parental leave, and medical LOA rules.
• **Travel & Expenses**: Frugality rules, booking timelines, $120/day meal caps, and combining vacation with business trips.
• **Allowances & Compliance**: $500 home office equipment allowance, internet reimbursement, and gift/entertainment pre-approval thresholds.

### 🛡️ 4. Security Sentinel (Model Armor & DLP)
• **Enterprise Safety**: Active protection against prompt injections and jailbreaks.
• **Data Privacy**: Automatic redaction and masking of sensitive SPII (SSNs, credit card numbers, phone numbers).

Feel free to ask a policy question, check your balances, or log an IT ticket!"""
            self._record_turn(session, user_message, resp_text, "orchestrator", "greeting", start_time)
            self._save_session(session)
            return self._format_result({"success": True, "response": resp_text, "requires_confirmation": False}, acting_agent="orchestrator")

        is_pto_balance_query = (
            ("pto" in lowered_msg and ("balance" in lowered_msg or "how many" in lowered_msg or "how much" in lowered_msg or "remaining" in lowered_msg or "available" in lowered_msg)) or
            ("balance" in lowered_msg and "pto" in lowered_msg) or
            ("leave balance" in lowered_msg or "vacation balance" in lowered_msg or "my balances" in lowered_msg)
        )

        ticket_create_patterns = [
            r"\b(open|create|log|file|submit|raise)\s+(?:an?\s+)?(?:[\w\-]+\s+)*(?:ticket|incident|case|request|inquiry|issue)\b",
            r"\b(want|need)\s+to\s+(open|create|log|file|submit|raise)\s+(?:an?\s+)?(?:[\w\-]+\s+)*(?:ticket|incident|case|request|inquiry|issue)\b",
            r"\b(order|request|need|get)\s+(?:an?\s+)?(?:new\s+)?(loaner|laptop|keyboard|mouse|monitor|hardware|equipment|headset|charger|mac\s*pro|macbook)\b",
            r"\b(ticket|incident)\b.*\b(broken|damaged|stolen|lost|flickering|crash|replace|replacement|repair|new\s+mouse|new\s+laptop|new\s+keyboard)\b"
        ]
        is_ticket_intent = any(re.search(p, lowered_msg) for p in ticket_create_patterns)

        # A. WorkWeek PTO Leave Booking Request
        was_awaiting_pto = False
        was_confirming_leave = False
        if session.turns:
            last_turn = session.turns[-1]
            last_tool = getattr(last_turn, "tool_invoked", "")
            if last_tool == "prompt_pto_details":
                was_awaiting_pto = True
            elif last_tool == "enter_confirmation_gate":
                was_confirming_leave = True

        dates = self.workweek_agent.parse_natural_dates(user_message)
        has_dates = len(dates) > 0
        has_duration = bool(re.search(r"\d+(?:\.\d+)?\s*(?:hours|hrs|hr|h|days|day|d|weeks|week|wks|wk)\b", lowered_msg))

        is_pto_booking = (
            not is_ticket_intent and (
                bool(re.search(r"\b(request|book|take|apply\s+for|schedule)\s+(?:an?\s+)?(?:[\w\-]+\s+)?\b(pto|vacation|time\s*off|leave)\b", lowered_msg))
                or (
                    bool(re.search(r"\b(pto|vacation|time\s*off|time-off|annual\s+leave)\b", lowered_msg))
                    and any(w in lowered_msg for w in ["request", "book", "take", "apply", "schedule", "submit", "want", "need", "revise", "change"])
                    and not is_pto_balance_query
                    and not ("policy" in lowered_msg or "rules" in lowered_msg or "can i" in lowered_msg or "allowed" in lowered_msg)
                )
            )
            or (was_awaiting_pto and (has_dates or has_duration))
            or (was_confirming_leave and (has_dates or has_duration))
            or (has_dates and has_duration and not is_pto_balance_query and not is_ticket_intent and not ("policy" in lowered_msg or "rules" in lowered_msg or "can i" in lowered_msg))
        )

        if is_pto_booking and not is_pto_balance_query:
            res = self.workweek_agent.process_leave_intent(user_message, employee_id)
            if res.get("pending_confirmation"):
                session.pending_confirmation = res["pending_confirmation"]
            self._record_turn(session, user_message, res["response"], res.get("acting_agent", "workweek_agent"), res.get("tool_invoked", "prompt_pto_details"), start_time)
            self._save_session(session)
            return self._format_result({
                "success": res.get("success", True),
                "response": res["response"],
                "requires_confirmation": res.get("requires_confirmation", False)
            }, acting_agent="workweek_agent")

        # B. WorkWeek PTO Balance Query
        if is_pto_balance_query:
            res = self.workweek_agent.get_balances(employee_id)
            self._record_turn(session, user_message, res["response"], res.get("acting_agent", "workweek_agent"), res.get("tool_invoked", "workweek_get_pto_balances"), start_time)
            self._save_session(session)
            return self._format_result({"success": True, "response": res["response"], "requires_confirmation": False}, acting_agent="workweek_agent")

        # C. ITSM Ticket Lookup Query
        ticket_match = re.search(r"\b(INC[0-9]+|INC-[A-Z0-9]+|SEC-[A-Z0-9]+)\b", user_message, re.IGNORECASE)
        is_ticket_lookup = (ticket_match and any(w in lowered_msg for w in ["status", "check", "track", "view", "show", "what is"])) or \
                           (any(p in lowered_msg for p in ["list my tickets", "show my tickets", "my tickets", "my open tickets", "list tickets", "open tickets", "view tickets", "ticket status", "support tickets"]) and not is_ticket_intent)
        
        if is_ticket_lookup and not is_ticket_intent:
            t_id = ticket_match.group(1) if ticket_match else None
            res = self.itsm_agent.lookup_tickets(user_message, employee_id, ticket_match=t_id)
            self._record_turn(session, user_message, res["response"], res.get("acting_agent", "itsm_agent"), res.get("tool_invoked", "itsm_get_ticket"), start_time)
            self._save_session(session)
            return self._format_result({"success": True, "response": res["response"], "requires_confirmation": False}, acting_agent="itsm_agent")

        # D. ITSM Ticket Creation Intent
        if is_ticket_intent:
            # Check for compound policy query in the same message
            has_policy_subquery = any(w in lowered_msg for w in [
                "can i claim", "can i expense", "is it eligible", "what is the policy", "allowance",
                "reimburse", "reimbursement", "home office", "gift card", "policy for", "stipend",
                "can i do that", "extra day", "extra day off", "business travel", "can i take", "is it permitted"
            ])
            policy_guidance = ""
            if has_policy_subquery:
                profile = self.repo.load_record("workweek/employees.json", employee_id)
                emp_role = "Executive" if profile and profile.get("role") in ["VP of Engineering", "Executive", "VP"] else "Employee"

                policy_blocks = []
                # Check for Home office allowance
                if any(w in lowered_msg for w in ["home office", "500", "allowance", "claim"]):
                    p1 = self.policy_agent.answer_policy_query("5.4 Home Office Equipment Allowance remote work", employee_role=emp_role)
                    if p1.get("success", True) and p1.get("has_policy_match"):
                        cit = f"\n*Source: [{p1['citation_label']}]({p1['citation_url']})*" if p1.get("citation_label") else ""
                        policy_blocks.append(f"**Home Office Equipment Allowance ($500)**:\n{p1['answer']}{cit}")

                # Check for Travel / extending business trip with vacation
                if any(w in lowered_msg for w in ["travel", "conference", "extra day", "business travel", "day off"]):
                    p2 = self.policy_agent.answer_policy_query("4.1 Frugality & Booking Timelines pre-travel checklist and travel", employee_role=emp_role)
                    if p2.get("success", True) and p2.get("has_policy_match"):
                        cit = f"\n*Source: [{p2['citation_label']}]({p2['citation_url']})*" if p2.get("citation_label") else ""
                        policy_blocks.append(f"**Business Travel & Extra Day Off Policy**:\n{p2['answer']}\n*Note: Taking personal vacation days in conjunction with business travel requires prior manager alignment. The extra day must be logged as Vacation in WorkWeek, and personal travel/lodging expenses are non-reimbursable.*{cit}")

                if policy_blocks:
                    policy_guidance = "\n\n---\n### 📖 Relevant Policy Guidance\n\n" + "\n\n".join(policy_blocks)
                else:
                    p_res = self.policy_agent.answer_policy_query(user_message, employee_role=emp_role)
                    if p_res.get("success", True) and p_res.get("answer"):
                        cit_link = f"\n\nSource: [{p_res['citation_label']}]({p_res['citation_url']})" if p_res.get("citation_label") else ""
                        policy_guidance = f"\n\n---\n### 📖 Policy Guidance\n{p_res['answer']}{cit_link}"

            res = self.itsm_agent.create_ticket(user_message, employee_id, policy_guidance=policy_guidance)
            self._record_turn(session, user_message, res["response"], res.get("acting_agent", "itsm_agent"), res.get("tool_invoked", "itsm_create_incident"), start_time)
            self._save_session(session)
            return self._format_result({"success": True, "response": res["response"], "requires_confirmation": False}, acting_agent="itsm_agent")

        # E. General Leave Programs Overview (Ambiguous Leave Query)
        if re.search(r"how\s+many\s+(weeks|days|months)\s+of\s+leave", lowered_msg) or lowered_msg in ["what leave do i get", "what leaves are available", "leave entitlement"]:
            resp_text = """According to company policy, full-time employees are eligible for several leave programs:

• **Paid Time Off (PTO)**: 160 hours (20 business days / 4 weeks) accrued annually ([Section 3.1](https://intranet.company.com/policies/hr-2026-leave.pdf))
• **Parental Leave**: Up to 16 weeks fully paid within the first 12 months ([Section 3.3](https://intranet.company.com/policies/hr-2026-leave.pdf))
• **Short-Term Medical LOA**: Up to 12 weeks with 100% salary continuation upon medical certification ([Section 3.4](https://intranet.company.com/policies/hr-2026-leave.pdf))
• **Bereavement Leave**: Up to 5 consecutive paid business days for immediate family ([Section 3.2](https://intranet.company.com/policies/hr-2026-leave.pdf))"""

            self._record_turn(session, user_message, resp_text, "policy_agent", "leave_overview", start_time)
            self._save_session(session)
            return self._format_result({"success": True, "response": resp_text, "requires_confirmation": False}, acting_agent="policy_agent")

        # F. Policy Q&A Inquiry
        profile = self.repo.load_record("workweek/employees.json", employee_id)
        emp_role = "Executive" if profile and profile.get("role") in ["VP of Engineering", "Executive", "VP"] else "Employee"
        
        p_res = self.policy_agent.answer_policy_query(user_message, employee_role=emp_role)
        resp_text = p_res["answer"]
        if p_res.get("citation_label") and p_res.get("citation_url"):
            resp_text += f"\n\nSource: [{p_res['citation_label']}]({p_res['citation_url']})"

        self._record_turn(session, user_message, resp_text, "policy_agent", "search_policies", start_time)
        self._save_session(session)
        return self._format_result({"success": True, "response": resp_text, "requires_confirmation": False}, acting_agent="policy_agent")

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
