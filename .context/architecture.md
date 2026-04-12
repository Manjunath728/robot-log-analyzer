# Architecture: Hybrid Graph-Vector RAG

The system operates in a multi-stage data retrieval pipeline to provide maximum context to the AI Agent.

## 1. Automated Knowledge Base (Neo4j)
The KB is managed via a "Set and Forget" synchronization model.
- **Lifespan Sync**: On every server startup, the `lifespan` handler pulls/clones Git repos and local paths defined in `KB_REPOS`.
- **TestCase Nodes**: Track names, tags, and direct steps.
- **Keyword Nodes**: Track definitions, source files, and `raw_text` (code content).
- **CALLS Relationship**: Maps the relationship from Tests to Keywords, and Keywords to other Keywords (recursive traversal).

## 2. Dynamic Failure Retrieval
When an `output.xml` is uploaded:
- **XML Parsing**: Identifies failed tests, the specific keyword where it crashed, and extracts `console_logs`.
- **Vector Indexing (Memory-Only)**: Temporarily indexes all current run failures in FAISS to find systemic cross-test patterns.

## 3. The Retrieval & Analysis Loop
For every failed test:
1. **Graph Lookup**: Resolves all keywords used (recursively) and any `PastFailure` memory nodes.
2. **Vector Lookup**: Finds similar crashes in the current run failure memory.
3. **Augmentation**: Combines code structure + failure history + systemic context into a prompt.
4. **Streaming Inference**: The AI generates a Markdown RCA report which is streamed to the UI.
5. **Memory Storage**: The RCA is saved back to Neo4j as a `PastFailure` node linked to the `TestCase` via `HAD_FAILURE`.

## 4. UI Communication
- **Event Streaming**: Uses `NDJSON` (Newline Delimited JSON) streams over `StreamingResponse`.
- **Buffering**: The frontend implements a chunk-reassembly buffer to ensure fragmented network packets don't break JSON parsing.
