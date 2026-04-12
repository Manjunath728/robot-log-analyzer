import os
import json
import shutil
import time
import uuid
import re
import subprocess
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse

from langchain_community.vectorstores import FAISS
from langchain_neo4j import Neo4jGraph
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from engine.config import (
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD,
    EMBEDDING_MODEL, LLM_DEBUG, OPENROUTER_API_KEY,
    LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE,
    KB_REPOS
)
from engine.parser import parse_output_xml
from engine.helpers import failure_to_doc
from engine.logger import logger
from engine.cli import bootstrap_schema, clear_db, load_repo_to_graph

def sync_kb_generator():
    """Generator for KB synchronization status updates."""
    yield json.dumps({"type": "status", "message": "🚀 Starting Knowledge Base Synchronization..."}) + "\n"
    
    try:
        graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
        bootstrap_schema(graph)
        yield json.dumps({"type": "status", "message": "⚡ Bootstrapping Neo4j Schema (Constraints & Labels)..."}) + "\n"
        
        clear_db(graph)
        yield json.dumps({"type": "status", "message": "[*] Wiping previous Graph topology..."}) + "\n"
        
        temp_repos_root = "temp_repos"
        os.makedirs(temp_repos_root, exist_ok=True)
        
        for repo_source in KB_REPOS:
            target_path = repo_source
            
            if repo_source.startswith("http") or repo_source.startswith("git@"):
                repo_name = re.sub(r'[^a-zA-Z0-9]', '_', repo_source.split('/')[-1])
                target_path = os.path.join(temp_repos_root, repo_name)
                
                if os.path.exists(target_path):
                    yield json.dumps({"type": "status", "message": f"[*] Repository {repo_source} exists. Pulling latest..."}) + "\n"
                    subprocess.run(["git", "-C", target_path, "pull"], check=False)
                else:
                    yield json.dumps({"type": "status", "message": f"[*] Cloning repository {repo_source}..."}) + "\n"
                    subprocess.run(["git", "clone", repo_source, target_path], check=False)
            
            if os.path.exists(target_path):
                yield json.dumps({"type": "status", "message": f"[*] Parsing & Mapping logic from: {target_path}..."}) + "\n"
                load_repo_to_graph(graph, target_path)
            else:
                yield json.dumps({"type": "error", "message": f"[!] Path/Repo not found: {target_path}"}) + "\n"
                
        yield json.dumps({"type": "done", "message": "✅ Knowledge Base Synchronization Complete."}) + "\n"
    except Exception as e:
        logger.error(f"❌ KB Sync failed: {e}")
        yield json.dumps({"type": "error", "message": f"❌ Synchronization failed: {str(e)}"}) + "\n"

def sync_kb_sources():
    """Legacy wrapper for startup sync (lifespan)."""
    for _ in sync_kb_generator():
        pass

# Helper function to run a sync generator in a thread pool to avoid blocking the event loop
async def wrap_sync_generator(gen):
    loop = asyncio.get_event_loop()
    while True:
        try:
            # Shift the sync 'next(gen)' call to a thread
            res = await loop.run_in_executor(None, next, gen)
            yield res
        except StopIteration:
            break
        except Exception as e:
            yield json.dumps({"type": "error", "message": f"Stream Error: {str(e)}"}) + "\n"
            break

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Sync Knowledge Base in a background thread
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, sync_kb_sources)
    yield
    # Shutdown logic (if any) could go here

app = FastAPI(title="Agentic RAG Engine", lifespan=lifespan)

# Ensure necessary directories exist
os.makedirs("ui", exist_ok=True)
os.makedirs("temp_data", exist_ok=True)
app.mount("/static", StaticFiles(directory="ui"), name="static")

def clean_llm_json(text: str) -> str:
    """Helper to extract JSON from LLM response strings which might be wrapped in ```json ... ```"""
    text = text.strip()
    if text.startswith("```"):
        # Remove starting ```json or ```
        text = re.sub(r'^```(?:json)?\s*', '', text)
        # Remove ending ```
        text = re.sub(r'\s*```$', '', text)
    return text.strip()

@app.post("/api/refresh-kb")
async def refresh_kb():
    """Trigger a manual refresh/sync of the Knowledge Base with async-safe streaming."""
    logger.info("Manual KB Refresh requested via UI.")
    gen = sync_kb_generator()
    return StreamingResponse(wrap_sync_generator(gen), media_type="application/x-ndjson")

@app.get("/")
def serve_index():
    return FileResponse("ui/index.html")

