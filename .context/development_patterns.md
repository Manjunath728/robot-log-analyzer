# Development Patterns & Gotchas

This document contains critical implementation patterns for the Agentic RAG Engine.

## 1. Zero-Trust LLM Formatting
The AI is instructed to output Markdown. When using Python f-strings for prompts, **double the curly braces** `{{` and `}}` if they are part of the instructions to avoid `ValueError: Invalid format specifier`.

## 2. Real-time Streaming Architecture
The system uses `NDJSON` (Newline Delimited JSON) over `StreamingResponse`. 
- **Backend**: Use `yield json.dumps(...) + "\n"`.
- **Frontend**: **Crucial Pattern**: Fragmented network packets split JSON strings. Always use a `buffer` in `app.js` (see `while` loop logic) to collect characters until a `\n` is found before calling `JSON.parse()`. Failure to do this causes silent UI log failures during long AI inference phases.

## 3. Automated Startup Lifecycle
The server uses the FastAPI `lifespan` event to sync the Knowledge Base. 
- **Pattern**: `sync_kb_sources()` clones/pulls any repos defined in `KB_REPOS`.
- **Concurrency**: This runs before the server starts accepting traffic, ensuring that the first analysis request always sees the latest test code.

## 4. UI Feedback States
To avoid user anxiety during long AI calls:
- **Status Type**: `inference` triggers a pulsating "Brain" icon and shimmer effect in the logs.
- **Auto-scroll**: The `appendLog` function in `app.js` ensures the latest operation is always visible.

## 5. Multi-User Safety
All uploads are processed using a `unique_id` (timestamp + uuid) into the `temp_data/` folder.
- **Cleanup**: The `analyze` endpoint uses a `finally` block to ensure temporary XML files are deleted from the disk immediately after analysis.
