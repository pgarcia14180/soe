#!/usr/bin/env python3
"""
Documentation Builder

Renders Jinja2 templates from docs_src/ to docs/.
Extracts code snippets from test files to ensure documentation matches reality.

Usage:
    python scripts/build_docs.py

Output:
    docs/guide_01_basics.md
    docs/guide_02_llm.md
    ...etc
"""

import os
import re
import ast
import shutil
from pathlib import Path
from typing import Optional

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("Error: jinja2 is required. Install with: pip install jinja2")
    exit(1)


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_SRC = PROJECT_ROOT / "docs_src"
DOCS_OUT = PROJECT_ROOT / "soe" / "docs"
TESTS_ROOT = PROJECT_ROOT / "tests"


def extract_yaml(file_path: str, variable_name: str) -> str:
    """
    Extract a YAML string from a Python file variable assignment.

    Args:
        file_path: Relative path from project root (e.g., 'tests/test_cases/workflows/guide_01_basics.py')
        variable_name: Name of the variable containing the YAML string

    Returns:
        The YAML content (without triple quotes), with Jinja2 syntax escaped
    """
    full_path = PROJECT_ROOT / file_path

    if not full_path.exists():
        return f"# ERROR: File not found: {file_path}"

    content = full_path.read_text()

    # Parse the Python file
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return f"# ERROR: Syntax error in {file_path}: {e}"

    # Find the variable assignment
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable_name:
                    # Get the value
                    if isinstance(node.value, ast.Constant):
                        value = node.value.value
                        if isinstance(value, str):
                            # Strip leading/trailing whitespace but preserve internal structure
                            result = value.strip()
                            # Escape Jinja2 braces so they render literally
                            # Use HTML-like entities that we'll convert back
                            result = result.replace("{{", "&#123;&#123;")
                            result = result.replace("}}", "&#125;&#125;")
                            result = result.replace("{%", "&#123;%")
                            result = result.replace("%}", "%&#125;")
                            return result

    return f"# ERROR: Variable '{variable_name}' not found in {file_path}"


def include_file(file_path: str, lines: Optional[str] = None) -> str:
    """
    Include content from a file.

    Args:
        file_path: Relative path from project root
        lines: Optional line range like '10-20'

    Returns:
        File content (optionally sliced)
    """
    full_path = PROJECT_ROOT / file_path

    if not full_path.exists():
        return f"# ERROR: File not found: {file_path}"

    content = full_path.read_text()
    all_lines = content.splitlines()

    if lines:
        match = re.match(r"(\d+)-(\d+)", lines)
        if match:
            start = int(match.group(1)) - 1  # 1-indexed to 0-indexed
            end = int(match.group(2))
            all_lines = all_lines[start:end]

    return "\n".join(all_lines)


def extract_test(file_path: str, test_name: str) -> str:
    """
    Extract a test function body from a Python file.

    Args:
        file_path: Relative path from project root
        test_name: Name of the test function

    Returns:
        The test function body (dedented)
    """
    full_path = PROJECT_ROOT / file_path

    if not full_path.exists():
        return f"# ERROR: File not found: {file_path}"

    content = full_path.read_text()

    # Simple regex extraction - find function and get its body
    pattern = rf"def {test_name}\([^)]*\):\s*\n((?:[ \t]+.+\n?)+)"
    match = re.search(pattern, content)

    if match:
        body = match.group(1)
        # Dedent by finding minimum indentation
        lines = body.splitlines()
        non_empty = [line for line in lines if line.strip()]
        if non_empty:
            min_indent = min(len(line) - len(line.lstrip()) for line in non_empty)
            dedented = [line[min_indent:] if len(line) >= min_indent else line for line in lines]
            return "\n".join(dedented).rstrip()

    return f"# ERROR: Test '{test_name}' not found in {file_path}"


def build_docs():
    """
    Build all documentation from Jinja2 templates.
    """
    # Clean output directory for a fresh build
    if DOCS_OUT.exists():
        shutil.rmtree(DOCS_OUT)
        print(f"Cleaned {DOCS_OUT}/")

    # Create output directory
    DOCS_OUT.mkdir(parents=True, exist_ok=True)

    # Setup Jinja environment
    env = Environment(
        loader=FileSystemLoader(str(DOCS_SRC)),
        keep_trailing_newline=True,
    )

    # Register custom functions
    env.globals["extract_yaml"] = extract_yaml
    env.globals["include_file"] = include_file
    env.globals["extract_test"] = extract_test

    # Find all .j2 templates (including subdirectories)
    templates = list(DOCS_SRC.glob("**/*.md.j2"))

    if not templates:
        print("No templates found in docs_src/")
        return

    print(f"Building documentation from {len(templates)} templates...")

    for template_path in sorted(templates):
        # Get relative path from DOCS_SRC
        relative_path = template_path.relative_to(DOCS_SRC)
        template_name = str(relative_path)
        output_name = template_name.replace(".j2", "")
        output_path = DOCS_OUT / output_name

        # Create subdirectories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            template = env.get_template(template_name)
            rendered = template.render()

            output_path.write_text(rendered)
            print(f"  ✓ {output_name}")

        except Exception as e:
            print(f"  ✗ {output_name}: {e}")

    print(f"\nDocumentation built to {DOCS_OUT}/")

    # Build the index
    build_index()


