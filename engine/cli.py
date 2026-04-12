"""
CLI entrypoint for the Agentic Graph-RAG Engine.

Usage:
    python run.py --init-kb examples      # Initialize the Neo4j Knowledge Base
"""

import argparse
import os

# Suppress overly verbose warnings from huggingface / tensor components
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

from langchain_neo4j import Neo4jGraph

from engine.config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from engine.parser import parse_robot_repo


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


def main():
    parser = argparse.ArgumentParser(description="Agentic Graph-RAG Engine CLI")
    parser.add_argument("--init-kb", type=str, help="Path to Robot repo to initialize Permanent Neo4j DB.")
    args = parser.parse_args()

    if args.init_kb:
        init_kb(args.init_kb)
    else:
        print("Usage: python run.py --init-kb <path-to-robot-tests>")
        print("       uvicorn engine.server:app --reload  (for web UI)")


if __name__ == "__main__":
    main()
