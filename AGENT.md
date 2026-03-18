# Agent Architecture - Task 3: The System Agent

## Overview
The system agent uses three tools to answer questions about wiki documentation, source code, and backend API data.

## Tools
1. list_files - List files in directories
2. read_file - Read file contents (wiki, source code, configs)
3. query_api - Query backend LMS API with LMS_API_KEY authentication

## Agentic Loop
1. Send question + tool definitions to LLM
2. LLM decides which tool to call
3. Execute tool, feed result back
4. Repeat until text answer or max 10 iterations

## Environment Variables

| Variable | Source |
|----------|--------|
| LLM_API_KEY, LLM_API_BASE, LLM_MODEL | .env.agent.secret |
| LMS_API_KEY | .env.docker.secret |
| AGENT_API_BASE_URL | env (default: http://localhost:42002) |

## Output Format

{
  "answer": "...",
  "source": "wiki/file.md#section or GET /endpoint",
  "tool_calls": [...]
}

## Running

uv run agent.py "Your question"
uv run run_eval.py

## Lessons Learned

Building the system agent revealed that tool descriptions critically affect LLM tool selection. The query_api tool must correctly authenticate with LMS_API_KEY from .env.docker.secret (not to be confused with LLM_API_KEY). Environment variable flexibility is essential since the autochecker injects different values. Error handling in tools allows the agent to see API errors for bug diagnosis. Result truncation at 4000 characters prevents context window overflow. Source extraction handles both file paths and API endpoints.
