# Task 1 Plan  Call an LLM from Code

## Goal
Build a Python CLI program `agent.py` that accepts a user question as the first command-line argument, sends it to an OpenAI-compatible chat completions API, and prints a single JSON object to stdout with fields:
- `answer`
- `tool_calls`

For Task 1, `tool_calls` is always an empty array.

## LLM provider choice
I will use Qwen Code API via the OpenAI-compatible proxy endpoint available on the VM.

## Reasons
- OpenAI-compatible API
- available on the VM
- suitable for coding tasks
- no hardcoded credentials

## Model
`qwen3-coder-plus`

## Configuration
The agent will read the following variables from `.env.agent.secret`:
- `LLM_API_KEY`
- `LLM_API_BASE`
- `LLM_MODEL`

## Implementation structure

### agent.py
Responsibilities:
1. Parse the first CLI argument as the user question
2. Load environment variables from `.env.agent.secret`
3. Build a minimal chat completion request
4. Send an HTTP POST request to `/v1/chat/completions`
5. Extract assistant text from the response
6. Print valid JSON to stdout:
   `{"answer": "...", "tool_calls": []}`

### Error handling
- debug and validation messages go to stderr
- non-zero exit code on failure
- request timeout below 60 seconds

## Testing strategy
Create one regression test that:
1. starts a local mock HTTP server implementing `/v1/chat/completions`
2. writes test configuration into `.env.agent.secret`
3. runs `agent.py` as a subprocess
4. parses stdout as JSON
5. checks that `answer` and `tool_calls` are present

## Documentation
`AGENT.md` will describe:
- the architecture
- provider/model
- configuration
- run instructions
- testing approach
