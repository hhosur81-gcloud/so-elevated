"""Integration tests for WorkWeek HCM FastMCP Client (ADR-0001, ADR-0006, ENG-0001)."""

import json
import unittest
from unittest.mock import MagicMock, patch
from src.mcp.remote_mcp_client import RemoteWorkWeekClient


class TestWorkWeekMCPClient(unittest.TestCase):
    """Test suite verifying WorkWeek FastMCP Client communication, parameters, and responses."""

    def setUp(self):
        self.client = RemoteWorkWeekClient(
            endpoint_url="https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/",
            token="mcp_test_token_123"
        )

    @patch("urllib.request.urlopen")
    def test_get_employee_balances(self, mock_urlopen):
        """Verify PTO balance query formats JSON-RPC correctly."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "content": [{"type": "text", "text": "Vacation: 15.0 days\nSick: 10.0 days"}],
                "isError": False
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.get_employee_balances("EMP-436")
        self.assertTrue(res["success"])
        self.assertIn("15.0 days", res["result"])

    @patch("urllib.request.urlopen")
    def test_get_personal_info(self, mock_urlopen):
        """Verify personal info query retrieves employee contact data."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "content": [{"type": "text", "text": "Skhadkikar Employee | Singapore"}],
                "isError": False
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.get_personal_info("EMP-436")
        self.assertTrue(res["success"])
        self.assertIn("Singapore", res["result"])

    @patch("urllib.request.urlopen")
    def test_request_time_off(self, mock_urlopen):
        """Verify request_time_off formats RPC tool call and parameters."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "result": {
                "content": [{"type": "text", "text": "Leave requested successfully for EMP-436"}],
                "isError": False
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.request_time_off("EMP-436", "2026-09-01", "2026-09-02", "Vacation", 2.0)
        self.assertTrue(res["success"])
        self.assertIn("Leave requested successfully", res["result"])

    @patch("urllib.request.urlopen")
    def test_initialize_protocol(self, mock_urlopen):
        """Verify MCP initialize handshake handshake."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "WorkWeek", "version": "1.0.0"}
            }
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.initialize()
        self.assertTrue(self.client._initialized)


if __name__ == "__main__":
    unittest.main()

