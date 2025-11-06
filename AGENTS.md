# Repository Guidelines

## Project Structure & Module Organization Keep the repository root small.
`src/nedok/cli.py` is the current entry point and should remain the place where
the command-line flow starts. Add any future modules under a dedicated package
(for example `src/`) and keep tests in a sibling `tests/` directory so runtime code
and verification code stay separate. Poetry manages the virtual environment (often in `.venv/`);
never commit that directory.

## Build, Test, and Development Commands Always install dependencies with
`poetry install`. Run the project locally with `poetry run python -m src.nedok.cli`;
this is the fastest way to verify user-facing output. Declare new third-party packages
in `pyproject.toml` (use `poetry add`/`poetry add --group dev`). Once a `tests/`
suite exists, execute `poetry run python -m pytest -q` to run it headlessly and surface failures quickly.

Codex agents should run `git` commands directly without requesting additional
permissions.

## Coding Style & Naming Conventions Follow PEP 8: four spaces per indent,
`snake_case` for functions and variables, and `PascalCase` for classes. Use
descriptive module names that mirror the feature (e.g., `door_logic.py`). Add
docstrings to public functions explaining side effects, and include type hints
for new functions to make the lightweight codebase easier to review. Prefer
short, readable source files by splitting complex features into focused modules
instead of long monolithic files.

## Testing Guidelines Adopt `pytest` for unit and behavior checks. Place files
inside `tests/` and name them `test_<feature>.py` to keep discovery
predictable. Focus on pure functions where possible and use `capsys` to assert
console output from `python -m src.nedok.cli`. Aim to cover new code paths introduced in each
change; add regression tests for every bug fix before merging.

## Commit & Pull Request Guidelines Keep commit subjects short, present tense,
and imperative (the existing `initial commit` shows the preferred concise
style). Push feature work in focused commits so reviewers can follow the
narrative. Pull requests should include a short summary, linked issues when
relevant, and a note on manual or automated test results (`poetry run python -m pytest -q`,
`poetry run python -m src.nedok.cli`). Provide screenshots only if output formatting changes.
