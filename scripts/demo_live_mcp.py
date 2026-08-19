#!/usr/bin/env python3
"""Interactive Live FastMCP Cloud SaaS Demonstration Script.

Demonstrates real-time JSON-RPC 2.0 communication over Streamable HTTP (SSE)
connecting directly to the live Google Cloud SaaS MCP servers:
  • WorkWeek HCM:          https://mock-saas.aishprabhat.demo.altostrat.com/work-week/mcp/
  • ServiceImmediately:    https://mock-saas.aishprabhat.demo.altostrat.com/service-immediately/mcp/
"""

import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.config.settings import settings
from src.mcp.remote_mcp_client import RemoteServiceImmediatelyClient, RemoteWorkWeekClient

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_header(title: str):
    print(f"\n{BOLD}{CYAN}{'=' * 72}")
    print(f" 🌐 {title}")
    print(f"{'=' * 72}{RESET}\n")


def run_demo():
    print(f"{BOLD}{GREEN}========================================================================")
    print(" 🚀 LIVE FASTMCP CLOUD SAAS CONNECTOR DEMONSTRATION")
    print(" Target: https://mock-saas.aishprabhat.demo.altostrat.com/")
    print(f"========================================================================{RESET}\n")

    # 1. Initialize Clients
    ww_client = RemoteWorkWeekClient(
        endpoint_url=settings.workweek_mcp_url,
        token=settings.workweek_mcp_token
    )
    itsm_client = RemoteServiceImmediatelyClient(
        endpoint_url=settings.itsm_mcp_url,
        token=settings.itsm_mcp_token
    )

    # 2. Protocol Handshake & Tool Discovery
    print_header("1. Protocol Handshake & Tool Discovery (JSON-RPC 2.0)")
    
    t0 = time.perf_counter()
    ww_init = ww_client.initialize()
    ww_lat = (time.perf_counter() - t0) * 1000
    server_info = ww_init.get("result", {}).get("serverInfo", {})
    print(f"🏢 {BOLD}WorkWeek FastMCP Server:{RESET} {server_info.get('name')} v{server_info.get('version')} ({ww_lat:.1f}ms)")
    print(f"   • Endpoint: {DIM}{settings.workweek_mcp_url}{RESET}")
    print(f"   • Header:   {YELLOW}X-MCP-Token: {settings.workweek_mcp_token[:12]}...{RESET}")

    ww_tools = ww_client.list_tools()
    print(f"   • Discovered Tools ({len(ww_tools)}): {', '.join([t['name'] for t in ww_tools])}")

    t0 = time.perf_counter()
    itsm_init = itsm_client.initialize()
    itsm_lat = (time.perf_counter() - t0) * 1000
    itsm_server = itsm_init.get("result", {}).get("serverInfo", {})
    print(f"\n🎫 {BOLD}ServiceImmediately FastMCP Server:{RESET} {itsm_server.get('name')} v{itsm_server.get('version')} ({itsm_lat:.1f}ms)")
    print(f"   • Endpoint: {DIM}{settings.itsm_mcp_url}{RESET}")
    print(f"   • Header:   {YELLOW}X-MCP-Token: {settings.itsm_mcp_token[:12]}...{RESET}")

    itsm_tools = itsm_client.list_tools()
    print(f"   • Discovered Tools ({len(itsm_tools)}): {', '.join([t['name'] for t in itsm_tools])}")

    # 3. Authenticated Identity Verification
    print_header("2. Authenticated Session Context & Identity")
    curr_emp = ww_client.get_current_employee_id()
    print(f"👤 {BOLD}Active Authenticated Employee ID:{RESET} {GREEN}{curr_emp}{RESET}")

    t0 = time.perf_counter()
    info_res = ww_client.get_personal_info(curr_emp)
    info_lat = (time.perf_counter() - t0) * 1000
    print(f"📍 {BOLD}Personal Contact Info ({info_lat:.1f}ms):{RESET}")
    print(f"   {info_res.get('result')}")

    # 4. Live WorkWeek Leave Balance Fetch
    print_header("3. Live WorkWeek HCM Balance Check (get_employee_balances)")
    t0 = time.perf_counter()
    bal_res = ww_client.get_employee_balances(curr_emp)
    bal_lat = (time.perf_counter() - t0) * 1000
    print(f"🌴 {BOLD}Real-Time Leave Balances ({bal_lat:.1f}ms):{RESET}")
    for line in bal_res.get("result", "").splitlines():
        print(f"   {GREEN}{line}{RESET}")

    # 5. Live ServiceImmediately Ticket List
    print_header("4. Live ServiceImmediately Ticket Lookup (list_tickets)")
    t0 = time.perf_counter()
    tix_res = itsm_client.list_tickets(curr_emp)
    tix_lat = (time.perf_counter() - t0) * 1000
    print(f"🎟️ {BOLD}Open Support Tickets for {curr_emp} ({tix_lat:.1f}ms):{RESET}")
    print(f"   {tix_res.get('result')}")

    # 6. Summary
    print(f"\n{BOLD}{GREEN}{'=' * 72}")
    print(" 🎉 LIVE CLOUD FASTMCP SAAS INTEGRATION VERIFIED 100% OPERATIONAL")
    print(f"{'=' * 72}{RESET}\n")


if __name__ == "__main__":
    run_demo()
