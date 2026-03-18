# Task 2 Plan: The Documentation Agent

## Overview

Transform the Task 1 CLI chatbot into an **agent** that can use tools to navigate the project wiki and answer
questions with proper source references.

## Architecture

User Question  agent.py  LLM (with tool definitions)  tool_calls  Execute tools  Feed results back 
Final answer with source

## Tool Definitions

### 1. read_file
Read a file from the project repository.
- Parameters: path (string) - Relative path from project root
- Security: No ../ traversal allowed
- Returns: File contents or error message

### 2. list_files
List files and directories at a given path.
- Parameters: path (string) - Relative directory path from project root
- Security: No ../ traversal allowed
- Returns: Newline-separated listing

## Path Security

Both tools use is_safe_path() to prevent directory traversal:
- Resolve full absolute path using Path.resolve()
- Check resolved path starts with project root
- Reject paths escaping project directory

## Agentic Loop

1. Send question + tool definitions to LLM
2. LLM decides which tool to call
3. Execute tool, feed result back
4. Repeat until LLM returns text answer or max 10 iterations

## Output Format

{
  "answer": "...",
  "source": "wiki/file.md#section",
  "tool_calls": [{"tool": "...", "args": {...}, "result": "..."}]
}

## Files to Modify

| File | Action |
|------|--------|
| plans/task-2.md | Create (this plan) |
| agent.py | Update with tools + loop |
| AGENT.md | Update documentation |
| backend/tests/unit/test_agent_task2.py | Create tests |
