# Environment Variables Guide

This project uses a `.env` file for configuration. Below are the required and optional variables.

## 1. Neo4j Graph Database
- `NEO4J_URI`: Connection string (default: `bolt://localhost:7687`).
- `NEO4J_USERNAME`: Database username (default: `neo4j`).
- `NEO4J_PASSWORD`: Database password.

## 2. LLM Configuration (OpenRouter)
- `LLM_DEBUG`: Set to `true` for actual AI analysis. Set to `false` for "Prompt Audit" mode (returns raw prompt context to UI).
- `OPENROUTER_API_KEY`: Your OpenRouter API key.
- `LLM_MODEL`: The AI model to use (e.g., `nvidia/nemotron-3-super-120b-a12b:free`).
- `LLM_BASE_URL`: API endpoint (default: `https://openrouter.ai/api/v1`).
- `LLM_TEMPERATURE`: AI creativity level (default: `0.2`).

## 3. Knowledge Base Automation
- `KB_REPOS`: A JSON-formatted list of repository links or local paths.
  - **Local Example**: `["examples", "/home/user/my-tests"]`
  - **Git Example**: `["https://github.com/my-org/robot-tests.git"]`
  - **Mixed Example**: `["examples", "https://github.com/my-org/robot-tests.git"]`
  - *Note*: If a Git URL is provided, the engine automatically handles `git clone` or `git pull` during startup.

## 4. Embedding & Logging
- `EMBEDDING_MODEL`: The model used for vector search (default: `BAAI/bge-large-en-v1.5`).
- `LOG_LEVEL`: Threshold for logging (e.g., `DEBUG`, `INFO`, `WARNING`, `ERROR`).
- `LOG_FILE`: Path to the persistent audit log file (default: `logs/audit.log`).
