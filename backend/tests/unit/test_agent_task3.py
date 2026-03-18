"""Regression tests for agent.py (Task 3) - System Agent with query_api tool."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
AGENT_PATH = PROJECT_ROOT / "agent.py"


class TestSystemAgent:
    @pytest.mark.skipif(not AGENT_PATH.exists(), reason="agent.py not found")
    def test_framework_question_uses_read_file(self):
        result = subprocess.run(
            [sys.executable, str(AGENT_PATH), "What Python web framework does the backend use?"],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0, f"Agent failed: {result.stderr}"
        data = json.loads(result.stdout.strip())
        assert "answer" in data and "source" in data and "tool_calls" in data
        assert len(data["tool_calls"]) > 0
        tool_names = [c.get("tool") for c in data["tool_calls"]]
        assert "read_file" in tool_names
        assert "fastapi" in data["answer"].lower()

    @pytest.mark.skipif(not AGENT_PATH.exists(), reason="agent.py not found")
    def test_items_count_question_uses_query_api(self):
        result = subprocess.run(
            [sys.executable, str(AGENT_PATH), "How many items are currently stored in the database?"],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0, f"Agent failed: {result.stderr}"
        data = json.loads(result.stdout.strip())
        assert "answer" in data and "source" in data and "tool_calls" in data
        assert len(data["tool_calls"]) > 0
        tool_names = [c.get("tool") for c in data["tool_calls"]]
        assert "query_api" in tool_names
        import re
        numbers = re.findall(r'\d+', data["answer"])
        assert len(numbers) > 0
