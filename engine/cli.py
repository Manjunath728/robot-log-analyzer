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
from engine.logger import logger

def bootstrap_schema(graph: Neo4jGraph):
    """Enforce schema constraints in Neo4j to prevent warnings."""
    logger.info("⚡ Bootstrapping Neo4j Schema (Constraints & Labels)...")
    commands = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TestCase) REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (k:Keyword) REQUIRE k.name IS UNIQUE",
        "CREATE INDEX IF NOT EXISTS FOR (f:PastFailure) ON (f.timestamp)",
        "CREATE INDEX IF NOT EXISTS FOR (f:PastFailure) ON (f.error_message)",
        "CREATE INDEX IF NOT EXISTS FOR (f:PastFailure) ON (f.failed_keyword)"
    ]
    for cmd in commands:
        try:
            graph.query(cmd)
        except Exception as e:
            logger.warning(f"Schema Command failed: {e}")

def clear_kb_topology(graph: Neo4jGraph):
    """Wipe only the TestCases and Keywords, preserving PastFailure memory."""
    logger.info("[*] Wiping current KB topology (Tests & Keywords)...")
    graph.query("MATCH (n) WHERE n:TestCase OR n:Keyword DETACH DELETE n")

def clear_db(graph: Neo4jGraph):
    """Full Database Reset: Wipe everything including historical memory."""
    logger.info("[!] PERFORMING FULL DATABASE RESET...")
    graph.query("MATCH (n) DETACH DELETE n")

def load_repo_to_graph(graph: Neo4jGraph, repo_path: str):
    """Parse a single Robot repo and merge it into the Graph."""
    logger.info(f"[*] Loading Robot logic from: {repo_path}")
    
    tests, keywords = parse_robot_repo(repo_path)
    if not tests:
        logger.warning(f"[!] No tests found in {repo_path}. Skipping.")
        return

    logger.info(f"[*] Merging {len(keywords)} Keywords and {len(tests)} Tests...")
    
    # Merge Keywords
    for kw in keywords:
        graph.query(
            "MERGE (k:Keyword {name: $name}) SET k.steps = $steps, k.source = $source, k.raw_text = $raw_text",
            params={"name": kw.name, "steps": kw.steps, "source": kw.source, "raw_text": kw.raw_text}
        )

    # Merge Tests
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

    # Link Keywords recursively
    for kw in keywords:
        for step in kw.steps:
            graph.query(
                "MATCH (k1:Keyword {name: $parent}), (k2:Keyword {name: $child}) MERGE (k1)-[:CALLS]->(k2)",
                params={"parent": kw.name, "child": step}
            )

def init_kb(repo_path: str, full_reset: bool = False):
    """Standard CLI-based initialization."""
    try:
        graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
        bootstrap_schema(graph)
        if full_reset:
            clear_db(graph)
        else:
            clear_kb_topology(graph)
        load_repo_to_graph(graph, repo_path)
        logger.info("[+] KB successfully mapped.")
    except Exception as e:
        logger.critical(f"Critical Error building Graph: {e}")

def main():
    parser = argparse.ArgumentParser(description="Agentic Graph-RAG Engine CLI")
    parser.add_argument("--init-kb", type=str, help="Path to Robot repo to initialize Permanent Neo4j DB.")
    parser.add_argument("--full-reset", action="store_true", help="Wipe ALL data including failure history before initialization.")
    args = parser.parse_args()

    if args.init_kb:
        init_kb(args.init_kb, full_reset=args.full_reset)
    else:
        logger.info("Usage: python run.py --init-kb <path-to-robot-tests> [--full-reset]")

if __name__ == "__main__":
    main()
