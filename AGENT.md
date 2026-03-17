# Agent Architecture - Task 1

## LLM Provider
**Provider:** Qwen Code API (self-hosted on VM)
**Model:** `qwen3-coder-plus`

## Data Flow
1. User runs: `uv run agent.py "question"`
2. Agent loads `.env.agent.secret` for API credentials
3. Agent sends HTTP POST to `{LLM_API_BASE}/chat/completions`
4. Agent outputs JSON to stdout: `{"answer": "...", "tool_calls": []}`
5. All debug output goes to stderr

## Running
uv run agent.py "What does REST stand for?"
uv run pytest backend/tests/unit/test_agent_task1.py -v
