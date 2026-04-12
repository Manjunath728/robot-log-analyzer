# Development Patterns & Gotchas

This document contains critical implementation patterns for future development of the Agentic RAG Engine.

## 1. Zero-Trust LLM Formatting
The AI is instructed to output Markdown. When using Python f-strings for prompts, **double the curly braces** `{{` and `}}` if they are part of the instructions (e.g., example JSON or code blocks) to avoid `ValueError: Invalid format specifier`.

## 2. Markdown-First UI
Do not attempt to parse complex JSON in the backend for RCA reports. The system is designed to pass an AI-generated Markdown string directly to the frontend. The frontend uses `marked.js` in `app.js` to render this safely and beautifully.

## 3. Schema Bootstrapping
Neo4j requires "Schema Warmup" to avoid warnings about non-existent labels or properties on fresh clusters.
- **Pattern**: During `cli.py:init_kb`, we execute `CREATE INDEX IF NOT EXISTS` for `PastFailure` and `Keyword` nodes.
- **Limitation**: Always use `CREATE INDEX` instead of `CREATE CONSTRAINT REQUIRED` for property existence, as the latter is a Neo4j Enterprise-only feature.

## 4. Multi-User Safety
All uploads are processed using a `unique_id` (timestamp + uuid) into the `temp_data/` folder.
- **Cleanup**: The `server.py` analyze endpoint uses a `finally` block to ensure `output.xml` is deleted from the server immediately after analysis completes.

## 5. Audit Logging
Avoid `print()` in production modules. Use `from engine.logger import logger`.
- **Level**: Controlled via `LOG_LEVEL` in `.env`.
- **Audit Trail**: Everything is persisted to `logs/audit.log`, which is the first place an agent should check if the pipeline slows down or fails.
