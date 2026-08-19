"""Remote Model Context Protocol (MCP) Streamable HTTP Client.

Connects to live FastMCP enterprise servers via Streamable HTTP (JSON-RPC 2.0)
using X-MCP-Token authentication headers.
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional


class RemoteMCPClient:
    """Client for Streamable HTTP FastMCP server endpoints."""

    def __init__(self, endpoint_url: str, token: str, client_name: str = "so-elevated-adk"):
        self.endpoint_url = endpoint_url.rstrip("/") + "/"
        self.token = token
        self.client_name = client_name
        self._initialized = False

    def _send_rpc(self, method: str, params: Dict[str, Any], req_id: int = 1) -> Dict[str, Any]:
        """Send JSON-RPC 2.0 payload to FastMCP endpoint."""
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint_url,
            data=data,
            headers={
                "X-MCP-Token": self.token,
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                resp_text = resp.read().decode("utf-8")
                return json.loads(resp_text)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": e.code, "message": f"HTTP {e.code} {e.reason}: {error_body}"}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)}
            }

    def initialize(self) -> Dict[str, Any]:
        """Initialize MCP protocol session."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": self.client_name, "version": "1.0.0"}
        }
        res = self._send_rpc("initialize", params, req_id=1)
        if "result" in res:
            self._initialized = True
        return res

    def list_tools(self) -> List[Dict[str, Any]]:
        """Discover available MCP tools."""
        res = self._send_rpc("tools/list", {}, req_id=2)
        if "result" in res and "tools" in res["result"]:
            return res["result"]["tools"]
        return []

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific MCP tool call."""
        params = {
            "name": tool_name,
            "arguments": arguments
        }
        res = self._send_rpc("tools/call", params, req_id=3)
        if "error" in res:
            return {"success": False, "error": res["error"].get("message", "Unknown error")}
        
        result = res.get("result", {})
        structured = result.get("structuredContent", {})
        content = result.get("content", [])
        text_out = content[0].get("text", "") if content and isinstance(content, list) else ""
        
        return {
            "success": not result.get("isError", False),
            "result": text_out,
            "structured": structured,
            "raw": result
        }


class RemoteWorkWeekClient(RemoteMCPClient):
    """Specialized client for live WorkWeek HCM FastMCP Server."""

    def get_current_employee_id(self) -> str:
        """Fetch the employee ID associated with this session token."""
        res = self.call_tool("get_current_employee_id", {})
        return res.get("result", "").strip()

    def get_employee_balances(self, employee_id: str) -> Dict[str, Any]:
        """Fetch current vacation and sick leave balances."""
        return self.call_tool("get_employee_balances", {"employee_id": employee_id})

    def get_personal_info(self, employee_id: str) -> Dict[str, Any]:
        """Fetch current personal contact details."""
        return self.call_tool("get_personal_info", {"employee_id": employee_id})

    def update_personal_info(self, employee_id: str, address: str, phone: str) -> Dict[str, Any]:
        """Update personal contact details."""
        return self.call_tool("update_personal_info", {
            "employee_id": employee_id,
            "address": address,
            "phone": phone
        })

    def request_time_off(self, employee_id: str, start_date: str, end_date: str, leave_type: str, days: float) -> Dict[str, Any]:
        """Submit request for time off."""
        return self.call_tool("request_time_off", {
            "employee_id": employee_id,
            "start_date": start_date,
            "end_date": end_date,
            "leave_type": leave_type,
            "days": days
        })

    def get_leave_requests(self, employee_id: str) -> Dict[str, Any]:
        """Get history of all requested time off."""
        return self.call_tool("get_leave_requests", {"employee_id": employee_id})

    def cancel_leave_request(self, employee_id: str, request_id: int) -> Dict[str, Any]:
        """Cancel a pending/approved leave request and refund days."""
        return self.call_tool("cancel_leave_request", {"employee_id": employee_id, "request_id": request_id})


class RemoteServiceImmediatelyClient(RemoteMCPClient):
    """Specialized client for live ServiceImmediately ITSM FastMCP Server."""

    def list_tickets(self, employee_id: str) -> Dict[str, Any]:
        """List all incident tickets requested by a specific employee."""
        return self.call_tool("list_tickets", {"employee_id": employee_id})

    def create_ticket(
        self,
        requested_by: str,
        category: str,
        short_description: str,
        priority: str = "3 - Moderate",
        assignment_group: str = "Service Desk"
    ) -> Dict[str, Any]:
        """Create a new ServiceImmediately incident ticket."""
        return self.call_tool("create_ticket", {
            "requested_by": requested_by,
            "category": category,
            "short_description": short_description,
            "priority": priority,
            "assignment_group": assignment_group
        })

    def add_ticket_comment(self, ticket_id: str, author: str, comment: str) -> Dict[str, Any]:
        """Append a comment/note to the activity log of a ticket."""
        return self.call_tool("add_ticket_comment", {
            "ticket_id": ticket_id,
            "author": author,
            "comment": comment
        })

    def update_ticket_status(self, ticket_id: str, status: str, resolution_notes: str = "", updated_by: str = "System") -> Dict[str, Any]:
        """Update the lifecycle state of a ticket."""
        return self.call_tool("update_ticket_status", {
            "ticket_id": ticket_id,
            "status": status,
            "resolution_notes": resolution_notes,
            "updated_by": updated_by
        })
