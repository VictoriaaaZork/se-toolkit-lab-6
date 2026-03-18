#!/usr/bin/env python3
"""Agent CLI that calls an LLM with tools to answer questions from the wiki."""

import json
import re
import sys
from pathlib import Path
from typing import Any

import httpx

MAX_TOOL_CALLS = 10
PROJECT_ROOT = Path(__file__).parent.resolve()
MAX_TOOL_RESULT_LENGTH = 4000


def load_env_file(path: Path) -> dict[str, str]:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def load_agent_env() -> dict[str, str]:
    return load_env_file(Path(".env.agent.secret"))


def is_safe_path(requested_path: str) -> bool:
    full_path = (PROJECT_ROOT / requested_path).resolve()
    return str(full_path).startswith(str(PROJECT_ROOT))


def read_file(path: str) -> str:
    if not is_safe_path(path):
        return f"Error: Access denied - path '{path}' is outside project directory"
    full_path = PROJECT_ROOT / path
    if not full_path.exists():
        return f"Error: File not found - '{path}'"
    if not full_path.is_file():
        return f"Error: Not a file - '{path}'"
    try:
        return full_path.read_text()
    except Exception as e:
        return f"Error reading file: {e}"


def list_files(path: str) -> str:
    if not is_safe_path(path):
        return f"Error: Access denied - path '{path}' is outside project directory"
    full_path = PROJECT_ROOT / path
    if not full_path.exists():
        return f"Error: Directory not found - '{path}'"
    if not full_path.is_dir():
        return f"Error: Not a directory - '{path}'"
    try:
        entries = []
        for entry in sorted(full_path.iterdir()):
            suffix = "/" if entry.is_dir() else ""
            entries.append(f"{entry.name}{suffix}")
        return "\n".join(entries)
    except Exception as e:
        return f"Error listing directory: {e}"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the project repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from project root"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative directory path from project root"}
                },
                "required": ["path"]
            }
        }
    }
]


SYSTEM_PROMPT = """You are a documentation assistant. Use tools to navigate the wiki.

Tools: list_files, read_file

Process:
1. Use list_files to discover wiki files
2. Use read_file to read relevant files
3. Find the answer and include source as: file_path#section_anchor

When you have the answer, respond with text (no tool calls) including the answer and source."""


def execute_tool(tool_name: str, args: dict[str, Any]) -> str:
    if tool_name == "read_file":
        result = read_file(args.get("path", ""))
    elif tool_name == "list_files":
        result = list_files(args.get("path", ""))
    else:
        result = f"Error: Unknown tool '{tool_name}'"
    if len(result) > MAX_TOOL_RESULT_LENGTH:
        result = result[:MAX_TOOL_RESULT_LENGTH] + "\n\n[...truncated...]"
    return result
