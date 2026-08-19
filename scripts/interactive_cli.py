"""Interactive Terminal Chat with Multi-User Authentication & Persona Switcher."""

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
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

MOCK_USERS = {
    "1": {
        "employee_id": "EMP-1001",
        "name": "Jane Doe",
        "email": "jane.doe@enterprise.com",
        "department": "Engineering",
        "role": "Employee",
        "title": "Senior Cloud Engineer"
    },
    "2": {
        "employee_id": "EMP-1002",
        "name": "John Smith",
        "email": "john.smith@enterprise.com",
        "department": "Sales",
        "role": "Employee",
        "title": "Account Executive"
    },
    "3": {
        "employee_id": "EMP-1004",
        "name": "Maria Chen",
        "email": "maria.chen@enterprise.com",
        "department": "Legal & Compliance",
        "role": "Employee",
        "title": "Data Protection Officer"
    },
    "4": {
        "employee_id": "EMP-1005",
        "name": "Marcus Vance",
        "email": "marcus.vance@enterprise.com",
        "department": "Engineering",
        "role": "Executive",
        "title": "VP of Engineering (Executive Clearance)"
    },
    "5": {
        "employee_id": "EMP-436",
        "name": "Skhadkikar Employee",
        "email": "skhadkikar@google.com",
        "department": "Global Solutions",
        "role": "Employee",
        "title": "Staff Solutions Engineer (Live Cloud SaaS Session)"
    }
}

def print_banner():
    print(f"\n{BOLD}{CYAN}======================================================================")
    print(" 🤖 SO-ELEVATED HR AGENTIC ASSISTANT — INTERACTIVE TERMINAL REPL")
    print(f"======================================================================{RESET}\n")

def select_persona():
    print(f"{BOLD}🔐 Select an Authenticated Enterprise Identity to Login:{RESET}")
    for k, u in MOCK_USERS.items():
        role_tag = f" {MAGENTA}[{u['role']}]{RESET}" if u['role'] == "Executive" else ""
        if u['employee_id'] == "EMP-436":
            role_tag += f" {GREEN}[LIVE SAAS]{RESET}"
        print(f"  [{BOLD}{k}{RESET}] {u['name']:<18} ({u['employee_id']}) — {u['title']}{role_tag}")
    print(f"  [{BOLD}6{RESET}] Custom Username & Password Login")
    print(f"  [{BOLD}q{RESET}] Exit\n")

    while True:
        choice = input(f"{BOLD}Select Identity (1-6 or q) > {RESET}").strip()
        if choice.lower() in ["q", "exit", "quit"]:
            return None
        if choice in MOCK_USERS:
            return MOCK_USERS[choice]
        if choice == "6":

            print(f"\n{DIM}Simulating Enterprise SSO (Okta / Google Workspace)...{RESET}")
            uname = input(f"{BOLD}Username / Corporate Email: {RESET}").strip()
            pwd = input(f"{BOLD}Password: {RESET}").strip()
            if not uname:
                print(f"{RED}Invalid username.{RESET}\n")
                continue
            
            # Simple credentials match or fallback
            for u in MOCK_USERS.values():
                if uname.lower() in [u["email"].lower(), u["name"].lower(), u["employee_id"].lower()]:
                    print(f"{GREEN}✅ Authenticated via SSO as {u['name']} ({u['employee_id']}){RESET}\n")
                    return u
            
            # Ad-hoc custom user
            custom_emp = {
                "employee_id": f"EMP-{abs(hash(uname)) % 9000 + 1000}",
                "name": uname.split("@")[0].replace(".", " ").title(),
                "email": uname if "@" in uname else f"{uname}@enterprise.com",
                "department": "Operations",
                "role": "Employee",
                "title": "Staff Member"
            }
            print(f"{GREEN}✅ Authenticated via SSO as {custom_emp['name']} ({custom_emp['employee_id']}){RESET}\n")
            return custom_emp
        print(f"{RED}Invalid choice. Please select 1-5 or q.{RESET}")

def main():
    print_banner()
    repo = FileStoreRepository(base_path="data/filestore")
    jwt_manager = JWTManager()
    orchestrator = PrimaryHROrchestrator(jwt_manager=jwt_manager, repository=repo)

    current_user = select_persona()
    if not current_user:
        print(f"\n{YELLOW}Exited without logging in.{RESET}\n")
        return

    session_id = f"cli-sess-{current_user['employee_id']}"

    print(f"\n{GREEN}======================================================================{RESET}")
    print(f" Logged in as: {BOLD}{current_user['name']}{RESET} ({current_user['employee_id']})")
    print(f" Email:        {DIM}{current_user['email']}{RESET}")
    print(f" Department:   {current_user['department']} | Role: {BOLD}{current_user['role']}{RESET}")
    print(f" Special cmds: {CYAN}/whoami{RESET} (view claims), {CYAN}/switch{RESET} (switch user), {CYAN}/exit{RESET}")
    print(f"{GREEN}======================================================================{RESET}\n")

    while True:
        try:
            user_input = input(f"{BOLD}[{current_user['name']}] > {RESET}").strip()
            if not user_input:
                continue

            # Command: Exit
            if user_input.lower() in ["/exit", "/quit", "/q", "exit", "quit"]:
                print(f"\n{YELLOW}Logging out. Goodbye!{RESET}\n")
                break

            # Command: Switch User
            if user_input.lower() in ["/switch", "switch", "/login"]:
                print()
                new_user = select_persona()
                if new_user:
                    current_user = new_user
                    session_id = f"cli-sess-{current_user['employee_id']}"
                    print(f"\n{GREEN}Switched identity to: {BOLD}{current_user['name']}{RESET} ({current_user['employee_id']}) [{current_user['department']}]\n")
                continue

            # Command: WhoAmI (Inspect Token & Claims)
            if user_input.lower() in ["/whoami", "whoami"]:
                token = jwt_manager.generate_delegated_token(current_user["employee_id"], scopes=["hcm:read", "hcm:write", "itsm:read", "itsm:write"])
                claims = jwt_manager.verify_token(token)
                print(f"\n{CYAN}--- Active Delegated Token Claims (ADR-0006, SEC-0001) ---{RESET}")
                print(f" Subject (sub):    {BOLD}{claims['sub']}{RESET}")
                print(f" Issuer (iss):     {claims['iss']}")
                print(f" Audience (aud):   {claims['aud']}")
                print(f" Scopes:           {claims['scopes']}")
                print(f" Role Clearance:   {current_user['role']}")
                print(f" Token Expiry:     {claims['exp']} (15-min TTL)\n")
                continue

            # Process Conversational Turn
            response = orchestrator.process_turn(session_id, current_user["employee_id"], user_input)

            if not response.get("success", False):
                if response.get("error_code") == "SECURITY_BLOCKED":
                    print(f"\n{RED}🛡️ [Model Armor Interception]: {response['response']}{RESET}\n")
                else:
                    print(f"\n{RED}❌ Error: {response.get('error', 'Unknown error')}{RESET}\n")
            elif response.get("requires_confirmation"):
                print(f"\n{YELLOW}🤖 HR Agent (Action Pending Confirmation):{RESET}\n{response['response']}\n")
            else:
                print(f"\n{GREEN}🤖 HR Agent:{RESET}\n{response['response']}\n")

        except (KeyboardInterrupt, EOFError):
            print(f"\n{YELLOW}Session ended.{RESET}\n")
            break

if __name__ == "__main__":
    main()
