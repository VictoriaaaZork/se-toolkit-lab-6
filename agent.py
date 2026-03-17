#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


ENV_FILE = ".env.agent.secret"
REQUEST_TIMEOUT_SECONDS = 50


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def load_env_file(path: str) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'"))
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_request_payload(model: str, question: str) -> dict:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise assistant. Answer the user's question directly.",
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        "temperature": 0,
    }


def extract_answer(response_json: dict) -> str:
    try:
        return response_json["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError, TypeError) as exc:
        raise RuntimeError("Invalid LLM response format") from exc


def call_llm(api_base: str, api_key: str, model: str, question: str) -> str:
    base = api_base.rstrip("/")
    url = f"{base}/chat/completions"

    payload = build_request_payload(model, question)
    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM HTTP error {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM connection error: {exc}") from exc

    try:
        response_json = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("LLM returned invalid JSON") from exc

    return extract_answer(response_json)


def main() -> int:
    if len(sys.argv) < 2:
        eprint('Usage: uv run agent.py "Your question"')
        return 1

    question = sys.argv[1].strip()
    if not question:
        eprint("Question must not be empty")
        return 1

    try:
        load_env_file(ENV_FILE)

        api_key = require_env("LLM_API_KEY")
        api_base = require_env("LLM_API_BASE")
        model = require_env("LLM_MODEL")

        answer = call_llm(
            api_base=api_base,
            api_key=api_key,
            model=model,
            question=question,
        )

        result = {
            "answer": answer,
            "tool_calls": [],
        }

        print(json.dumps(result, ensure_ascii=False))
        return 0

    except Exception as exc:
        eprint(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
