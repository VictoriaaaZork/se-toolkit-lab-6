# Agent Architecture

## Task 2: The Documentation Agent

### Architecture

User Question  agent.py  LLM API  tool_calls  Execute tools  Feed back  Final answer

### Agentic Loop

1. Send question + tool definitions to LLM
2. LLM decides which tool to call
3. Execute tool (read_file / list_files)
4. Feed result back to LLM
5. Repeat until text answer or max 10 iterations

### Tools

#### read_file
Read a file from the project repository.
- Parameters: path (string) - Relative path from project root
- Security: No ../ traversal allowed

#### list_files
List files and directories at a given path.
- Parameters: path (string) - Relative directory path
- Security: No ../ traversal allowed

### Output Format
{
  "answer": "...",
  "source": "wiki/file.md#section",
  "tool_calls": [{"tool": "...", "args": {...}, "result": "..."}]
}

### Path Security
def is_safe_path(requested_path: str) -> bool:
    full_path = (PROJECT_ROOT / requested_path).resolve()
    return str(full_path).startswith(str(PROJECT_ROOT))

### Running
uv run agent.py "How do you resolve a merge conflict?"
uv run pytest backend/tests/unit/test_agent_task2.py -v
