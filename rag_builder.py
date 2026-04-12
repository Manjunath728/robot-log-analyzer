import argparse
import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple


def safe_get(d: Dict[str, Any], key: str, default: Any = "") -> Any:
    return d.get(key, default)


def format_test_doc(test_dict: Dict[str, Any]) -> Tuple[str, str]:
    """Pure function mapping a test dictionary to its RAG Markdown document."""
    name = safe_get(test_dict, "name")
    tags = ", ".join(safe_get(test_dict, "tags", []))
    source = safe_get(test_dict, "source")
    lineno = safe_get(test_dict, "lineno", 0)
    steps = safe_get(test_dict, "steps", [])
    
    # Using functional mapping to build steps string
    steps_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
    
    doc = f"""# Test Case: {name}
**Tags:** {tags}
**Source:** {source} (Line {lineno})

## Execution Steps (Keywords)
{steps_str}
"""
    # Safe filename
    filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', name) + ".md"
    return filename, doc


def format_failure_doc(merged_dict: Dict[str, Any]) -> Tuple[str, str]:
    """Pure function mapping a merged failure dictionary to its RAG failure report."""
    name = safe_get(merged_dict, "test_name")
    status = safe_get(merged_dict, "status")
    source = safe_get(merged_dict, "source")
    
    expected = safe_get(merged_dict, "expected", {})
    tags = ", ".join(safe_get(expected, "tags", []))
    expected_steps = safe_get(expected, "steps", [])
    
    actual = safe_get(merged_dict, "actual", {})
    actual_steps = safe_get(actual, "steps", [])
    
    hint = safe_get(merged_dict, "root_cause_hint", {})
    failed_kw = safe_get(hint, "failed_keyword")
    error_msg = safe_get(hint, "message")
    
    expected_steps_str = "\n".join(f"- {step}" for step in expected_steps)
    actual_steps_str = "\n".join(
        f"{i+1}. {step}{' (FAILED)' if step == failed_kw else ''}" 
        for i, step in enumerate(actual_steps)
    )

    doc = f"""# Failure Report: {name}
**Status:** {status}

## Expected Definition
**Tags:** {tags}
**Original Steps (Flat):**
{expected_steps_str}

## Runtime Failure Context
**Failed Keyword:** {failed_kw}
**Source:** {source}
**Error Cause:** 
```text
{error_msg}
```

**Execution Path:** 
{actual_steps_str}
"""
    filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', name) + "_failure.md"
    return filename, doc


def load_json(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_doc(outdir: Path, doc_tuple: Tuple[str, str]) -> None:
    filename, content = doc_tuple
    outpath = outdir / filename
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_text(content, encoding="utf-8")


def pipeline(
    data_list: List[Dict[str, Any]], 
    formatter: Callable[[Dict[str, Any]], Tuple[str, str]], 
    outdir: Path
) -> None:
    """Pure functional pipeline: map -> effect"""
    docs = map(formatter, data_list)
    # Side effect boundary
    for doc in docs:
        write_doc(outdir, doc)


def run_pipeline(tests_path: str, merged_path: str, out_path: str) -> None:
    tests_file = Path(tests_path)
    merged_file = Path(merged_path)
    out_dir = Path(out_path)
    
    test_out = out_dir / "tests"
    failure_out = out_dir / "failures"

    # Functional composition boundaries
    tests_data = load_json(tests_file)
    merged_data = load_json(merged_file)

    # Transform and write
    pipeline(tests_data, format_test_doc, test_out)
    
    # We only want to generate failure docs for tests that actually failed.
    # The merged_context.json only has failures if we built it that way.
    # Filter functionally just in case.
    failures_data = filter(lambda x: x.get("status") == "FAIL", merged_data)
    pipeline(list(failures_data), format_failure_doc, failure_out)

    print(f"Generated RAG Test Documents in: {test_out.resolve()}")
    print(f"Generated RAG Failure Documents in: {failure_out.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate RAG-optimized Markdown documents from Robot output.")
    parser.add_argument("--tests", required=True, help="Path to tests.json")
    parser.add_argument("--merged", required=True, help="Path to merged_context.json")
    parser.add_argument("--outdir", default="data/rag_docs", help="Directory to output markdown files")
    args = parser.parse_args()

    run_pipeline(args.tests, args.merged, args.outdir)
