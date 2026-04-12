from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Tuple

# Robot Framework imports with fallbacks for version differences.
try:
    from robot.api import TestSuiteBuilder, ExecutionResult
except Exception:  # pragma: no cover
    from robot.running.builder import TestSuiteBuilder  # type: ignore
    from robot.api import ExecutionResult  # type: ignore


@dataclass
class RobotTest:
    name: str
    source: str = ""
    lineno: int = 0
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    console_logs: List[str] = field(default_factory=list)

@dataclass
class RobotKeyword:
    name: str
    source: str = ""
    raw_text: str = ""
    steps: List[str] = field(default_factory=list)


@dataclass
class FailedTest:
    name: str
    source: str = ""
    status: str = "FAIL"
    message: str = ""
    failed_keyword: str = ""
    failed_keyword_message: str = ""
    tags: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    console_logs: List[str] = field(default_factory=list)


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        item = _safe_str(item)
        if not item:
            continue
        key = item.casefold()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _iter_children(obj: Any, attr_name: str) -> List[Any]:
    children = getattr(obj, attr_name, None)
    if not children:
        return []
    try:
        return list(children)
    except TypeError:
        return []


def _walk_tests(suite: Any) -> Iterable[Any]:
    """
    Recursively yield test cases from a Robot suite object.
    """
    for test in _iter_children(suite, "tests"):
        yield test

    for child_suite in _iter_children(suite, "suites"):
        yield from _walk_tests(child_suite)




def _keyword_name(item: Any) -> str:
    node_type = getattr(item, "type", None)
    if node_type and node_type not in ("KEYWORD", "SETUP", "TEARDOWN"):
        return _safe_str(node_type)

    for attr in ("name", "kwname", "keyword", "type"):
        value = getattr(item, attr, None)
        if value:
            return _safe_str(value)
    return _safe_str(item)


def _extract_immediate_steps(node: Any) -> List[str]:
    steps: List[str] = []
    for item in _iter_children(node, "body"):
        item_name = _keyword_name(item)
        if item_name:
            steps.append(item_name)
        # Capture nested control structures naturally present in the node
        elif hasattr(item, "body"):
            steps.extend(_extract_immediate_steps(item))

    return _dedupe_preserve_order(steps)


def _extract_logs_from_node(node: Any) -> List[str]:
    logs: List[str] = []
    for item in _iter_children(node, "body"):
        # Check if it's a Message node (has level and message properties)
        if hasattr(item, "level") and hasattr(item, "message"):
            msg = _safe_str(getattr(item, "message", ""))
            lvl = _safe_str(getattr(item, "level", "INFO"))
            if msg:
                logs.append(f"[{lvl}] {msg}")
        # Recurse for deeper logs
        if hasattr(item, "body"):
            logs.extend(_extract_logs_from_node(item))
    return logs


