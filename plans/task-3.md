 Task 3 Plan: The System Agent
 Overview
Extend Task 2 agent with query_api tool to interact with the deployed backend API.
 Tool: query_api

- Call backend LMS API with LMS_API_KEY authentication
- Parameters: method, path, body (optional)
- Returns: JSON with status_code and body
 Environment Variables

 Variable  Source 
------------------
 LLM_API_KEY, LLM_API_BASE, LLM_MODEL  .env.agent.secret 
 LMS_API_KEY  .env.docker.secret 
## Benchmark Results

**Final Score: 10/10 PASSED**

All local benchmark questions passed:
1.  Wiki: protect branch steps
2.  Wiki: SSH connection steps
3.  Framework: FastAPI
4.  API router modules: items, interactions, analytics, pipeline
5.  Items count: query_api returns count
6.  Status code without auth: 401
7.  Completion-rate bug: ZeroDivisionError
8.  Top-learners bug: TypeError NoneType sorted
9.  Request journey: Caddy  FastAPI  auth  router  DB
10.  ETL idempotency: external_id check prevents duplicates

## Iteration Strategy

1. **Fixed authentication**: Changed from X-API-Key to Bearer token auth
2. **Added auth parameter**: Allow query_api to test unauthenticated access
3. **Optimized system prompt**: Added specific rules for each question type
4. **Increased MAX_TOOL_CALLS**: From 10 to 20 for reasoning questions
5. **Prevented tool loops**: Added explicit instructions to answer after reading files
## Benchmark Results

**Final Score: 10/10 PASSED**

All local benchmark questions passed:
1.  Wiki: protect branch steps
2.  Wiki: SSH connection steps
3.  Framework: FastAPI
4.  API router modules: items, interactions, analytics, pipeline
5.  Items count: query_api returns count
6.  Status code without auth: 401
7.  Completion-rate bug: ZeroDivisionError
8.  Top-learners bug: TypeError NoneType sorted
9.  Request journey: Caddy  FastAPI  auth  router  DB
10.  ETL idempotency: external_id check prevents duplicates

## Iteration Strategy

1. **Fixed authentication**: Changed from X-API-Key to Bearer token auth
2. **Added auth parameter**: Allow query_api to test unauthenticated access
3. **Optimized system prompt**: Added specific rules for each question type
4. **Increased MAX_TOOL_CALLS**: From 10 to 20 for reasoning questions
5. **Prevented tool loops**: Added explicit instructions to answer after reading files
