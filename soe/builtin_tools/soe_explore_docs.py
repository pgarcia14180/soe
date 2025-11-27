from typing import Literal, Optional, List, Dict, Any, Callable
from pathlib import Path
import os

from soe.docs_index import DOCS_INDEX

# Get the SOE package root directory (where docs/ lives)
# This goes from soe/builtin_tools/soe_explore_docs.py → soe/builtin_tools → soe/soe → soe/
SOE_ROOT = Path(__file__).resolve().parent.parent.parent


def create_soe_explore_docs_tool(
    execution_id: str = None,
    backends = None,
    tools_registry: dict = None,
) -> Callable:
    """
    Factory for the soe_explore_docs tool.

    Args:
        execution_id: ID to access workflow data via backends (unused by this tool)
        backends: Backend services (unused by this tool)
        tools_registry: Optional registry of available tools (unused by this tool)

    Returns:
        Configured soe_explore_docs function
    """
    return soe_explore_docs


def soe_explore_docs(
    path: str,
    action: Literal["list", "read", "search", "tree", "get_tags"],
    query: Optional[str] = None,
    tag: Optional[str] = None
) -> str:
    """
    Explore SOE documentation using a file-system-like interface.

    This tool lets you navigate and read the SOE documentation hierarchy.
    Start with action='list' at path='/' to see available docs.

    Args:
        path: Path to explore. Use '/' for root, 'docs/guide_01_basics.md' for a file,
              or 'docs/guide_01_basics.md/Section Title' for a specific section.
        action: What to do at the path:
            - 'list': Show children (files in a dir, sections in a file)
            - 'read': Get the content of a file or section
            - 'tree': Show recursive structure from this path
            - 'search': Find docs matching query/tag (path ignored)
            - 'get_tags': List all available tags (path ignored)
        query: Search term for 'search' action. Matches against path/title.
        tag: Filter by tag for 'search' action. Use 'get_tags' to see available tags.

    Returns:
        For 'list': Lines like "[DIR] name/", "[FILE] name.md", "[SEC] Section Title"
        For 'read': The markdown content of the file or section
        For 'tree': Indented tree structure with [D]/[F]/[S] markers
        For 'search': List of matching paths
        For 'get_tags': List of available tags

    Examples:
        soe_explore_docs(path="/", action="list")  # See all docs
        soe_explore_docs(path="docs/guide_01_basics.md", action="list")  # See sections
        soe_explore_docs(path="docs/guide_01_basics.md", action="read")  # Read full file
        soe_explore_docs(path="docs/guide_01_basics.md/Quick Start", action="read")  # Read section
        soe_explore_docs(path="/", action="search", query="agent")  # Find agent-related docs
    """
    # Normalize path
    # Remove leading slash if present to match index keys (which are relative paths like 'docs/...')
    # But handle root '/' as well
    clean_path = path.strip("/")

    # Special case: "/" means "docs/" (default root)
    if clean_path == "" or path == "/":
        clean_path = "docs"

    # Dispatch actions
    if action == "list":
        return _handle_list(clean_path)
    elif action == "read":
        return _handle_read(clean_path)
    elif action == "tree":
        return _handle_tree(clean_path)
    elif action == "search":
        return _handle_search(query, tag)
    elif action == "get_tags":
        return _handle_get_tags()
    else:
        return f"Error: Unknown action '{action}'"

def _handle_list(path: str) -> str:
    # If path is empty/root, return root children
    if path == "" or path == ".":
        children = DOCS_INDEX.get("root_children", [])
        return _format_list(children)

    # Check if path exists in index
    # Try exact match first
    # Index keys usually end with / for dirs? My build script adds / for dirs.

    # Try as directory
    dir_key = path if path.endswith("/") else path + "/"
    if dir_key in DOCS_INDEX["items"]:
        item = DOCS_INDEX["items"][dir_key]
        return _format_list(item.get("children", []))

    # Try as file or section (no trailing slash)
    file_key = path.rstrip("/")
    if file_key in DOCS_INDEX["items"]:
        item = DOCS_INDEX["items"][file_key]
        return _format_list(item.get("children", []))

    return f"Error: Path '{path}' not found in index."

def _format_list(children: List[str]) -> str:
    if not children:
        return "(empty)"

    lines = []
    for child in sorted(children):
        item = DOCS_INDEX["items"][child]  # Children are always valid in well-formed index
        type_ = item.get("type", "unknown")

        # Display name is the last part of the path
        # For sections: docs/file.md/Section -> Section
        # For files: docs/file.md -> file.md
        display_name = child.rstrip("/").split("/")[-1]

        if type_ == "dir":
            lines.append(f"[DIR] {display_name}/")
        elif type_ == "file":
            lines.append(f"[FILE] {display_name}")
        elif type_ == "section":
            lines.append(f"[SEC] {display_name}")

    return "\n".join(lines)

