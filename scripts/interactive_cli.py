"""Interactive Terminal Chat with the So-Elevated HR Agentic Solution."""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.agents.orchestrator_agent import PrimaryHROrchestrator
from src.config.security import JWTManager
from src.repositories.filestore_repository import FileStoreRepository

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def main():
    print(f"\n{BOLD}{CYAN}======================================================================")
    print(" 🤖 SO-ELEVATED HR AGENTIC ASSISTANT — INTERACTIVE TERMINAL REPL")
    print("======================================================================{RESET}")
    print(f"Logged in as: {BOLD}Jane Doe (EMP-1001){RESET} | Department: {BOLD}Engineering{RESET}")
    print("Type your message below (or type 'exit' / 'quit' to exit, 'reset' to clear session):\n")

    repo = FileStoreRepository(base_path="data/filestore")
    jwt_manager = JWTManager()
    orchestrator = PrimaryHROrchestrator(jwt_manager=jwt_manager, repository=repo)

    session_id = "cli-session-interactive"
    emp_id = "EMP-1001"

    while True:
        try:
            user_input = input(f"{BOLD}You > {RESET}").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print(f"\n{YELLOW}Goodbye! Exiting interactive session.{RESET}\n")
                break

            response = orchestrator.process_turn(session_id, emp_id, user_input)

            if not response.get("success", False):
                if response.get("error_code") == "SECURITY_BLOCKED":
                    print(f"\n{RED}🛡️ [Security Intercepted]: {response['response']}{RESET}\n")
                else:
                    print(f"\n{RED}❌ Error: {response.get('error', 'Unknown error')}{RESET}\n")
            elif response.get("requires_confirmation"):
                print(f"\n{YELLOW}🤖 HR Agent (Action Pending Approval):{RESET}\n{response['response']}\n")
            else:
                print(f"\n{GREEN}🤖 HR Agent:{RESET}\n{response['response']}\n")

        except (KeyboardInterrupt, EOFError):
            print(f"\n{YELLOW}Session ended.{RESET}\n")
            break

if __name__ == "__main__":
    main()
