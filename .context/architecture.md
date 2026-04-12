# Architecture: Hybrid Graph-Vector RAG

The system operates in a multi-stage data retrieval pipeline to provide maximum context to the AI Agent.

## 1. Static Knowledge (Neo4j)
Initialized via `python run.py --init-kb <dir>`, this phase parses all `.robot` and `.resource` files.
- **TestCase Nodes**: Track names, tags, and direct steps.
- **Keyword Nodes**: Track definitions, source files, and `raw_text` (code content).
- **CALLS Relationship**: Maps the relationship from Tests to Keywords, and Keywords to other Keywords (recursive traversal).

## 2. Dynamic Failure Retrieval
When an `output.xml` is uploaded:
- **XML Parsing**: Identifies failed tests, the specific keyword where it crashed, and extracts `console_logs`.
- **Vector Indexing (Memory-Only)**: Temporarily indexes all current run failures in FAISS to find systemic cross-test patterns.

## 3. The Retrieval Loop
For every failed test:
1. **Graph Lookup**: Resolves all keywords used (recursively) and any `PastFailure` memory nodes.
2. **Vector Lookup**: Finds similar crashes in the current run.
3. **Augmentation**: Combines Code Structure + Failure History + Systemic Context into a single prompt.

## 4. Inference & Storage
- **Inference**: LLM generates a Markdown Root Cause Analysis (RCA).
- **Graph Storage**: The RCA is saved back to Neo4j as a `PastFailure` node linked to the `TestCase` via `HAD_FAILURE`.
