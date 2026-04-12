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
    """
    Enforce schema constraints in Neo4j to prevent "unrecognized label/property" warnings.
    This acts as a 'seed' for the database schema.
    """
    logger.info("⚡ Bootstrapping Neo4j Schema (Constraints & Labels)...")
    
    # Use Indexes instead of Existence Constraints to support Community Edition.
    # An index on a property implicitly defines the label and property in the schema.
    commands = [
        # TestCase Constraints
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TestCase) REQUIRE t.name IS UNIQUE",
        
        # Keyword Constraints
        "CREATE CONSTRAINT IF NOT EXISTS FOR (k:Keyword) REQUIRE k.name IS UNIQUE",
        
        # Seed the PastFailure schema via Indexes (Safe for Community Edition)
        "CREATE INDEX IF NOT EXISTS FOR (f:PastFailure) ON (f.timestamp)",
        "CREATE INDEX IF NOT EXISTS FOR (f:PastFailure) ON (f.error_message)",
        "CREATE INDEX IF NOT EXISTS FOR (f:PastFailure) ON (f.failed_keyword)"
    ]
    
    for cmd in commands:
        try:
            graph.query(cmd)
            logger.debug(f"Executed Schema Command: {cmd}")
        except Exception as e:
            logger.warning(f"Schema Command failed (Safe to ignore if cluster is still starting): {e}")

def init_kb(repo_path: str):
    """Parse Robot Framework test definitions and build the Neo4j Knowledge Base."""
    logger.info(f"[*] Starting Knowledge Base initialization from: {repo_path}")
    
    tests, keywords = parse_robot_repo(repo_path)
    if not tests:
        logger.error("[!] No tests found or parsed. Check your path.")
        return

    logger.info("[*] Connecting to Neo4j Graph Database...")
    try:
        graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)

        # 1. Warm up schema first
        bootstrap_schema(graph)

        logger.info("[*] Wiping previous Graph topology...")
        graph.query("MATCH (n) DETACH DELETE n")

        logger.info(f"[*] Building {len(keywords)} Custom Keyword Nodes...")
        for kw in keywords:
            graph.query(
                "MERGE (k:Keyword {name: $name}) SET k.steps = $steps, k.source = $source, k.raw_text = $raw_text",
                params={"name": kw.name, "steps": kw.steps, "source": kw.source, "raw_text": kw.raw_text}
            )

        logger.info(f"[*] Building {len(tests)} TestCase Nodes and routing internal logic paths...")
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

        logger.info("[*] Mapping recursive Keyword-to-Keyword logic flows...")
        for kw in keywords:
            for step in kw.steps:
                graph.query(
                    "MATCH (k1:Keyword {name: $parent}), (k2:Keyword {name: $child}) MERGE (k1)-[:CALLS]->(k2)",
                    params={"parent": kw.name, "child": step}
                )

        logger.info("[+] Pure Graph Knowledge Base successfully mapped into Neo4j!")
    except Exception as e:
        logger.critical(f"Critical Error building Graph: {e}")

def main():
    parser = argparse.ArgumentParser(description="Agentic Graph-RAG Engine CLI")
    parser.add_argument("--init-kb", type=str, help="Path to Robot repo to initialize Permanent Neo4j DB.")
    args = parser.parse_args()

    if args.init_kb:
        init_kb(args.init_kb)
    else:
        logger.info("Usage: python run.py --init-kb <path-to-robot-tests>")
        logger.info("       uvicorn engine.server:app --reload  (for web UI)")

if __name__ == "__main__":
    main()
