# Project Overview: Agentic Graph-RAG Engine

## Goal
To transform Robot Framework test results (`output.xml`) into deep, actionable root cause analysis using a hybrid Graph-Vector RAG architecture.

## Tech Stack
- **Backend**: Python 3.12, FastAPI, LangChain.
- **Database**: Neo4j (Graph Knowledge Base), FAISS (In-memory Vector storage).
- **Frontend**: Vanilla JS, CSS (Glassmorphism), `marked.js` (Markdown rendering), `lucide` (Icons).
- **Inference**: OpenRouter (ChatOpenAI wrapper).

## Core Philosophy
1. **Markdown-First Reporting**: The agent produces structured Markdown reports which the frontend renders directly via `marked.js`, avoiding fragile JSON parsing in the backend.
2. **Automated KB Lifecycle**: The system uses a "Zero-Step" initialization. It automatically clones/pulls Git repositories and syncs the Knowledge Base on every startup.
3. **Real-time Streaming**: Status updates, logs, and AI analysis results are streamed to the UI in real-time using `StreamingResponse`.
4. **Graph-Enhanced Retrieval**: Uses Neo4j to resolve keyword dependencies and "past failure" memory, providing the AI with much deeper context than vector search alone.
5. **Production Reliability**: Centralized Audit Logging (`logs/audit.log`), multi-user safe file processing (`temp_data/`), and clean environment configuration.
