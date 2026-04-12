"""
CLI Entrypoint — thin wrapper around engine.cli

Usage:
    python run.py --init-kb examples    # Build the Neo4j Knowledge Base
    python run.py                        # Interactive analysis loop
"""

from engine.cli import main

if __name__ == "__main__":
    main()
