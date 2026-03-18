"""Regression tests for agent.py (Task 2) - Documentation Agent with tools."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
AGENT_PATH = PROJECT_ROOT / "agent.py"


class TestDocumentationAgent:
    """Test that agent.py correctly uses tools to answer wiki questions."""

    @pytest.mark.skipif(not AGENT_PATH.exists(), reason="agent.py not found")
    def test_merge_conflict_question_uses_read_file(self):
        result = subprocess.run(
            [sys.executable, str(AGENT_PATH), "How do you resolve a merge conflict?"],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout.strip())
        assert "answer" in data and "source" in data and "tool_calls" in data
        assert len(data["tool_calls"]) > 0
