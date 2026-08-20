#!/usr/bin/env python3
"""Unified Google Agent CLI for So-Elevated Enterprise HR Assistant (ADK Standard)."""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Optional

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.agents.orchestrator_agent import PrimaryHROrchestrator
from src.config.settings import settings
from src.repositories.filestore_repository import FileStoreRepository

# ANSI styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner():
    print(f"\n{BOLD}{CYAN}======================================================================")
    print(" 🤖 SO-ELEVATED HR AGENT CLI — VERTEX AI ADK RUNTIME")
    print(f"======================================================================{RESET}\n")


def handle_query(args):
    """Execute a single turn query through the PrimaryHROrchestrator supervisor."""
    orchestrator = PrimaryHROrchestrator()
    session_id = args.session_id or f"cli-session-{int(time.time())}"
    employee_id = args.employee_id or "EMP-436"
    message = args.message

    print(f"{DIM}Routing turn for {employee_id} (Session: {session_id})...{RESET}\n")
    start = time.perf_counter()
    res = orchestrator.process_turn(
        session_id=session_id,
        employee_id=employee_id,
        user_message=message
    )
    elapsed = (time.perf_counter() - start) * 1000.0

    print(f"{BOLD}{GREEN}🤖 Agent Response ({elapsed:.1f}ms):{RESET}\n")
    print(res.get("response", ""))
    print(f"\n{DIM}Status: {'SUCCESS' if res.get('success') else 'BLOCKED'} | Confirmation Required: {res.get('requires_confirmation', False)}{RESET}\n")


def handle_status(args):
    """Inspect local agent subsystems, cloud reasoning engine, and remote FastMCP servers."""
    print_banner()
    print(f"{BOLD}📊 Agent Subsystems & Runtime Topology:{RESET}\n")

    print(f"  • {BOLD}Root Supervisor{RESET}: `PrimaryHROrchestrator` ([src/agents/orchestrator_agent.py])")
    print(f"  • {BOLD}Specialist Sub-Agents{RESET}:")
    print(f"    - `WorkWeekAgent` ([src/agents/workweek_agent.py]) ──► FastMCP WorkWeek")
    print(f"    - `ITSMAgent` ([src/agents/itsm_agent.py]) ──────────► FastMCP ServiceImmediately")
    print(f"    - `PolicyAgent` ([src/agents/policy_agent.py]) ──────► 161 OKF Policy Corpus")
    print(f"  • {BOLD}Security Gates{RESET}: Model Armor (Layer 0) & Persistent DLP Masking")
    print(f"  • {BOLD}Cloud Reasoning Engine{RESET}: `projects/136598345275/locations/us-central1/reasoningEngines/2744444244847493120`")
    print(f"  • {BOLD}Cloud Run Frontend{RESET}: `https://so-elevated-hr-agent-ks3x62na6q-uc.a.run.app`\n")

    print(f"{BOLD}🔗 Remote FastMCP Endpoints:{RESET}")
    print(f"  • WorkWeek HCM: {settings.workweek_mcp_url}")
    print(f"  • ServiceImmediately ITSM: {settings.itsm_mcp_url}\n")


def handle_interactive(args):
    """Launch full interactive terminal REPL."""
    from scripts.interactive_cli import main as run_repl
    run_repl()


def handle_eval(args):
    """Execute benchmark evaluation across golden queries."""
    print_banner()
    dataset_path = args.dataset or "tests/eval/datasets/eval-golden-queries.json"
    if not os.path.exists(dataset_path):
        print(f"{RED}Dataset not found at {dataset_path}{RESET}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    test_cases = data if isinstance(data, list) else data.get("test_cases", [])
    print(f"{BOLD}🧪 Executing Automated Evaluation on {len(test_cases)} Golden Queries...{RESET}\n")

    orch = PrimaryHROrchestrator()
    passed = 0
    start_total = time.perf_counter()

    for idx, tc in enumerate(test_cases, 1):
        q = tc.get("query") or tc.get("input", "")
        emp = tc.get("employee_id", "EMP-436")
        expected_intent = tc.get("expected_intent", "")

        t_start = time.perf_counter()
        res = orch.process_turn(f"eval-sess-{idx}", emp, q)
        t_ms = (time.perf_counter() - t_start) * 1000.0

        is_ok = res.get("success", False)
        status_sym = f"{GREEN}PASS{RESET}" if is_ok else f"{RED}FAIL{RESET}"
        if is_ok:
            passed += 1

        print(f"  [{idx:02d}/{len(test_cases):02d}] [{status_sym}] ({t_ms:5.1f}ms) {q[:55]:<55}")

    total_time = time.perf_counter() - start_total
    pass_rate = (passed / len(test_cases)) * 100.0 if test_cases else 0.0

    print(f"\n{BOLD}======================================================================")
    print(f" 📈 Evaluation Complete: {passed}/{len(test_cases)} Passed ({pass_rate:.1f}%) in {total_time:.2f}s")
    print(f"======================================================================{RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Google Agent CLI for So-Elevated Enterprise HR Assistant (Vertex AI ADK Runtime)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Agent CLI Command")

    # Command: query
    query_parser = subparsers.add_parser("query", help="Run a single conversational turn")
    query_parser.add_argument("message", type=str, help="User message to process")
    query_parser.add_argument("--employee-id", "-e", type=str, default="EMP-436", help="Employee identity (e.g. EMP-436, EMP-1001)")
    query_parser.add_argument("--session-id", "-s", type=str, default=None, help="Session identifier for multi-turn state")

    # Command: status
    subparsers.add_parser("status", help="Show live agent subsystems and cloud connectivity")

    # Command: interactive / chat
    subparsers.add_parser("interactive", help="Start interactive multi-user terminal session")
    subparsers.add_parser("chat", help="Alias for interactive terminal session")

    # Command: eval
    eval_parser = subparsers.add_parser("eval", help="Run automated golden query benchmark evaluation")
    eval_parser.add_argument("--dataset", "-d", type=str, default="tests/eval/datasets/eval-golden-queries.json", help="Path to golden dataset")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "query":
        handle_query(args)
    elif args.command == "status":
        handle_status(args)
    elif args.command in ["interactive", "chat"]:
        handle_interactive(args)
    elif args.command == "eval":
        handle_eval(args)


if __name__ == "__main__":
    main()
