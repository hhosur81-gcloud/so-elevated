"""WorkWeek HCM Model Context Protocol (MCP) Server (ADR-0001, ADR-0006, ENG-0001, ENG-0002)."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.config.security import JWTManager
from src.repositories.filestore_repository import FileStoreRepository


class WorkWeekMCPServer:
    """Model Context Protocol (MCP) Enterprise Server for WorkWeek HCM."""

    FILE_PATH = "workweek/employees.json"
    IDEMPOTENCY_FILE = "workweek/idempotency_cache.json"

    def __init__(self, jwt_manager: Optional[JWTManager] = None, repository: Optional[FileStoreRepository] = None):
        self.jwt_manager = jwt_manager or JWTManager()
        self.repo = repository or FileStoreRepository()

    def _verify_auth(self, employee_id: str, bearer_token: str, required_scope: str) -> Optional[Dict[str, Any]]:
        """Verify token signature, expiry, identity claim, and scope."""
        try:
            claims = self.jwt_manager.verify_token(bearer_token)
        except Exception as e:
            return {"success": False, "error_code": "UNAUTHORIZED", "error": f"Invalid token: {str(e)}"}

        if claims.get("sub") != employee_id and claims.get("sub") != "system-admin":
            return {"success": False, "error_code": "FORBIDDEN", "error": "Token identity mismatch"}

        if not self.jwt_manager.has_scope(claims, required_scope):
            return {"success": False, "error_code": "FORBIDDEN", "error": f"Missing required scope: {required_scope}"}

        return None

    def workweek_get_profile(self, employee_id: str, bearer_token: str) -> Dict[str, Any]:
        """MCP Tool: Fetch employee profile and metadata."""
        auth_err = self._verify_auth(employee_id, bearer_token, "hcm:read")
        if auth_err:
            return auth_err

        profile = self.repo.load_record(self.FILE_PATH, employee_id)
        if not profile:
            return {"success": False, "error_code": "NOT_FOUND", "error": f"Employee {employee_id} not found"}

        return {"success": True, "data": profile}

    def workweek_get_pto_balances(self, employee_id: str, bearer_token: str) -> Dict[str, Any]:
        """MCP Tool: Fetch PTO, sick leave, and floating holiday balances."""
        auth_err = self._verify_auth(employee_id, bearer_token, "hcm:read")
        if auth_err:
            return auth_err

        profile = self.repo.load_record(self.FILE_PATH, employee_id)
        if not profile:
            return {"success": False, "error_code": "NOT_FOUND", "error": f"Employee {employee_id} not found"}

        return {
            "success": True,
            "data": {
                "employee_id": employee_id,
                "pto_balance_hours": profile.get("pto_balance_hours", 0.0),
                "sick_leave_hours": profile.get("sick_leave_hours", 0.0),
                "floating_holiday_hours": profile.get("floating_holiday_hours", 16.0)
            }
        }

    def workweek_submit_leave_request(
        self,
        employee_id: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        hours: float,
        bearer_token: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """MCP Tool: Submit a leave request with balance deduction and idempotency deduplication."""
        auth_err = self._verify_auth(employee_id, bearer_token, "hcm:write")
        if auth_err:
            return auth_err

        # Check Idempotency Cache
        if idempotency_key:
            cached_resp = self.repo.load_record(self.IDEMPOTENCY_FILE, idempotency_key)
            if cached_resp:
                return cached_resp

        profile = self.repo.load_record(self.FILE_PATH, employee_id)
        if not profile:
            return {"success": False, "error_code": "NOT_FOUND", "error": f"Employee {employee_id} not found"}

        if leave_type == "PTO":
            current_balance = profile.get("pto_balance_hours", 0.0)
            if hours > current_balance:
                return {
                    "success": False,
                    "error_code": "INSUFFICIENT_BALANCE",
                    "error": f"Requested {hours}h exceeds available PTO balance of {current_balance}h"
                }
        elif leave_type == "SICK":
            current_balance = profile.get("sick_leave_hours", 0.0)
            if hours > current_balance:
                return {
                    "success": False,
                    "error_code": "INSUFFICIENT_BALANCE",
                    "error": f"Requested {hours}h exceeds available SICK balance of {current_balance}h"
                }
        elif leave_type == "MEDICAL":
            # Policy Section 3.4: Up to 12 weeks (480 hours) Short-Term Medical LOA
            if hours > 480.0:
                return {
                    "success": False,
                    "error_code": "INSUFFICIENT_BALANCE",
                    "error": f"Requested {hours}h exceeds maximum medical LOA cap of 480 hours"
                }

        request_id = f"LOA-{uuid.uuid4().hex[:6].upper()}"
        leave_entry = {
            "request_id": request_id,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "hours_requested": hours,
            "status": "CONFIRMED",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "idempotency_key": idempotency_key
        }

        def mutate_profile(data: Dict[str, Any]) -> Dict[str, Any]:
            if leave_type == "PTO":
                data["pto_balance_hours"] -= hours
            elif leave_type == "SICK":
                data["sick_leave_hours"] -= hours
            data.setdefault("leave_requests", []).append(leave_entry)
            return data

        updated = self.repo.update_record(self.FILE_PATH, employee_id, mutate_profile)

        response = {
            "success": True,
            "data": {
                "request_id": request_id,
                "employee_id": employee_id,
                "leave_type": leave_type,
                "hours_deducted": hours,
                "remaining_pto_hours": updated.get("pto_balance_hours"),
                "remaining_sick_hours": updated.get("sick_leave_hours"),
                "status": "CONFIRMED"
            }
        }

        # Cache Idempotent response
        if idempotency_key:
            self.repo.save_record(self.IDEMPOTENCY_FILE, idempotency_key, response)

        return response
