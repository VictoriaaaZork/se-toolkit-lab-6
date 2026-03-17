"""Regression tests for agent.py (Task 1).

These tests run agent.py as a subprocess, parse the stdout JSON,
and verify the required fields are present.

Run with: uv run pytest backend/tests/unit/test_agent_task1.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


# Project root is 3 levels up from backend/tests/unit/
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
AGENT_PATH = PROJECT_ROOT / "agent.py"


class TestAgentOutput:
    """Test that agent.py produces valid JSON output with required fields."""

    @pytest.mark.skipif(
        not AGENT_PATH.exists(),
        reason="agent.py not found - run this test from project root",
    )
    def test_agent_returns_valid_json_with_required_fields(self):
        """Test that agent outputs valid JSON with 'answer' and 'tool_calls' fields."""
        result = subprocess.run(
            [sys.executable, str(AGENT_PATH), "What is 2+2?"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Agent failed: {result.stderr}"
        assert result.stdout.strip(), "Agent produced no output"

        try:
            data = json.loads(result.stdout.strip())
        except json.JSONDecodeError as e:
            pytest.fail(f"Agent output is not valid JSON: {e}\nOutput: {result.stdout[:200]}")

        assert "answer" in data, "Missing 'answer' field in output"
        assert isinstance(data["answer"], str), "'answer' must be a string"
        assert len(data["answer"]) > 0, "'answer' must not be empty"
        assert "tool_calls" in data, "Missing 'tool_calls' field in output"
        assert isinstance(data["tool_calls"], list), "'tool_calls' must be a list"

    @pytest.mark.skipif(
        not AGENT_PATH.exists(),
        reason="agent.py not found - run this test from project root",
    )
    def test_agent_stderr_does_not_contaminate_stdout(self):
        """Test that debug output goes to stderr, not stdout."""
        result = subprocess.run(
            [sys.executable, str(AGENT_PATH), "Say hello"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        stdout_lines = result.stdout.strip().splitlines()
        assert len(stdout_lines) == 1, f"stdout should have exactly 1 line, got {len(stdout_lines)}"
        json.loads(result.stdout.strip())
