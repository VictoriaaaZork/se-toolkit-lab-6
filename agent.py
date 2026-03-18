#!/usr/bin/env python3
"""Agent CLI that calls an LLM with tools to answer questions from wiki and backend API."""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import httpx

MAX_TOOL_CALLS = 10
PROJECT_ROOT = Path(__file__).parent.resolve()
MAX_TOOL_RESULT_LENGTH = 4000
DEFAULT_AGENT_API_BASE_URL = "http://localhost:42002"


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


def load_docker_env() -> dict[str, str]:
    return load_env_file(Path(".env.docker.secret"))


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
            "description": "Read the contents of a file from the project repository. Use this to read wiki files, source code, or configuration files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md', 'backend/app/main.py')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path. Use this to discover what files exist in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root (e.g., 'wiki', 'backend/app/routers')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Query the backend LMS API. Use for questions about current data (item counts, scores), API behavior (status codes), or runtime errors. Requires authentication.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, PUT, DELETE)"
                    },
                    "path": {
                        "type": "string",
                        "description": "API path (e.g., '/items/', '/analytics/completion-rate')"
                    },
                    "body": {
                        "type": "string",
                        "description": "Optional JSON request body for POST/PUT requests"
                    }
                },
                "required": ["method", "path"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are a documentation and system assistant for a software engineering project.

Available tools:
1. list_files - List files and directories at a given path
2. read_file - Read the contents of a file (wiki, source code, configs)
3. query_api - Query the backend LMS API (requires authentication)

Tool selection guide:
- Use list_files/read_file for: wiki documentation, source code, configuration files (docker-compose.yml, Dockerfile, etc.)
- Use query_api for: current data (item counts, scores, completion rates), API behavior (status codes, error responses), runtime errors

Common API endpoints:
- GET /items/ - List all items in the database
- GET /items/{id} - Get a specific item by ID
- GET /analytics/completion-rate?lab=lab-XX - Get completion rate for a lab
- GET /analytics/top-learners?lab=lab-XX - Get top learners for a lab
- GET /analytics/scores?lab=lab-XX - Get score distribution for a lab
- GET /analytics/pass-rates?lab=lab-XX - Get pass rates per task for a lab
- GET /analytics/timeline?lab=lab-XX - Get submissions timeline for a lab
- GET /analytics/groups?lab=lab-XX - Get per-group performance for a lab

Process:
1. For wiki/source questions: use list_files to discover files, then read_file to read content
2. For data/API questions: use query_api to fetch current data or test API behavior
3. For bug diagnosis: use query_api to reproduce the error, then read_file to find the bug in source code
4. Find the answer and include source reference (file path + section anchor for files, endpoint for API)

When you have the answer, respond with a text message (no tool calls) that includes:
- The answer to the user's question
- The source reference (file path#section or API endpoint used)"""


def query_api(method: str, path: str, body: str = None) -> str:
    docker_env = load_docker_env()
    lms_api_key = docker_env.get("LMS_API_KEY")
    api_base = os.environ.get("AGENT_API_BASE_URL", DEFAULT_AGENT_API_BASE_URL)

    if not lms_api_key:
        return json.dumps({"error": "LMS_API_KEY not found in .env.docker.secret"})

    url = f"{api_base.rstrip('/')}{path}"
    headers = {
        "X-API-Key": lms_api_key,
        "Content-Type": "application/json",
    }

    try:
        print(f"  Querying API: {method} {url}", file=sys.stderr)
        if method.upper() == "GET":
            response = httpx.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = httpx.post(url, headers=headers, json=json.loads(body) if body else {}, timeout=30)
        elif method.upper() == "PUT":
            response = httpx.put(url, headers=headers, json=json.loads(body) if body else {}, timeout=30)
        elif method.upper() == "DELETE":
            response = httpx.delete(url, headers=headers, timeout=30)
        else:
            return json.dumps({"error": f"Unsupported method: {method}"})

        result = {
            "status_code": response.status_code,
            "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }
        return json.dumps(result)
    except httpx.TimeoutException:
        return json.dumps({"error": "API request timed out"})
    except httpx.HTTPError as e:
        return json.dumps({"error": str(e), "status_code": getattr(e.response, "status_code", None)})
    except Exception as e:
        return json.dumps({"error": str(e)})


def execute_tool(tool_name: str, args: dict[str, Any]) -> str:
    if tool_name == "read_file":
        result = read_file(args.get("path", ""))
    elif tool_name == "list_files":
        result = list_files(args.get("path", ""))
    elif tool_name == "query_api":
        result = query_api(args.get("method", "GET"), args.get("path", ""), args.get("body"))
    else:
        result = f"Error: Unknown tool '{tool_name}'"

    if len(result) > MAX_TOOL_RESULT_LENGTH:
        result = result[:MAX_TOOL_RESULT_LENGTH] + "\n\n[...truncated...]"
    return result


def call_llm_with_tools(messages, api_key, api_base, model, timeout=60, max_retries=3):
    url = f"{api_base}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for attempt in range(max_retries):
        try:
            payload = {"model": model, "messages": messages, "tools": TOOLS, "tool_choice": "auto"}
            print(f"Calling LLM at {url}... (attempt {attempt + 1}/{max_retries})", file=sys.stderr)
            response = httpx.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            print(f"LLM response received", file=sys.stderr)
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500 and attempt < max_retries - 1:
                print(f"Server error (500), retrying...", file=sys.stderr)
                continue
            raise


def extract_source_from_answer(answer: str, tool_calls_log: list) -> str:
    pattern = r'(wiki/[\w\-/]+\.[\w]+(?:#[\w\-]+)?)'
    match = re.search(pattern, answer, re.IGNORECASE)
    if match:
        source = match.group(1)
        if '#' not in source:
            source = f"{source}#content"
        return source

    source_match = re.search(r'Source:\s*(\S+)', answer, re.IGNORECASE)
    if source_match:
        source = source_match.group(1)
        if source.startswith('/') or source.startswith('GET') or source.startswith('POST'):
            return source

    for call in reversed(tool_calls_log):
        if call.get("tool") == "read_file":
            path = call.get("args", {}).get("path", "")
            if path.startswith("wiki/") or path.endswith(".py") or path.endswith(".yml") or path.endswith(".md"):
                return f"{path}#content"

    for call in reversed(tool_calls_log):
        if call.get("tool") == "list_files":
            path = call.get("args", {}).get("path", "")
            return f"{path}#directory-listing"

    for call in reversed(tool_calls_log):
        if call.get("tool") == "query_api":
            method = call.get("args", {}).get("method", "GET")
            path = call.get("args", {}).get("path", "")
            return f"{method} {path}"

    return "unknown"


def run_agentic_loop(question, api_key, api_base, model):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    tool_calls_log = []

    for iteration in range(MAX_TOOL_CALLS):
        print(f"\n[Iteration {iteration + 1}/{MAX_TOOL_CALLS}]", file=sys.stderr)
        response_data = call_llm_with_tools(messages, api_key, api_base, model)
        message = response_data["choices"][0]["message"]
        tool_calls = message.get("tool_calls", [])

        if tool_calls:
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                print(f"  Executing tool: {tool_name}({tool_args})", file=sys.stderr)
                result = execute_tool(tool_name, tool_args)
                tool_calls_log.append({"tool": tool_name, "args": tool_args, "result": result})
                messages.append({"role": "user", "content": f"[Tool output from {tool_name}]:\n{result}"})
                print(f"  Tool result: {len(result)} chars", file=sys.stderr)
        else:
            answer = message.get("content", "")
            print(f"\nFinal answer received ({len(answer)} chars)", file=sys.stderr)
            source = extract_source_from_answer(answer, tool_calls_log)
            return answer, source, tool_calls_log

    print("\nMax tool calls reached", file=sys.stderr)
    return "Max tool calls reached.", "unknown", tool_calls_log


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"<question>\"", file=sys.stderr)
        return 1

    question = sys.argv[1]
    env = load_agent_env()
    api_key = env.get("LLM_API_KEY")
    api_base = env.get("LLM_API_BASE")
    model = env.get("LLM_MODEL")

    if not api_key or not api_base or not model:
        print("Error: Missing LLM env vars in .env.agent.secret", file=sys.stderr)
        return 1

    print(f"Using model: {model}", file=sys.stderr)
    print(f"Project root: {PROJECT_ROOT}", file=sys.stderr)

    try:
        answer, source, tool_calls_log = run_agentic_loop(question, api_key, api_base, model)
        result = {"answer": answer, "source": source, "tool_calls": tool_calls_log}
        print(json.dumps(result, indent=2))
        return 0
    except httpx.TimeoutException:
        print("Error: LLM request timed out", file=sys.stderr)
        return 1
    except httpx.HTTPError as e:
        print(f"Error: HTTP error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
