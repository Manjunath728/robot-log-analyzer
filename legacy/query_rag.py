import argparse
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default="Why did TC03 fail?", help="Question to ask the RAG system")
    args = parser.parse_args()
    
    print("Loading Embedding Model...")
    embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    out_dir = Path("data/vector_dbs")
    
    if not (out_dir / "failure_db").exists() or not (out_dir / "robot_db").exists():
        print("Vector DBs not found. Please run build_vector_dbs.py first.")
        return

    print("Loading FAISS Indices...")
    failure_db = FAISS.load_local(
        str(out_dir / "failure_db"), 
        embedding,
        allow_dangerous_deserialization=True  # Required by LangChain to load local pickle
    )
    robot_db = FAISS.load_local(
        str(out_dir / "robot_db"), 
        embedding,
        allow_dangerous_deserialization=True
    )
    
    import re
    
    print(f"\nQuerying: '{args.query}'\n")
    
    # Check if the query asks for a specific test
    match = re.search(r'(TC\d+)', args.query, re.IGNORECASE)
    search_kwargs = {"k": 3}
    if match:
        test_id = match.group(1).upper()
        print(f"[*] Detected explicit Test ID '{test_id}' in query. Applying exact Metadata Filter.")
        search_kwargs["filter"] = {"test_id": test_id}
        
    # STEP 1: Retrieve failure
    failure_results = failure_db.similarity_search(args.query, **search_kwargs)
    failure_content = "\n\n".join([doc.page_content for doc in failure_results])
    
    # STEP 2: Retrieve test definition
    robot_results = robot_db.similarity_search(args.query, **search_kwargs)
    robot_content = "\n\n".join([doc.page_content for doc in robot_results])
    
    # STEP 3: Build context
    context = f"""
================ SYSTEM PROMPT ================
You are a root cause analysis engine for Robot Framework testing. 
Analyze the failure based on the following retrieved context:

[FAILURE CONTEXT]
{failure_content}

[EXPECTED BEHAVIOR CONTEXT]
{robot_content}

QUESTION: {args.query}
[Expected output in table format] 

test-name -- error -- expected -- root-cause -- testfix needed -- bug create needed   

===============================================
"""
    print(context)
    print("\nSTEP 4: (Pass the above prompt block to your LLM backend)")

if __name__ == "__main__":
    main()
