"""
Centralized configuration loader for the Agentic RAG Engine.
All environment variables are loaded from .env and exposed as module-level constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
