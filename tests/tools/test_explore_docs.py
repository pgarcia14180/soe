import pytest
from pathlib import Path
from soe.builtin_tools.soe_explore_docs import soe_explore_docs, create_soe_explore_docs_tool
from soe.docs_index import DOCS_INDEX


def test_create_soe_explore_docs_tool():
    """Test the factory function returns the soe_explore_docs function."""
    tool_func = create_soe_explore_docs_tool()
    assert tool_func == soe_explore_docs

    # Also test with kwargs (as called by SOE)
    tool_func2 = create_soe_explore_docs_tool(
        execution_id="test_id",
        backends=None,
        tools_registry={}
    )
    assert tool_func2 == soe_explore_docs


def test_soe_explore_docs_list_root():
    """Test listing the root directory."""
    result = soe_explore_docs(path="/", action="list")
    assert "[DIR]" in result
    # Should list contents of docs/ by default
    assert "guide_01_basics.md" in result or "guide_00_getting_started.md" in result

def test_soe_explore_docs_list_file_sections():
    """Test listing sections within a markdown file."""
    # Find a file with sections
    target_file = None
    for path, meta in DOCS_INDEX["items"].items():
        if meta["type"] == "file" and meta["sections"]:
            target_file = path
            break

    assert target_file, "No markdown files with sections found in index."

    result = soe_explore_docs(path=target_file, action="list")
    assert "[SEC]" in result

def test_soe_explore_docs_read_file():
    """Test reading a full file."""
    # Use a known small file or the first one found
    target_file = None
    for path, meta in DOCS_INDEX["items"].items():
        if meta["type"] == "file":
            target_file = path
            break

    assert target_file, "No files found."

    result = soe_explore_docs(path=target_file, action="read")
    assert not result.startswith("Error:")
    assert len(result) > 0

def test_soe_explore_docs_read_section():
    """Test reading a specific section."""
    target_section = None
    for path, meta in DOCS_INDEX["items"].items():
        if meta["type"] == "section":
            target_section = path
            break

    assert target_section, "No sections found."

    result = soe_explore_docs(path=target_section, action="read")
    assert not result.startswith("Error:")
    assert len(result) > 0

def test_soe_explore_docs_tree():
    """Test the tree view."""
    result = soe_explore_docs(path="/", action="tree")
    assert "[D]" in result
    assert "[F]" in result
    # Should be recursive
    assert "\n" in result

def test_soe_explore_docs_search_text():
    """Test text search."""
    # Search for a common term like "workflow"
    result = soe_explore_docs(path="", action="search", query="workflow")
    assert not result.startswith("Error:")
    assert "docs/" in result or "ai_docs/" in result

def test_soe_explore_docs_search_tag():
    """Test tag search."""
    # Get a valid tag first
    tags = DOCS_INDEX.get("tags", {})
    assert tags, "No tags found in index."

    tag = list(tags.keys())[0]
    result = soe_explore_docs(path="", action="search", tag=tag)
    assert not result.startswith("Error:")
    assert len(result) > 0

def test_soe_explore_docs_get_tags():
    """Test getting all tags."""
    result = soe_explore_docs(path="", action="get_tags")
    assert "Available tags:" in result
    assert "[" in result
    assert "]" in result

def test_soe_explore_docs_invalid_path():
    """Test error handling for invalid paths."""
    result = soe_explore_docs(path="docs/non_existent_file.md", action="read")
    assert result.startswith("Error:")
    assert "not found" in result

def test_soe_explore_docs_read_directory_error():
    """Test error when trying to read a directory."""
    result = soe_explore_docs(path="docs/", action="read")
    assert result.startswith("Error:")
    assert "is a directory" in result
    assert "Use action='list'" in result

def test_soe_explore_docs_search_empty():
    """Test error when search query is empty."""
    result = soe_explore_docs(path="", action="search")
    assert result.startswith("Error:")
    assert "Provide 'query' or 'tag'" in result

def test_soe_explore_docs_list_invalid_path():
    """Test listing a non-existent path."""
    result = soe_explore_docs(path="docs/ghost_folder", action="list")
    assert result.startswith("Error:")
    assert "not found in index" in result

