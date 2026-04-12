"""
Centralized configuration loader for the Agentic RAG Engine.
All environment variables are loaded from .env and exposed as module-level constants.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# LLM
_llm_enabled_raw = os.getenv("LLM_ENABLED", os.getenv("LLM_DEBUG", "false")).lower()
LLM_ENABLED = _llm_enabled_raw == "true"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "x-ai/grok-4.20")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# Embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "microsoft/codebert-base")

# Knowledge Base Automation
_kb_repos_raw = os.getenv("KB_REPOS", '["examples"]')
try:
    KB_REPOS = json.loads(_kb_repos_raw)
except Exception:
    # Fallback for simple comma-separated string if JSON parsing fails
    KB_REPOS = [r.strip() for r in _kb_repos_raw.split(",") if r.strip()]
