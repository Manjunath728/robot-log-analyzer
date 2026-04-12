"""
CLI entrypoint for the Agentic Graph-RAG Engine.

Usage:
    python run.py --init-kb examples      # Initialize the Neo4j Knowledge Base
    python run.py                          # Start the interactive analysis loop
"""

import argparse
import os
from pathlib import Path

# Suppress overly verbose warnings from huggingface / tensor components
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from langchain_community.vectorstores import FAISS
from langchain_neo4j import Neo4jGraph
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from engine.config import (
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD,
    OPENROUTER_API_KEY, LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE,
    EMBEDDING_MODEL,
)
from engine.parser import parse_robot_repo, parse_output_xml
from engine.helpers import extract_test_id, failure_to_doc


def init_kb(repo_path: str):
    """Parse Robot Framework test definitions and build the Neo4j Knowledge Base."""
    print(f"[*] Parsing Robot test definitions from {repo_path}...")
    tests, keywords = parse_robot_repo(repo_path)
    if not tests:
        print("[!] No tests found or parsed.")
        return

    print("[*] Connecting to Neo4j Graph Database...")
    try:
        graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)

        print("[*] Wiping previous Graph topology...")
        graph.query("MATCH (n) DETACH DELETE n")

        print(f"[*] Building {len(keywords)} Custom Keyword Nodes...")
        for kw in keywords:
            graph.query(
                "MERGE (k:Keyword {name: $name}) SET k.steps = $steps, k.source = $source, k.raw_text = $raw_text",
                params={"name": kw.name, "steps": kw.steps, "source": kw.source, "raw_text": kw.raw_text}
            )

        print(f"[*] Building {len(tests)} TestCase Nodes and routing internal logic paths...")
        for t in tests:
            graph.query(
                "MERGE (tc:TestCase {name: $name}) SET tc.steps = $steps, tc.tags = $tags, tc.source = $source",
                params={"name": t.name, "steps": t.steps, "tags": t.tags, "source": t.source}
            )
            for step in t.steps:
                graph.query(
                    "MATCH (tc:TestCase {name: $tc}), (k:Keyword {name: $step}) MERGE (tc)-[:CALLS]->(k)",
                    params={"tc": t.name, "step": step}
                )

        print("[*] Mapping recursive Keyword-to-Keyword logic flows...")
        for kw in keywords:
            for step in kw.steps:
                graph.query(
                    "MATCH (k1:Keyword {name: $parent}), (k2:Keyword {name: $child}) MERGE (k1)-[:CALLS]->(k2)",
                    params={"parent": kw.name, "child": step}
                )

        print("[+] Pure Graph Knowledge Base successfully mapped into Neo4j!")
    except Exception as e:
        print(f"[!] Error building Graph: {e}")
        print("    Did you start `docker-compose up -d`?")


def run_interactive_loop():
    """Start the interactive CLI analysis loop."""
    print("[*] Initializing OpenRouter Free AI Runtime...")
    if not OPENROUTER_API_KEY:
        print("[!] ERROR: OPENROUTER_API_KEY is not set in .env!")
        print("    Please add your key to .env and restart.")
        return

    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=LLM_BASE_URL,
        temperature=LLM_TEMPERATURE,
    )

    print(f"[*] Loading Deep Retriever Embedding model ({EMBEDDING_MODEL})...")
    embedding = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    print("[*] Securing native Graph Traversal Driver for Neo4j...")
    try:
        robot_graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
    except Exception as e:
        print(f"[!] Critical Error connecting to Neo4j Graph Database: {e}")
        print("    Make sure Docker is running and you have initialized the KB using --init-kb.")
        return

    print("\n" + "=" * 50)
    print(" Agentic Neo4j RAG System Ready!")
    print("=" * 50)

    while True:
        xml_path = input("\nEnter path to output.xml (or 'q' to quit): ").strip()
        if xml_path.lower() == 'q':
            break

        if not Path(xml_path).exists():
            print(f"[!] File '{xml_path}' not found.")
            continue

        print(f"[*] Traversing and Parsing output.xml: {xml_path}")
        try:
            failures = parse_output_xml(xml_path)
        except Exception as e:
            print(f"[!] Error parsing XML: {e}")
            continue

        if not failures:
            print("[+] No failures detected! All tests passed.")
            continue

        print(f"[*] Found {len(failures)} failed tests. Spinning up temporary FAISS Memory Vector DB...")
        failure_docs = [failure_to_doc(f) for f in failures]
        temp_failure_db = FAISS.from_documents(failure_docs, embedding)

        print("\n" + "*" * 50)
        print(" AUTO-AGENTIC PROMPT GENERATION INITIATED")
        print("*" * 50)

        for idx, failure in enumerate(failures):
            print(f"\n################ FAILURE {idx+1}/{len(failures)}: {failure.name} ################")

            cypher_query = """
            MATCH (t:TestCase {name: $test_name})
            OPTIONAL MATCH (t)-[:CALLS*]->(k:Keyword)
            RETURN t.name AS test_name, t.tags AS test_tags, t.steps AS test_steps, 
                   collect(DISTINCT {name: k.name, steps: k.steps}) AS nested_keywords
            """
            graph_results = robot_graph.query(cypher_query, params={"test_name": failure.name})

            if not graph_results:
                expected_content = f"Test Case '{failure.name}' not found in Static Neo4j Knowledge Graph."
            else:
                data = graph_results[0]
                expected_content = f"Test: {data['test_name']}\nTags: {', '.join(data.get('test_tags', []))}\nExpected Flow: {' -> '.join(data.get('test_steps', []))}"
                kws = data.get('nested_keywords', [])
                if kws and any(k.get('name') for k in kws):
                    glossary_str = "\n".join([f"- {k['name']}: {' -> '.join(k.get('steps', []))}" for k in kws if k.get('name')])
                    expected_content += f"\n\n[KEYWORD GLOSSARY]\n{glossary_str}"

            search_query = f"Test '{failure.name}' broke during '{failure.failed_keyword}' yielding '{failure.failed_keyword_message}'."
            exec_results = temp_failure_db.similarity_search(search_query, k=2, filter=dict(test=failure.name))
            exec_content = "\n\n".join([doc.page_content for doc in exec_results])

            prompt = f"""
================ SYSTEM PROMPT ================
You are a root cause analysis engine for Robot Framework testing. 
Analyze the failure based on the following retrieved contexts from our Vector Databases.

[EXPECTED KNOWLEDGE BASE (NEO4J)]
{expected_content}

[RUNTIME CRASH CONTEXT (FAISS MEMORY)]
{exec_content}

TASK: Identify exactly why '{failure.name}' broke and suggest a fix.
===============================================
"""
            print("[➤] Compiling Context...")
            try:
                print("\n" + "=" * 60)
                print(f" ROOT CAUSE ANALYSIS: {failure.name}")
                print("=" * 60)
                print("printing prompt instead of response")
                print(prompt)
                print("=" * 60 + "\n")
            except Exception as e:
                print(f"[!] Evaluation request failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Agentic Graph-RAG Engine CLI")
    parser.add_argument("--init-kb", type=str, help="Path to Robot repo to initialize Permanent Neo4j DB.")
    args = parser.parse_args()

    if args.init_kb:
        init_kb(args.init_kb)
    else:
        run_interactive_loop()


if __name__ == "__main__":
    main()
