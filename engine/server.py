import os
import json
import shutil
import time
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse

from langchain_community.vectorstores import FAISS
from langchain_neo4j import Neo4jGraph
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from engine.config import (
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD,
    OPENROUTER_API_KEY, LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE,
    EMBEDDING_MODEL,
)
from engine.parser import parse_output_xml
from engine.helpers import failure_to_doc

app = FastAPI(title="Agentic RAG Engine")

# Ensure necessary directories exist
os.makedirs("ui", exist_ok=True)
os.makedirs("temp_data", exist_ok=True)
app.mount("/static", StaticFiles(directory="ui"), name="static")

@app.get("/")
def serve_index():
    return FileResponse("ui/index.html")



@app.post("/api/analyze")
async def analyze_failures(file: UploadFile = File(...)):
    def event_stream():
        # Multi-user safe: unique filename per request
        unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        temp_file_path = f"temp_data/output_{unique_id}.xml"
        
        yield json.dumps({"type": "status", "message": f"Receiving file: {file.filename}..."}) + "\n"
        
        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            yield json.dumps({"type": "error", "message": f"Failed to save uploaded file: {str(e)}"}) + "\n"
            return
            
        try:
            yield json.dumps({"type": "status", "message": f"Parsing XML output '{file.filename}'..."}) + "\n"
            try:
                failures = parse_output_xml(temp_file_path)
            except Exception as e:
                yield json.dumps({"type": "error", "message": f"Error parsing XML: {str(e)}"}) + "\n"
                return

            if not failures:
                yield json.dumps({"type": "done", "message": "All Tests Passed!"}) + "\n"
                return

            yield json.dumps({"type": "status", "message": f"Found {len(failures)} failed tests. Initializing DB connections..."}) + "\n"

            try:
                robot_graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
                embedding = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
                yield json.dumps({"type": "status", "message": "✓ Connected to Neo4j Graph DB & Embeddings Model."}) + "\n"
            except Exception as e:
                yield json.dumps({"type": "error", "message": f"Database/Embedding connection failed: {str(e)}"}) + "\n"
                return

            llm = ChatOpenAI(
                model=LLM_MODEL,
                api_key=OPENROUTER_API_KEY or "DEBUG_KEY",
                base_url=LLM_BASE_URL,
                temperature=LLM_TEMPERATURE,
            )

            yield json.dumps({"type": "status", "message": "Embedding trace logs into temporary FAISS memory..."}) + "\n"
            failure_docs = [failure_to_doc(f) for f in failures]
            temp_failure_db = FAISS.from_documents(failure_docs, embedding)

            for failure in failures:
                yield json.dumps({"type": "status", "message": f"► [Test: {failure.name}] Resolving Keyword Traversal Graph..."}) + "\n"
                
                cypher_query = """
                MATCH (t:TestCase {name: $test_name})
                OPTIONAL MATCH (t)-[:CALLS*]->(k:Keyword)
                OPTIONAL MATCH (t)-[:HAD_FAILURE]->(f:PastFailure)
                RETURN t.name AS test_name, t.tags AS test_tags, t.steps AS test_steps, 
                       collect(DISTINCT {name: k.name, raw_text: k.raw_text}) AS nested_keywords,
                       collect(DISTINCT {error: f.error_message, rca: f.rca_content, date: f.timestamp}) AS past_failures
                """
                graph_results = robot_graph.query(cypher_query, params={"test_name": failure.name})
                
                if not graph_results:
                    expected_content = f"Test Case '{failure.name}' not found in Static Neo4j Knowledge Graph."
                else:
                    data = graph_results[0]
                    expected_content = f"Test: {data['test_name']}\nTags: {', '.join(data.get('test_tags', []))}\nExpected Flow: {' -> '.join(data.get('test_steps', []))}"
                    kws = data.get('nested_keywords', [])
                    if kws and any(k.get('name') for k in kws):
                        glossary_str = "\n\n".join([f"--- {k['name']} ---\n{k.get('raw_text', '')}" for k in kws if k.get('name')])
                        expected_content += f"\n\n[KEYWORD DEFINITIONS]\n{glossary_str}"
                    
                    past_fails = data.get('past_failures', [])
                    if past_fails and any(pf.get('error') for pf in past_fails):
                        past_str = "\n\n".join([f"Time: {pf.get('date', 'Unknown')}\nError: {pf.get('error')}\nPrevious RCA: {pf.get('rca', '')}" for pf in past_fails if pf.get('error')])
                        expected_content += f"\n\n[PAST FAILURES MEMORY]\nThe following are previous recorded failures for this exact same test case. Use them to understand if this is a recurring issue or if past fixes failed.\n\n{past_str}"

                yield json.dumps({"type": "status", "message": f"► [Test: {failure.name}] Fetching Vector Context Memory..."}) + "\n"
                # Remove the hard filter to allow vector cross-pollination of systemic identical failures across the repo
                search_query = f"Keyword mapping failure '{failure.failed_keyword}' yielding '{failure.failed_keyword_message}'."
                exec_results = temp_failure_db.similarity_search(search_query, k=4)
                exec_content = "\n\n---\n\n".join([f"[SIMILAR RUNTIME CRASH LOG: {doc.metadata.get('test', 'Unknown')}]\n{doc.page_content}" for doc in exec_results])

                yield json.dumps({"type": "status", "message": f"⚡ [Test: {failure.name}] Initiating Agentic RCA Inference..."}) + "\n"

                prompt = f"""
================ SYSTEM PROMPT ================
You are a root cause analysis engine for Robot Framework testing. 
Analyze the failure based on the following retrieved contexts from our Vector Databases.

[EXPECTED KNOWLEDGE BASE (NEO4J)]
{expected_content}

[RUNTIME CRASH CONTEXT (FAISS MEMORY)]
{exec_content}

TASK: Analyze why '{failure.name}' broke. You must structure your output STRICTLY with the following sections formatted in Markdown:

1. **Root Cause & Expected Behavior**: Explain the exact cause of the failure and what the behavior was expected to be.
2. **Test Fix Needed**: Detail any specific modifications required within the Robot Framework test scripts.
3. **System Bug / Issue**: Determine if this is an underlying system/application bug. If yes, write a brief bug report summary.
4. **Recommendations / Context**: Any further actions required, missing variables, or confidence metrics.
===============================================
"""
                try:
                    # Bypass LLM strictly to route Context Engine directly to UI for debugging
                    # response = llm.invoke(prompt)
                    # rca_text = response.content
                    rca_text = "✨ PROMPT DEBUG MODE:\n\n" + prompt
                except Exception as e:
                    rca_text = f"API Evaluation failed: {str(e)}"
                    
                try:
                    write_query = """
                    MATCH (t:TestCase {name: $test_name})
                    MERGE (t)-[:HAD_FAILURE]->(f:PastFailure)
                    SET f.failed_keyword = $failed_kw,
                        f.error_message = $error_msg,
                        f.rca_content = $rca,
                        f.timestamp = datetime()
                    """
                    robot_graph.query(write_query, params={
                        "test_name": failure.name,
                        "failed_kw": failure.failed_keyword,
                        "error_msg": failure.failed_keyword_message,
                        "rca": rca_text
                    })
                    yield json.dumps({"type": "status", "message": f"💾 Saved LLM Analysis to Permanent Graph Memory."}) + "\n"
                except Exception as e:
                    yield json.dumps({"type": "error", "message": f"Failed to save to graph memory: {str(e)}"}) + "\n"
                    
                yield json.dumps({
                    "type": "result",
                    "data": {
                        "test_name": failure.name,
                        "failed_keyword": failure.failed_keyword,
                        "error_message": failure.failed_keyword_message,
                        "rca": rca_text,
                        "tags": failure.tags
                    }
                }) + "\n"

            yield json.dumps({"type": "done", "message": "Analysis Pipeline Completed successfully!"}) + "\n"
        finally:
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
