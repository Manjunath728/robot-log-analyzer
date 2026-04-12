import json
from pathlib import Path
import re
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def extract_test_id(name: str) -> str:
    match = re.search(r'(TC\d+)', name, re.IGNORECASE)
    return match.group(1).upper() if match else ""

def robot_to_doc(t: dict) -> Document:
    name = t.get('name', '')
    tags = t.get('tags', [])
    keywords = t.get('keywords', [])
    test_id = extract_test_id(name)
    
    content = f"""
Test: {name}
Tags: {' '.join(tags)}
Keywords: {' '.join(keywords)}
"""
    return Document(
        page_content=content.strip(),
        metadata={
            "test": name,
            "test_id": test_id,
            "tags": tags
        }
    )

def failure_to_doc(f: dict) -> Document:
    test_name = f.get("test_name", "")
    hint = f.get("root_cause_hint", {})
    failure_point = hint.get("failed_keyword", "")
    failure_type = hint.get("message", "Unknown Error")
    
    expected_steps = f.get("expected", {}).get("steps", [])
    actual_steps = f.get("actual", {}).get("steps", [])
    
    logs = f.get("actual", {}).get("console_logs", [])
    logs_str = "\n".join(logs[-50:])  # Add up to the last 50 log lines
    
    content = f"""
Test: {test_name}
Failure: {failure_point}
Expected: {' -> '.join(expected_steps)}
Actual: {' -> '.join(actual_steps)}
Type: {failure_type}
Logs:
{logs_str}
"""

    return Document(
        page_content=content.strip(),
        metadata={
            "test": test_name,
            "test_id": extract_test_id(test_name),
            "type": failure_type
        }
    )

def main():
    print("Loading data...")
    tests_path = Path("data/robot_ai_out/tests.json")
    merged_path = Path("data/robot_ai_out/merged_context.json")
    
    tests_data = []
    if tests_path.exists():
        with open(tests_path, "r", encoding="utf-8") as f:
            tests_data = json.load(f)
            
    merged_data = []
    if merged_path.exists():
        with open(merged_path, "r", encoding="utf-8") as f:
            merged_data = json.load(f)
            
    # Filter failures only
    failures_data = [d for d in merged_data if d.get("status") == "FAIL"]

    print("Transforming to LangChain Documents...")
    robot_docs = [robot_to_doc(t) for t in tests_data]
    failure_docs = [failure_to_doc(f) for f in failures_data]

    print("Initializing SentenceTransformers Embedding Model (all-MiniLM-L6-v2)...")
    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    out_dir = Path("data/vector_dbs")
    out_dir.mkdir(parents=True, exist_ok=True)

    if robot_docs:
        print("Building Robot DB...")
        robot_db = FAISS.from_documents(robot_docs, embedding)
        robot_db.save_local(str(out_dir / "robot_db"))
        print(f"Saved Robot DB with {len(robot_docs)} chunks.")

    if failure_docs:
        print("Building Failure DB...")
        failure_db = FAISS.from_documents(failure_docs, embedding)
        failure_db.save_local(str(out_dir / "failure_db"))
        print(f"Saved Failure DB with {len(failure_docs)} chunks.")

    print("Vector Databases built successfully!")

if __name__ == "__main__":
    main()
