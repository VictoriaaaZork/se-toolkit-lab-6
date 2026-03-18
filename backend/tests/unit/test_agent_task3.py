"""Regression tests for agent.py (Task 3) - System Agent."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
AGENT_PATH = PROJECT_ROOT / "agent.py"


class TestSystemAgent:
    """Test system agent tool usage."""

    @pytest.mark.skipif(not AGENT_PATH.exists(), reason="agent.py not found")
    def test_framework_question_uses_read_file(self):
        """Test framework question uses read_file."""
        result = subprocess.run(
            [sys.executable, str(AGENT_PATH), "What Python web framework does the backend use?"],
            capture_output=True, text=True, timeout=120,
        )
        # Test passes if agent uses read_file (even if answer incomplete)
        data = json.loads(result.stdout.strip())
        tool_names = [c.get("tool") for c in data.get("tool_calls", [])]
        assert "read_file" in tool_names, "Expected read_file to be used"

    @pytest.mark.skipif(not AGENT_PATH.exists(), reason="agent.py not found")
    def test_items_count_uses_query_api(self):
        """Test items count question uses query_api."""
        result = subprocess.run(
            [sys.executable, str(AGENT_PATH), "How many items are in the database?"],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        tool_names = [c.get("tool") for c in data.get("tool_calls", [])]
        assert "query_api" in tool_names, "Expected query_api to be used"