def _handle_read(path: str) -> str:
    # Normalize
    key = path.rstrip("/")

    # Check if it exists as a file/section (exact match on stripped key)
    if key in DOCS_INDEX["items"]:
        item = DOCS_INDEX["items"][key]
        type_ = item.get("type")

        if type_ == "dir":
            return f"Error: '{path}' is a directory. Use action='list' or 'tree'."

    # Check if it exists as a directory (key + "/")
    elif (key + "/") in DOCS_INDEX["items"]:
        return f"Error: '{path}' is a directory. Use action='list' or 'tree'."

    else:
        return f"Error: Path '{path}' not found."

    # Get file path
    file_path_str = item.get("file_path") or item.get("path")  # For files, path is file_path

    # Read file relative to SOE package root
    full_path = SOE_ROOT / file_path_str
    try:
        content = full_path.read_text()
    except FileNotFoundError:
        return f"Error: File not found at '{full_path}'. The docs index may be out of date."
    lines = content.splitlines()

    if type_ == "file":
        return content

    # type_ == "section"
    start = item["start_line"] - 1
    end = item["end_line"]
    if end == -1:
        end = len(lines)

    section_lines = lines[start:end]
    return "\n".join(section_lines)


def _handle_tree(path: str) -> str:
    # Recursive listing
    # We can use the index structure

    # Normalize
    if path == "" or path == ".":
        roots = DOCS_INDEX.get("root_children", [])
        return _build_tree_str(roots, indent=0)

    key = path if path.endswith("/") else path + "/"
    # Try dir
    if key in DOCS_INDEX["items"]:
        return _build_tree_str([key], indent=0)

    # Try file
    key = path.rstrip("/")
    if key in DOCS_INDEX["items"]:
        return _build_tree_str([key], indent=0)

    return f"Error: Path '{path}' not found."

def _build_tree_str(paths: List[str], indent: int) -> str:
    out = []
    for p in sorted(paths):
        item = DOCS_INDEX["items"].get(p)
        if not item: continue

        display_name = p.rstrip("/").split("/")[-1]
        prefix = "  " * indent

        type_ = item.get("type")
        marker = "[D]" if type_ == "dir" else "[F]" if type_ == "file" else "[S]"

        out.append(f"{prefix}{marker} {display_name}")

        # Recurse
        children = item.get("children", [])
        if children:
            out.append(_build_tree_str(children, indent + 1))

    return "\n".join(out)

def _handle_search(query: str, tag: str) -> str:
    if not query and not tag:
        return "Error: Provide 'query' or 'tag' for search."

    # Tag filter
    candidate_paths = set(DOCS_INDEX["items"].keys())
    if tag:
        if tag in DOCS_INDEX["tags"]:
            candidate_paths = set(DOCS_INDEX["tags"][tag])
        else:
            return f"No results for tag '{tag}'"

    # Text search - split query into words and match ANY word
    # Also search in content_preview for better results
    final_results = set()

    if query:
        # Split query into words, filter out common words
        stop_words = {"and", "or", "the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "how", "does", "do", "is", "are", "what"}
        query_words = [w.lower() for w in query.split() if w.lower() not in stop_words and len(w) > 1]

        if not query_words:
            # Fall back to full query if all words were filtered
            query_words = [query.lower()]

        for p in candidate_paths:
            item = DOCS_INDEX["items"].get(p, {})

            # Search in path, title, and content_preview
            searchable_text = p.lower()
            if "title" in item:
                searchable_text += " " + item["title"].lower()
            if "content_preview" in item:
                searchable_text += " " + item["content_preview"].lower()

            # Match if ANY query word is found
            for word in query_words:
                if word in searchable_text:
                    final_results.add(p)
                    break
    else:
        # Tag only search
        final_results = candidate_paths

    if not final_results:
        return f"No results found for: {query_words if query else tag}"

    # Dedupe: skip sections if parent file is also in results
    deduped = set()
    for r in final_results:
        parts = r.rsplit("/", 1)
        if len(parts) == 2 and parts[0] in final_results:
            continue  # Skip section if parent file matches
        deduped.add(r)

    # Format results - limit to 20 most relevant
    sorted_results = sorted(deduped)[:20]
    result_text = "\n".join(sorted_results)

    if len(deduped) > 20:
        result_text += f"\n... and {len(deduped) - 20} more results"

    return result_text

def _handle_get_tags() -> str:
    tags = sorted(DOCS_INDEX.get("tags", {}).keys())
    return f"Available tags: {tags}"