@app.post("/api/analyze")
async def analyze_failures(file: UploadFile = File(...)):
    # Eagerly read file content into memory asynchronously to avoid blocking
    content = await file.read()
    
    def event_stream():
        # Multi-user safe: unique filename per request
        unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        temp_file_path = f"temp_data/output_{unique_id}.xml"
        
        logger.info(f"Incoming Request: File={file.filename}, TempPath={temp_file_path}")
        yield json.dumps({"type": "status", "message": f"Processing file: {file.filename}..."}) + "\n"
        
        try:
            # Write bytes from memory to disk
            with open(temp_file_path, "wb") as buffer:
                buffer.write(content)
            logger.info(f"File saved successfully: {temp_file_path}")
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {str(e)}")
            yield json.dumps({"type": "error", "message": f"Failed to save uploaded file: {str(e)}"}) + "\n"
            return
            
        try:
            logger.info("Parsing XML output...")
            yield json.dumps({"type": "status", "message": f"Parsing XML output '{file.filename}'..."}) + "\n"
            try:
                failures = parse_output_xml(temp_file_path)
            except Exception as e:
                logger.error(f"XML Parsing Error: {str(e)}")
                yield json.dumps({"type": "error", "message": f"Error parsing XML: {str(e)}"}) + "\n"
                return

            if not failures:
                logger.info("Analysis complete: All Tests Passed.")
                yield json.dumps({"type": "done", "message": "All Tests Passed!"}) + "\n"
                return

            logger.info(f"Detected {len(failures)} failed tests. Connecting to Graph/Embedding DBs...")
            yield json.dumps({"type": "status", "message": f"Found {len(failures)} failed tests. Initializing DB connections..."}) + "\n"

            try:
                robot_graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
                embedding = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
                logger.info("✓ Connected to Neo4j and Embedding engine.")
                yield json.dumps({"type": "status", "message": "✓ Connected to Neo4j Graph DB & Embeddings Model."}) + "\n"
            except Exception as e:
                logger.error(f"DB Connection Failed: {str(e)}")
                yield json.dumps({"type": "error", "message": f"Database/Embedding connection failed: {str(e)}"}) + "\n"
                return

            logger.info("Initializing Short-term Flow Memory (FAISS)...")
            yield json.dumps({"type": "status", "message": "Embedding trace logs into temporary FAISS memory..."}) + "\n"
            failure_docs = [failure_to_doc(f) for f in failures]
            temp_failure_db = FAISS.from_documents(failure_docs, embedding)

            for failure in failures:
                logger.info(f"Analyzing Failure: {failure.name}")
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
                    logger.warning(f"Metadata missing for {failure.name} in Graph DB.")
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
                        logger.info(f"Retrieved {len(past_fails)} past failure records for {failure.name}.")
                        past_str = "\n\n".join([f"Time: {pf.get('date', 'Unknown')}\nError: {pf.get('error')}\nPrevious RCA: {pf.get('rca', '')}" for pf in past_fails if pf.get('error')])
                        expected_content += f"\n\n[PAST FAILURES MEMORY]\nThe following are previous recorded failures for this exact same test case. Use them to understand if this is a recurring issue or if past fixes failed.\n\n{past_str}"

                yield json.dumps({"type": "status", "message": f"► [Test: {failure.name}] Fetching Vector Context Memory..."}) + "\n"
                search_query = f"Keyword mapping failure '{failure.failed_keyword}' yielding '{failure.failed_keyword_message}'."
                exec_results = temp_failure_db.similarity_search(search_query, k=4)
                exec_content = "\n\n---\n\n".join([f"[SIMILAR RUNTIME CRASH LOG: {doc.metadata.get('test', 'Unknown')}]\n{doc.page_content}" for doc in exec_results])

                logger.info(f"Context compiled for {failure.name}. Ready for inference.")
                yield json.dumps({"type": "status", "message": f"⚡ [Test: {failure.name}] Retrieval complete. Compiling Agent memory..."}) + "\n"
                yield json.dumps({"type": "inference", "message": f"⏳ [Test: {failure.name}] AI Agent is thinking & drafting RCA..."}) + "\n"

                prompt = f"""
================ SYSTEM PROMPT ================
You are a root cause analysis engine for Robot Framework testing. 
Analyze the failure based on the following retrieved contexts from our Vector Databases.

[EXPECTED KNOWLEDGE BASE (NEO4J)]
{expected_content}

[RUNTIME CRASH CONTEXT (FAISS MEMORY)]
{exec_content}

TASK: Analyze why '{failure.name}' broke. You must structure your output as a professional Root Cause Analysis report in Markdown. Use headers, bold text, and lists to make it readable.

Include these sections:
1. **Root Cause & Expected Behavior**
2. **Proposed Test Fixes**
3. **System Bug / Issue Analysis**
4. **Final Recommendations**
===============================================
"""
                if LLM_DEBUG:
                    logger.info(f"LLM_DEBUG is TRUE. Invoking actual LLM ({LLM_MODEL})...")
                    try:
                        llm = ChatOpenAI(
                            model=LLM_MODEL,
                            api_key=OPENROUTER_API_KEY,
                            base_url=LLM_BASE_URL,
                            temperature=LLM_TEMPERATURE,
                        )
                        response = llm.invoke(prompt)
                        rca_text = response.content
                    except Exception as e:
                        logger.error(f"LLM Invocation Failed: {str(e)}")
                        rca_text = f"AI Evaluation failed: {str(e)}"
                else:
                    logger.info("LLM_DEBUG is FALSE. Returning raw prompt for audit.")
                    rca_text = prompt
                    
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
                    logger.info(f"Analysis saved to Graph Memory for {failure.name}")
                    yield json.dumps({"type": "status", "message": f"💾 Saved LLM Analysis to Permanent Graph Memory."}) + "\n"
                except Exception as e:
                    logger.error(f"Failed to save to graph memory: {str(e)}")
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

            logger.info("Full analysis pipeline finished.")
            yield json.dumps({"type": "done", "message": "Analysis Pipeline Completed successfully!"}) + "\n"
        finally:
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"Cleaned up temp file: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Final cleanup failed for {temp_file_path}: {e}")

    # Run the sync generator in a thread pool using the wrapper
    gen = event_stream()
    return StreamingResponse(wrap_sync_generator(gen), media_type="application/x-ndjson")
