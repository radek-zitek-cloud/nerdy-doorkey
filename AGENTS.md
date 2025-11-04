# Repository Guidelines

## Project Structure & Module Organization
Keep the repository root small. `main.py` is the current entry point and should remain the place where the command-line flow starts. Add any future modules under a dedicated package (for example `src/`) and keep tests in a sibling `tests/` directory so runtime code and verification code stay separate. The `.venv/` directory is a developer convenience only—never commit its contents.

## Build, Test, and Development Commands
Always activate the local virtual environment first with `source .venv/bin/activate`. Run the project locally with `python main.py`; this is the fastest way to verify user-facing output. Dependencies are intentionally minimal. If you add third-party packages, capture them in `requirements.txt` and sync environments with `python -m pip install -r requirements.txt`. Once a `tests/` suite exists, execute `python -m pytest -q` to run it headlessly and surface failures quickly.

## Coding Style & Naming Conventions
Follow PEP 8: four spaces per indent, `snake_case` for functions and variables, and `PascalCase` for classes. Use descriptive module names that mirror the feature (e.g., `door_logic.py`). Add docstrings to public functions explaining side effects, and include type hints for new functions to make the lightweight codebase easier to review.

## Testing Guidelines
Adopt `pytest` for unit and behavior checks. Place files inside `tests/` and name them `test_<feature>.py` to keep discovery predictable. Focus on pure functions where possible and use `capsys` to assert console output from `main.py`. Aim to cover new code paths introduced in each change; add regression tests for every bug fix before merging.

## Commit & Pull Request Guidelines
Keep commit subjects short, present tense, and imperative (the existing `initial commit` shows the preferred concise style). Push feature work in focused commits so reviewers can follow the narrative. Pull requests should include a short summary, linked issues when relevant, and a note on manual or automated test results (`python -m pytest -q`, `python main.py`). Provide screenshots only if output formatting changes.
