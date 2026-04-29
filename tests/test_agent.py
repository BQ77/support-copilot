"""Structural tests for Support Copilot.

These do not call the LLM - they validate file structure, Python
syntax, and that the project skeleton is intact. Real eval lives
in the (planned) eval harness.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).parent.parent


def _parse(filename: str):
    with open(ROOT / filename) as f:
        ast.parse(f.read())


def test_agent_syntax():
    _parse("agent.py")


def test_app_syntax():
    _parse("app.py")


def test_mcp_server_syntax():
    _parse("mcp_server.py")


def test_docs_folder_populated():
    docs = ROOT / "docs"
    assert docs.is_dir(), "docs/ folder missing"
    txt_files = list(docs.glob("*.txt"))
    assert len(txt_files) >= 1, "no .txt docs found"


def test_required_files():
    required = ["agent.py", "app.py", "Dockerfile", "requirements.txt", "README.md"]
    for fname in required:
        assert (ROOT / fname).is_file(), f"missing required file: {fname}"
