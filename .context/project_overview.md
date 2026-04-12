# Project Overview: Agentic Graph-RAG Engine

## Goal
To transform Robot Framework test results (`output.xml`) into deep, actionable root cause analysis using a hybrid Graph-Vector RAG architecture.

## Tech Stack
- **Backend**: Python 3.12, FastAPI, LangChain.
- **Database**: Neo4j (Graph Knowledge Base), FAISS (In-memory Vector storage).
- **Frontend**: Vanilla JS, CSS (Glassmorphism), `marked.js` (Markdown rendering), `lucide` (Icons).
- **Inference**: OpenRouter (ChatOpenAI wrapper).

## Core Philosophy
1. **Markdown-First**: The agent avoids complex JSON parsing in the backend for reports; it produces structured Markdown which the frontend renders directly.
2. **Audit Logging**: Every step of the pipeline (Parsing -> Graph -> Vector -> AI) is logged to `logs/audit.log`.
3. **Graph-Enhanced Logic**: Uses Neo4j to resolve keyword dependencies and "past failure" memory, providing the AI with much deeper context than vector search alone.
4. **Production Grade**: No hardcoded secrets (uses `.env`), modular package structure (`engine/`), and Dockerized infrastructure.
