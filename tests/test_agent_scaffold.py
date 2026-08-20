"""Unit tests verifying the ADK root agent configuration and tool registrations."""
import pytest
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from agent import agent, config
from agent.agent import root_agent, list_concepts, read_concept, workweek_mcp, serviceimmediately_mcp


def test_agent_initialization():
    """Verify that root agent is correctly initialized with expected model and instruction."""
    assert isinstance(root_agent, LlmAgent)
    assert root_agent.name == "hr_agentic_orchestrator"
    assert root_agent.model == config.GEMINI_MODEL
    assert "Altostrat" in root_agent.description


def test_agent_tool_registration():
    """Verify that OKF and FastMCP tools are registered with the agent."""
    tools = root_agent.tools
    assert list_concepts in tools
    assert read_concept in tools
    assert workweek_mcp in tools
    assert serviceimmediately_mcp in tools


def test_mcp_connection_parameters():
    """Verify that FastMCP parameters match the live service endpoints and security tokens."""
    # Check WorkWeek MCP params
    ww_params = workweek_mcp.connection_params
    assert isinstance(ww_params, StreamableHTTPConnectionParams)
    assert ww_params.url == config.WORKWEEK_MCP_URL
    assert ww_params.headers.get("X-MCP-Token") == config.WORKWEEK_MCP_TOKEN

    # Check ServiceImmediately MCP params
    si_params = serviceimmediately_mcp.connection_params
    assert isinstance(si_params, StreamableHTTPConnectionParams)
    assert si_params.url == config.SERVICEIMMEDIATELY_MCP_URL
    assert si_params.headers.get("X-MCP-Token") == config.SERVICEIMMEDIATELY_MCP_TOKEN