def _extract_source_block(source_path: str, start_line: int) -> str:
    if not source_path or start_line < 1:
        return ""
    try:
        with open(source_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        idx = start_line - 1
        block = [lines[idx].rstrip()]
        idx += 1
        
        while idx < len(lines):
            line = lines[idx]
            stripped = line.strip()
            if stripped == "" or stripped.startswith("#"):
                block.append(line.rstrip())
                idx += 1
                continue
            if not (line.startswith(" ") or line.startswith("\t")):
                break
            block.append(line.rstrip())
            idx += 1
            
        return "\n".join(block).strip()
    except Exception:
        pass
    return ""


def parse_robot_repo(repo_path: str) -> Tuple[List[RobotTest], List[RobotKeyword]]:
    repo = Path(repo_path)
    if not repo.exists():
        raise FileNotFoundError(f"Repo path not found: {repo}")

    # Build suites for tests using the standard builder
    suite = TestSuiteBuilder().build(str(repo))
    
    keywords: List[RobotKeyword] = []
    kw_seen = set()

    # To check completely recursively, manually scan all files so we don't miss Fragment resource files
    try:
        from robot.api import get_model
        
        def walk_ast_steps(node: Any) -> List[str]:
            res: List[str] = []
            for c in getattr(node, 'body', []):
                tname = type(c).__name__
                if tname == "KeywordCall":
                    kcmd = getattr(c, 'keyword', '')
                    if kcmd:
                        res.append(str(kcmd))
                elif hasattr(c, 'body'):
                    res.extend(walk_ast_steps(c))
            return res

        for p in repo.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in (".robot", ".resource"):
                continue
            try:
                model = get_model(str(p))
                for section in getattr(model, 'sections', []):
                    if type(section).__name__ == "KeywordSection":
                        for block in getattr(section, 'body', []):
                            if type(block).__name__ == "Keyword":
                                n = _safe_str(getattr(block, 'name', ''))
                                if not n or n.casefold() in kw_seen:
                                    continue
                                kw_seen.add(n.casefold())
                                
                                src = str(p)
                                lineno = int(getattr(block, 'lineno', -1))
                                
                                steps = walk_ast_steps(block)
                                steps = _dedupe_preserve_order(steps)
                                raw_text = _extract_source_block(src, lineno)
                                
                                keywords.append(RobotKeyword(name=n, source=src, raw_text=raw_text, steps=steps))
            except Exception:
                pass
    except ImportError:
        # Fallback to the old method if get_model is unavailable
        def _gather_kws(s: Any):
            if hasattr(s, "resource") and hasattr(s.resource, "keywords"):
                for kw in s.resource.keywords:
                    n = _safe_str(getattr(kw, "name", ""))
                    src = _safe_str(getattr(kw, "source", ""))
                    lineno = int(getattr(kw, "lineno", -1))
                    if n and n.casefold() not in kw_seen:
                        kw_seen.add(n.casefold())
                        steps = _extract_immediate_steps(kw)
                        raw_text = _extract_source_block(src, lineno)
                        keywords.append(RobotKeyword(name=n, source=src, raw_text=raw_text, steps=steps))
            for child in getattr(s, "suites", []):
                _gather_kws(child)
        _gather_kws(suite)

    tests: List[RobotTest] = []
    seen = set()

    for test in _walk_tests(suite):
        name = _safe_str(getattr(test, "name", ""))
        source = _safe_str(getattr(test, "source", ""))
        lineno = int(getattr(test, "lineno", 0) or 0)
        tags = [str(t) for t in getattr(test, "tags", [])] if getattr(test, "tags", None) else []
        tags = _dedupe_preserve_order(tags)

        # Retrieve mapped explicit steps
        steps = _extract_immediate_steps(test)
        kw_dedupe = _dedupe_preserve_order(steps)

        key = (name.casefold(), source.casefold(), lineno)
        if key in seen:
            continue
        seen.add(key)

        tests.append(
            RobotTest(
                name=name,
                source=source,
                lineno=lineno,
                tags=tags,
                keywords=kw_dedupe,
                steps=steps,
            )
        )

    return tests, keywords


def _first_nonempty(*values: Any) -> str:
    for value in values:
        text = _safe_str(value)
        if text:
            return text
    return ""


def _find_failed_keyword(node: Any) -> Tuple[str, str]:
    """
    Find the first failed keyword in a test execution node.
    Returns (failed_keyword_name, failed_keyword_message).
    """
    for item in _iter_children(node, "body"):
        status = _safe_str(getattr(item, "status", "")).upper()
        if status == "FAIL":
            kw_name = _keyword_name(item)
            kw_msg = _first_nonempty(
                getattr(item, "message", None),
                getattr(item, "error", None),
            )
            if kw_name:
                return kw_name, kw_msg

        if hasattr(item, "body"):
            nested_name, nested_msg = _find_failed_keyword(item)
            if nested_name:
                return nested_name, nested_msg

    return "", ""


def parse_output_xml(output_xml_path: str) -> List[FailedTest]:
    xml_path = Path(output_xml_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"output.xml not found: {xml_path}")

    result = ExecutionResult(str(xml_path))
    root_suite = getattr(result, "suite", result)

    failures: List[FailedTest] = []
    seen = set()

    for test in _walk_tests(root_suite):
        status = _safe_str(getattr(test, "status", "")).upper()
        if status != "FAIL":
            continue

        name = _safe_str(getattr(test, "name", ""))
        source = _safe_str(getattr(test, "source", ""))
        message = _first_nonempty(getattr(test, "message", None))

        failed_kw, failed_kw_msg = _find_failed_keyword(test)

        tags = [str(t) for t in getattr(test, "tags", [])] if getattr(test, "tags", None) else []
        tags = _dedupe_preserve_order(tags)
        steps = _extract_immediate_steps(test)
        console_logs = _extract_logs_from_node(test)

        key = (name.casefold(), source.casefold())
        if key in seen:
            continue
        seen.add(key)

        failures.append(
            FailedTest(
                name=name,
                source=source,
                status=status,
                message=message,
                failed_keyword=failed_kw,
                failed_keyword_message=failed_kw_msg,
                tags=tags,
                steps=steps,
                console_logs=console_logs,
            )
        )

    return failures
