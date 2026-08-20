"""Unit tests verifying SQLite Session Persistence across service restarts (ENG-0004)."""
import pytest
from pathlib import Path
from google.adk.sessions import DatabaseSessionService
from agent import config


@pytest.mark.asyncio
async def test_sqlite_session_lifecycle(tmp_path: Path):
    """Verify session creation, persistence, and reloading from SQLite database file."""
    db_file = tmp_path / "test_sessions.db"
    db_uri = f"sqlite+aiosqlite:///{db_file}"

    # 1. Initialize Service 1 and create session
    service1 = DatabaseSessionService(db_url=db_uri)
    sess1 = await service1.create_session(
        app_name="so_elevated",
        user_id="EMP1001",
        session_id="session_laptop_test",
        state={"employee_id": "EMP1001", "role": "Cloud Architect"},
    )
    assert sess1.id == "session_laptop_test"
    assert sess1.user_id == "EMP1001"
    assert sess1.state["role"] == "Cloud Architect"

    # Simulate process termination / closing laptop (new service instance)
    service2 = DatabaseSessionService(db_url=db_uri)
    reloaded_sess = await service2.get_session(
        app_name="so_elevated",
        user_id="EMP1001",
        session_id="session_laptop_test",
    )

    assert reloaded_sess is not None
    assert reloaded_sess.id == "session_laptop_test"
    assert reloaded_sess.user_id == "EMP1001"
    assert reloaded_sess.state["role"] == "Cloud Architect"