def build_index():
    """
    Builds a Python index of the documentation for the soe_explore_docs tool.
    Scans docs/ for Markdown files, extracts sections and tags.
    """
    print("\nBuilding documentation index...")

    index_data = {
        "items": {},  # path -> metadata
        "tags": {},   # tag -> list of paths
        "root_children": [] # list of top-level paths
    }

    # Directories to scan
    scan_dirs = [DOCS_OUT]

    for root_dir in scan_dirs:
        if not root_dir.exists():
            continue

        root_name = root_dir.name

        # Add root dir to children
        index_data["root_children"].append(root_name + "/")
        index_data["items"][root_name + "/"] = {
            "type": "dir",
            "children": [],
            "path": root_name + "/"
        }

        for path in sorted(root_dir.rglob("*.md")):
            rel_path = path.relative_to(PROJECT_ROOT)
            str_path = str(rel_path)

            # Add file to parent dir's children
            parent_dir = str(path.parent.relative_to(PROJECT_ROOT))
            if parent_dir == ".":
                parent_path = root_name + "/"
            else:
                parent_path = parent_dir + "/"

            # Ensure parent dirs exist in index
            parts = parent_path.strip("/").split("/")
            current_build_path = ""
            for i, part in enumerate(parts):
                prev_path = current_build_path
                current_build_path += part + "/"

                if current_build_path not in index_data["items"]:
                    index_data["items"][current_build_path] = {
                        "type": "dir",
                        "children": [],
                        "path": current_build_path
                    }
                    # Add to parent
                    if i == 0:
                        # It's a top level dir (like docs/) - already handled or subfolder
                        pass
                    else:
                         if prev_path in index_data["items"] and current_build_path not in index_data["items"][prev_path]["children"]:
                            index_data["items"][prev_path]["children"].append(current_build_path)

            # Add file to its parent
            if parent_path in index_data["items"] and str_path not in index_data["items"][parent_path]["children"]:
                index_data["items"][parent_path]["children"].append(str_path)

            # Parse File
            file_meta = parse_markdown_file(path, str_path)
            index_data["items"][str_path] = file_meta

            # STRIP FRONTMATTER from DOCS_OUT files
            # If we found frontmatter, we should remove it from the file on disk
            # so it doesn't appear in the final docs.
            if root_dir == DOCS_OUT and file_meta.get("frontmatter_end_offset"):
                offset = file_meta["frontmatter_end_offset"]
                original_content = path.read_text()
                # +3 for the closing ---
                # But wait, parse_markdown_file logic for end_fm is content.find("---", 3)
                # So end_fm is the index of the start of the closing ---
                # We want to strip up to end_fm + 3 + newline

                # Let's rely on what parse_markdown_file returns
                # It returns frontmatter_end_offset which is the index of the closing ---

                # Actually, let's just re-read and strip carefully
                if original_content.startswith("---"):
                    end_fm = original_content.find("---", 3)
                    if end_fm != -1:
                        # Strip including the closing --- and following newline
                        stripped_content = original_content[end_fm+3:].lstrip()
                        path.write_text(stripped_content)

            # Add sections to items
            for section in file_meta.get("sections", []):
                sec_path = section["path"]
                index_data["items"][sec_path] = section

                # Add tags
                for tag in section.get("tags", []):
                    if tag not in index_data["tags"]:
                        index_data["tags"][tag] = []
                    if sec_path not in index_data["tags"][tag]:
                        index_data["tags"][tag].append(sec_path)

            # Add file tags
            for tag in file_meta.get("tags", []):
                if tag not in index_data["tags"]:
                    index_data["tags"][tag] = []
                if str_path not in index_data["tags"][tag]:
                    index_data["tags"][tag].append(str_path)

    # Write to soe/docs_index.py
    output_file = PROJECT_ROOT / "soe" / "docs_index.py"
    with open(output_file, "w") as f:
        f.write("# Auto-generated documentation index. Do not edit manually.\n")
        f.write(f"DOCS_INDEX = {repr(index_data)}\n")

    print(f"Index written to {output_file}")


