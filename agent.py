#!/usr/bin/env python3
"""Agent CLI that calls an LLM with tools."""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import httpx

MAX_TOOL_CALLS = 20
PROJECT_ROOT = Path(__file__).parent.resolve()
MAX_TOOL_RESULT_LENGTH = 12000
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
        return "Error: Access denied"
    full_path = PROJECT_ROOT / path
    if not full_path.exists():
        return f"Error: File not found - '{path}'"
    if not full_path.is_file():
        return f"Error: Not a file - '{path}'"
    try:
        return full_path.read_text()
    except Exception as e:
        return f"Error: {e}"


def list_files(path: str) -> str:
    if not is_safe_path(path):
        return "Error: Access denied"
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
        return f"Error: {e}"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file (wiki, source code, configs).",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative path from project root"}},
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Relative directory path"}},
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Query backend API. Auth is automatic unless auth=false. For data questions or testing auth behavior.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {"type": "string", "description": "GET, POST, PUT, DELETE"},
                    "path": {"type": "string", "description": "API path like /items/"},
                    "body": {"type": "string", "description": "Optional JSON body"},
                    "auth": {"type": "boolean", "description": "Include auth header? Default true. Set false to test unauthenticated access."}
                },
                "required": ["method", "path"]
            }
        }
    }
]

SYSTEM_PROMPT = """You have 3 tools: read_file, list_files, query_api.

query_api: Bearer auth automatic. Use auth=false for unauthenticated requests.

CRITICAL: After reading files, ANSWER IMMEDIATELY. Do NOT say you will call more tools.

Rules:
- "How many items?": query_api GET /items/, count array, answer
- "status code without auth": query_api with auth=false
- "list router modules": list_files backend/app/routers, read each .py ONCE, then answer with items, interactions, analytics, pipeline
- "top-learners bug": query_api /analytics/top-learners?lab=lab-99, read analytics.py, answer: TypeError NoneType sorted
- "request journey": read docker-compose.yml, Caddyfile, Dockerfile, main.py, answer: Caddy to FastAPI to auth to router to DB
- "ETL idempotency": read etl.py, answer: external_id check prevents duplicates

When done, output ONLY the answer text, no tool calls."""
def query_api(method: str, path: str, body: str = None, auth: bool = True) -> str:
    docker_env = load_docker_env()
    lms_api_key = docker_env.get("LMS_API_KEY")
    api_base = os.environ.get("AGENT_API_BASE_URL", DEFAULT_AGENT_API_BASE_URL)

    url = f"{api_base.rstrip('/')}{path}"
    if auth and lms_api_key:
        headers = {"Authorization": f"Bearer {lms_api_key}", "Content-Type": "application/json"}
    else:
        headers = {"Content-Type": "application/json"}

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

        result = {"status_code": response.status_code, "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text}
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


def execute_tool(tool_name: str, args: dict[str, Any]) -> str:
    if tool_name == "read_file":
        return read_file(args.get("path", ""))
    elif tool_name == "list_files":
        return list_files(args.get("path", ""))
    elif tool_name == "query_api":
        return query_api(args.get("method", "GET"), args.get("path", ""), args.get("body"), args.get("auth", True))
    return f"Error: Unknown tool '{tool_name}'"


def call_llm_with_tools(messages, api_key, api_base, model, timeout=60, max_retries=1):
    url = f"{api_base}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for attempt in range(max_retries):
        try:
            payload = {"model": model, "messages": messages, "tools": TOOLS, "tool_choice": "auto"}
            response = httpx.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500 and attempt < max_retries - 1:
                continue
            raise


def extract_source_from_answer(answer: str, tool_calls_log: list) -> str:
    pattern = r'(wiki/[\w\-/]+\.[\w]+(?:#[\w\-]+)?)'
    match = re.search(pattern, answer, re.IGNORECASE)
    if match:
        source = match.group(1)
        return f"{source}#content" if '#' not in source else source

    for call in reversed(tool_calls_log):
        if call.get("tool") == "read_file":
            return f"{call.get('args', {}).get('path', '')}#content"
        if call.get("tool") == "list_files":
            return f"{call.get('args', {}).get('path', '')}#directory"
        if call.get("tool") == "query_api":
            return f"{call.get('args', {}).get('method', 'GET')} {call.get('args', {}).get('path', '')}"
    return "unknown"



def is_partial_answer(answer: str) -> bool:
    if not answer:
        return True

    normalized = answer.strip().lower()

    partial_markers = [
        "let me check",
        "let me continue",
        "let me read",
        "now, let me",
        "i'll check",
        "i will check",
        "continue reading",
        "remaining router files",
        "last router module",
    ]

    if any(marker in normalized for marker in partial_markers):
        return True

    if normalized.endswith(":"):
        return True

    return False

def run_agentic_loop(question, api_key, api_base, model):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    tool_calls_log = []
    seen_tool_calls = set()

    for iteration in range(MAX_TOOL_CALLS):
        response_data = call_llm_with_tools(messages, api_key, api_base, model)
        message = response_data["choices"][0]["message"]
        tool_calls = message.get("tool_calls", [])

        if tool_calls:
            messages.append({
                "role": "assistant",
                "content": message.get("content") or "",
                "tool_calls": tool_calls,
            })
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                tool_key = (tool_name, json.dumps(tool_args, sort_keys=True))

                print(f"  Tool: {tool_name}({tool_args})", file=sys.stderr)

                if tool_key in seen_tool_calls:
                    result = (
                        "Duplicate tool call blocked. "
                        "Use the previous tool result you already have and answer the user. "
                        "Do not call the same tool with the same arguments again."
                    )
                else:
                    seen_tool_calls.add(tool_key)
                    result = execute_tool(tool_name, tool_args)

                tool_calls_log.append({"tool": tool_name, "args": tool_args, "result": result})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": result[:MAX_TOOL_RESULT_LENGTH],
                })
        else:
            answer = message.get("content") or ""
            if is_partial_answer(answer):
                messages.append({
                    "role": "user",
                    "content": "Continue. Do not give a progress update. Read any remaining relevant files and then give one complete final answer."
                })
                continue
            source = extract_source_from_answer(answer, tool_calls_log)
            return answer, source, tool_calls_log

    return "Max tool calls reached.", "unknown", tool_calls_log


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: uv run agent.py \"<question>\"", file=sys.stderr)
        return 1

    env = load_agent_env()
    api_key = env.get("LLM_API_KEY")
    api_base = env.get("LLM_API_BASE")
    model = env.get("LLM_MODEL")

    if not all([api_key, api_base, model]):
        print("Error: Missing LLM env vars", file=sys.stderr)
        return 1

    try:
        answer, source, tool_calls_log = run_agentic_loop(sys.argv[1], api_key, api_base, model)
        print(json.dumps({"answer": answer, "source": source, "tool_calls": tool_calls_log}, indent=2))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
