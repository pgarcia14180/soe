import pytest
import os

# Default model for LLM tests (when stubs aren't used)
DEFAULT_MODEL = "gpt-4o"

def pytest_addoption(parser):
    parser.addoption(
        "--backend",
        action="store",
        default="file",
        help="Backend to use: file or memory"
    )
    parser.addoption(
        "--model",
        action="store",
        default=DEFAULT_MODEL,
        help="Model name for LLM calls"
    )
    parser.addoption(
        "--show",
        action="store",
        default="",
        help="Comma-separated: telemetry,context,conversation_history,prompt,response"
    )

def pytest_configure(config):
    backend = config.getoption("--backend")
    if backend:
        os.environ["SOE_TEST_BACKEND"] = backend

    model = config.getoption("--model")
    if model:
        os.environ["SOE_TEST_MODEL"] = model

    show = config.getoption("--show")
    if show:
        os.environ["SOE_VERBOSE"] = show