def generate_tags(rel_path: str, content: str) -> list:
    """
    Generates tags based on file path and content keywords.
    """
    tags = set()
    path_lower = rel_path.lower()
    content_lower = content.lower()

    # Map filename patterns to tags
    patterns = {
        "getting_started": ["getting-started", "setup", "installation"],
        "basics": ["basics", "concepts"],
        "tool": ["tools", "plugins", "extensions"],
        "llm": ["llm", "models", "configuration", "ai"],
        "router": ["router", "flow-control", "logic", "branching"],
        "patterns": ["patterns", "architecture", "best-practices"],
        "agent": ["agent", "autonomous", "loop"],
        "schema": ["schema", "validation", "types", "data-structure"],
        "identity": ["identity", "security", "permissions", "auth"],
        "child": ["sub-orchestration", "child-workflows", "nesting"],
        "ecosystem": ["ecosystem", "integrations", "community"],
        "infrastructure": ["infrastructure", "deployment", "scaling", "ops"],
        "coding_principles": ["coding-principles", "standards", "best-practices"],
        "architecture": ["architecture", "design", "system"],
        "testing": ["testing", "qa", "validation"],
        "marketing": ["marketing", "strategy"],
        "monetization": ["monetization", "business"],
        "assessment": ["assessment", "evaluation", "analysis"],
        "proposal": ["proposal", "rfc"],
        "guide": ["guide", "tutorial"],
    }

    for pattern, associated_tags in patterns.items():
        if pattern in path_lower:
            tags.update(associated_tags)

    # Content-based keywords (simple presence check)
    keywords = {
        "python": "python",
        "javascript": "javascript",
        "docker": "docker",
        "kubernetes": "kubernetes",
        "api": "api",
        "rest": "rest-api",
        "async": "async",
        "workflow": "workflow",
        "orchestration": "orchestration",
        "event": "event-driven",
        "signal": "signals",
        "state": "state-management",
        "context": "context",
        "memory": "memory",
        "history": "history",
        "telemetry": "telemetry",
        "logging": "logging",
        "debugging": "debugging",
        "error": "error-handling",
        "retry": "retries",
        "timeout": "timeouts",
        "jinja": "jinja2",
        "template": "templating",
    }

    for keyword, tag in keywords.items():
        # Check if keyword appears significantly (e.g. more than once or in headers)
        # For now, simple existence is enough for broad tagging
        if keyword in content_lower:
            tags.add(tag)

    return list(tags)


def parse_markdown_file(file_path: Path, rel_path: str) -> dict:
    """
    Parses a markdown file to extract sections and metadata.
    """
    content = file_path.read_text()
    lines = content.splitlines()

    meta = {
        "type": "file",
        "path": rel_path,
        "children": [], # Sections
        "tags": [],
        "sections": [], # Flat list of section objects to add to index
        "frontmatter_end_offset": None
    }

    # Frontmatter extraction
    if content.startswith("---"):
        try:
            end_fm = content.find("---", 3)
            if end_fm != -1:
                meta["frontmatter_end_offset"] = end_fm
                fm_text = content[3:end_fm]
                # Simple YAML parsing for tags
                for line in fm_text.splitlines():
                    if line.strip().startswith("tags:"):
                        tags_raw = line.split(":", 1)[1].strip()
                        # Handle [tag1, tag2] or tag1, tag2
                        tags_raw = tags_raw.strip("[]")
                        meta["tags"] = [t.strip() for t in tags_raw.split(",") if t.strip()]
        except Exception:
            pass # Ignore frontmatter errors

    # Programmatic Tagging (Heuristic)
    generated_tags = generate_tags(rel_path, content)
    for t in generated_tags:
        if t not in meta["tags"]:
            meta["tags"].append(t)

    # Section extraction
    current_section = None
    section_stack = [] # Stack of (level, section_dict)

    for i, line in enumerate(lines):
        # Match headers
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()

            # Create section path
            # We use a simplified path: file.md/Section Name
            # Note: This doesn't handle duplicate section names perfectly, but good enough for now
            section_path = f"{rel_path}/{title}"

            section = {
                "type": "section",
                "path": section_path,
                "file_path": rel_path,
                "start_line": i + 1, # 1-based
                "end_line": -1, # Will be set later
                "children": [],
                "tags": meta["tags"], # Inherit file tags
                "level": level
            }

            # Close previous sections
            while section_stack and section_stack[-1][0] >= level:
                closed_level, closed_sec = section_stack.pop()
                closed_sec["end_line"] = i # End at current header line

            # Add to parent
            if section_stack:
                parent = section_stack[-1][1]
                parent["children"].append(section_path)
            else:
                # Top level section in file
                meta["children"].append(section_path)

            section_stack.append((level, section))
            meta["sections"].append(section)

    # Close remaining sections
    file_end = len(lines)
    while section_stack:
        _, closed_sec = section_stack.pop()
        closed_sec["end_line"] = file_end

    return meta


if __name__ == "__main__":
    build_docs()