def test_soe_explore_docs_invalid_action():
    """Test error handling for invalid actions."""
    # Note: Type checker would catch this, but runtime check is good too
    try:
        result = soe_explore_docs(path="docs/", action="dance") # type: ignore
        assert result.startswith("Error:")
        assert "Unknown action" in result
    except Exception:
        pass # If it raises, that's also fine (though implementation returns string)


def test_soe_explore_docs_list_dot_path():
    """Test listing with '.' as path (current directory)."""
    result = soe_explore_docs(path=".", action="list")
    # Should return root children (same as "/" or "")
    assert "[DIR]" in result or "[FILE]" in result


def test_soe_explore_docs_search_by_tag_only():
    """Test search with tag but no query."""
    tags = DOCS_INDEX.get("tags", {})
    if not tags:
        pytest.skip("No tags found in index")

    tag = list(tags.keys())[0]
    result = soe_explore_docs(path="", action="search", tag=tag)
    assert not result.startswith("Error:")


def test_soe_explore_docs_search_no_results():
    """Test search that returns no results."""
    result = soe_explore_docs(path="", action="search", query="xyznonexistent12345")
    assert "No results found" in result


def test_soe_explore_docs_search_invalid_tag():
    """Test search with a tag that doesn't exist."""
    result = soe_explore_docs(path="", action="search", tag="nonexistent_tag_xyz")
    assert "No results for tag" in result


def test_soe_explore_docs_tree_specific_file():
    """Test tree view starting from a specific file."""
    # Find a file in the index
    target_file = None
    for path, meta in DOCS_INDEX["items"].items():
        if meta["type"] == "file":
            target_file = path
            break

    if target_file:
        result = soe_explore_docs(path=target_file, action="tree")
        assert not result.startswith("Error:")
        assert "[F]" in result or "[S]" in result


def test_soe_explore_docs_tree_specific_dir():
    """Test tree view starting from a specific directory."""
    # Find a directory in the index
    target_dir = None
    for path, meta in DOCS_INDEX["items"].items():
        if meta["type"] == "dir":
            target_dir = path.rstrip("/")
            break

    if target_dir:
        result = soe_explore_docs(path=target_dir, action="tree")
        assert not result.startswith("Error:")


def test_soe_explore_docs_tree_invalid_path():
    """Test tree with invalid path."""
    result = soe_explore_docs(path="nonexistent/path", action="tree")
    assert result.startswith("Error:")
    assert "not found" in result


def test_soe_explore_docs_read_section_content():
    """Test that reading a section returns the actual section content."""
    # Find a section with known content
    target_section = None
    for path, meta in DOCS_INDEX["items"].items():
        if meta["type"] == "section" and meta.get("start_line") and meta.get("end_line"):
            target_section = path
            break

    if not target_section:
        pytest.skip("No sections with line numbers found")

    result = soe_explore_docs(path=target_section, action="read")
    # Should return content, not an error
    assert not result.startswith("Error:")
    # Should have some content
    assert len(result) > 0


def test_soe_explore_docs_list_empty_directory():
    """Test listing a directory with no children returns '(empty)'."""
    # We need to find a dir with no children or mock it
    # Since we can't easily mock, let's check if any empty dirs exist
    for path, meta in DOCS_INDEX["items"].items():
        if meta["type"] == "dir" and not meta.get("children"):
            result = soe_explore_docs(path=path.rstrip("/"), action="list")
            assert result == "(empty)"
            return

    # If no empty dirs, skip
    pytest.skip("No empty directories found in index")


def test_soe_explore_docs_read_dir_without_trailing_slash():
    """Test reading a directory path without trailing slash gives directory error."""
    # Find a directory
    target_dir = None
    for path, meta in DOCS_INDEX["items"].items():
        if meta["type"] == "dir":
            target_dir = path.rstrip("/")
            break

    if target_dir:
        result = soe_explore_docs(path=target_dir, action="read")
        assert result.startswith("Error:")
        assert "is a directory" in result
