"""Altostrat HR & IT Agentic Solution — ADK Agent Entry Point (ENG-0003, ENG-0004)."""
import asyncio
import os
import sys
from typing import List, Optional

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.genai import types

try:
    from . import config
    from .prompt import POLICY_ORCHESTRATOR_PROMPT
    from .services.policy_service import PolicyService
    from .services.idempotency_store import IdempotencyStore
except (ImportError, ValueError):
    import config
    from prompt import POLICY_ORCHESTRATOR_PROMPT
    from services.policy_service import PolicyService
    from services.idempotency_store import IdempotencyStore

# ---------------------------------------------------------------------------
# 1. Services & Tools Setup
# ---------------------------------------------------------------------------
policy_service = PolicyService()
idempotency_store = IdempotencyStore(config.IDEMPOTENCY_DB_PATH)


def list_concepts(filter_keyword: str = "") -> str:
    """Lists all available HR policy categories, sections, and concept files in the knowledge base."""
    return policy_service.list_concepts(filter_keyword)


def read_concept(concept_path: str) -> str:
    """Reads the full policy text and metadata of a specific OKF concept file."""
    return policy_service.read_concept(concept_path)


# ---------------------------------------------------------------------------
# 2. Live FastMCP Toolsets
# ---------------------------------------------------------------------------
workweek_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=config.WORKWEEK_MCP_URL,
        headers={"X-MCP-Token": config.WORKWEEK_MCP_TOKEN},
    )
)

serviceimmediately_mcp = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=config.SERVICEIMMEDIATELY_MCP_URL,
        headers={"X-MCP-Token": config.SERVICEIMMEDIATELY_MCP_TOKEN},
    )
)

# ---------------------------------------------------------------------------
# 3. Root ADK Agent Construction
# ---------------------------------------------------------------------------
root_agent = LlmAgent(
    name="hr_agentic_orchestrator",
    model=config.GEMINI_MODEL,
    description=(
        "Altostrat Tier-1 Enterprise HR & IT Service Assistant grounded in "
        "Open Knowledge Format (OKF) policies and live FastMCP integrations."
    ),
    instruction=POLICY_ORCHESTRATOR_PROMPT,
    tools=[
        list_concepts,
        read_concept,
        workweek_mcp,
        serviceimmediately_mcp,
    ],
)


def get_session_service():
    """Lazily load the appropriate session service (DatabaseSessionService or InMemory)."""
    try:
        from google.adk.sessions import DatabaseSessionService
        return DatabaseSessionService(db_url=config.SQLITE_SESSION_DB_URI)
    except Exception:
        from google.adk.sessions import InMemorySessionService
        return InMemorySessionService()


# ---------------------------------------------------------------------------
# 4. Interactive CLI & Direct Runner
# ---------------------------------------------------------------------------
async def run_query(
    user_query: str,
    user_id: str = "EMP1001",
    session_id: str = "default_session",
    runner: Optional[Runner] = None,
):
    """Execute a single query through the ADK Runner."""
    session_service = get_session_service()
    if runner is None:
        runner = Runner(agent=root_agent, session_service=session_service, app_name="agent")

    # Ensure session exists
    try:
        sess = await session_service.get_session(app_name="agent", user_id=user_id, session_id=session_id)
        if not sess:
            await session_service.create_session(app_name="agent", user_id=user_id, session_id=session_id)
    except Exception:
        pass

    print(f"\n💬 User ({user_id}): {user_query}\n")
    print("🤖 Agent: ", end="", flush=True)

    new_msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_query)],
    )

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_msg,
        ):
            if hasattr(event, "content") and event.content:
                for part in getattr(event.content, "parts", []):
                    if hasattr(part, "text") and part.text:
                        print(part.text, end="", flush=True)
            elif hasattr(event, "text") and event.text:
                print(event.text, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\n[Execution error: {e}]")


async def interactive_loop(user_id: str = "EMP1001", session_id: str = "interactive_session"):
    """Start an interactive chat session with persistent state."""
    session_service = get_session_service()
    print("=" * 75)
    print(" Altostrat HR & IT Agentic Assistant (Google ADK)")
    print(f" User: {user_id} | Session: {session_id}")
    print(" Type 'exit' or 'quit' to end session.")
    print("=" * 75)

    runner = Runner(agent=root_agent, session_service=session_service, app_name="agent")

    while True:
        try:
            query = input("\nYou > ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                print("Session paused.")
                break
            await run_query(query, user_id=user_id, session_id=session_id, runner=runner)
        except (KeyboardInterrupt, EOFError):
            print("\nSession paused.")
            break


def main():
    """CLI entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] in ("-i", "--interactive", "interactive"):
            asyncio.run(interactive_loop())
        else:
            query = " ".join(sys.argv[1:])
            asyncio.run(run_query(query))
    else:
        asyncio.run(interactive_loop())


if __name__ == "__main__":
    main()
