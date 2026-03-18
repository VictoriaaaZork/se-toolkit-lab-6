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
