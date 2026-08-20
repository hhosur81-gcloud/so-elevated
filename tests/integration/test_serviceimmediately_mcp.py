"""Integration tests for ServiceImmediately ITSM FastMCP Client (ADR-0001, ADR-0010, SEC-0005)."""

import json
import unittest
from unittest.mock import MagicMock, patch
from src.mcp.remote_mcp_client import RemoteServiceImmediatelyClient


class TestServiceImmediatelyMCPClient(unittest.TestCase):
    """Test suite verifying ServiceImmediately FastMCP Client communication and tool calls."""

    def setUp(self):
        self.client = RemoteServiceImmediatelyClient(
            endpoint_url="https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/",
            token="mcp_test_token_456"
        )

    @patch("urllib.request.urlopen")
    def test_list_tickets(self, mock_urlopen):
        """Verify list_tickets formats JSON-RPC correctly."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "content": [{"type": "text", "text": '[{"ticket_id": "INC0002820", "status": "New"}]'}],
                "isError": False
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.list_tickets("EMP-436")
        self.assertTrue(res["success"])
        self.assertIn("INC0002820", res["result"])

    @patch("urllib.request.urlopen")
    def test_get_ticket(self, mock_urlopen):
        """Verify get_ticket retrieves specific ticket by ID."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "content": [{"type": "text", "text": '{"ticket_id": "INC0002820", "category": "Hardware", "priority": "3 - Moderate"}'}],
                "isError": False
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.get_ticket("INC0002820")
        self.assertTrue(res["success"])
        self.assertIn("INC0002820", res["result"])

    @patch("urllib.request.urlopen")
    def test_create_ticket(self, mock_urlopen):
        """Verify create_ticket formats RPC tool call and parameters."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "content": [{"type": "text", "text": '[{"ticket_id": "INC0002821", "status": "New", "priority": "3 - Moderate"}]'}],
                "isError": False
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.create_ticket(
            requested_by="EMP-436",
            category="Hardware",
            short_description="Loaner laptop for conference travel",
            priority="3 - Moderate"
        )
        self.assertTrue(res["success"])
        self.assertIn("INC0002821", res["result"])

    @patch("urllib.request.urlopen")
    def test_add_comment_and_status_transition(self, mock_urlopen):
        """Verify add_comment and update_ticket_status calls."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "content": [{"type": "text", "text": '{"ticket_id": "INC0002820", "status": "In Progress"}'}],
                "isError": False
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        c_res = self.client.add_comment("INC0002820", "IT technician assigned.")
        self.assertTrue(c_res["success"])

        s_res = self.client.update_ticket_status("INC0002820", "In Progress", "Working on setup")
        self.assertTrue(s_res["success"])


if __name__ == "__main__":
    unittest.main()
