"""Regression tests for agent.py (Task 1)."""
import json, subprocess, sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
AGENT_PATH = PROJECT_ROOT / "agent.py"

class TestAgentOutput:
    @pytest.mark.skipif(not AGENT_PATH.exists(), reason="agent.py not found")
    def test_agent_returns_valid_json_with_required_fields(self):
        result = subprocess.run(
            [sys.executable, str(AGENT_PATH), "What is 2+2?"],
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result.returncode == 0, f"Agent failed: {result.stderr}"
        data = json.loads(result.stdout.strip())
        assert "answer" in data and isinstance(data["answer"], str) and len(data["answer"]) > 0
        assert "tool_calls" in data and isinstance(data["tool_calls"], list)

    @pytest.mark.skipif(not AGENT_PATH.exists(), reason="agent.py not found")
    def test_agent_stderr_does_not_contaminate_stdout(self):
        result = subprocess.run(
            [sys.executable, str(AGENT_PATH), "Say hello"],
            capture_output=True,
            text=True,
            timeout=60
        )
        assert len(result.stdout.strip().splitlines()) == 1
        json.loads(result.stdout.strip())
