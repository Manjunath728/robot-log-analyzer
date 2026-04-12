"""
Shared helper functions for document transformation.
Used by the web server to create LangChain Documents
from parsed Robot Framework data structures.
"""

from dataclasses import asdict

from langchain_core.documents import Document


def failure_to_doc(f_obj) -> Document:
    """Convert a FailedTest dataclass into a LangChain Document for vector storage."""
    f = asdict(f_obj)
    test_name = f.get("name", "")
    failure_point = f.get("failed_keyword", "")
    failure_type = f.get("failed_keyword_message", "")

    actual_steps = f.get("steps", [])
    logs = f.get("console_logs", [])
    logs_str = "\n".join(logs[-50:])

    content = f"""
Test: {test_name}
Failure: {failure_point}
Actual Steps: {' -> '.join(actual_steps)}
Type: {failure_type}
Logs:
{logs_str}
"""
    return Document(
        page_content=content.strip(),
        metadata={
            "test": test_name,
            "type": failure_type,
        }
    )
