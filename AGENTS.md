# Repository Guidelines

## Project Structure & Module Organization
- Keep orchestration light inside `src/notebookmaker/cli.py`; move reusable logic into nearby library modules (`utils.py`, `llm/`, provider adapters). Thin scripts keep testing easy.
- `src/notebookmaker/llm/` owns credentials discovery, provider clients, and Pydantic models for runtime validation of API inputs and outputs.
- `tests/` mirrors the package layout for pytest modules and holds any `.t` cram scripts for shell-level CLI workflows; `prompts/`, `examples/`, and gitignored `outputs/` house prompt templates, sample decks, and generated notebooks.
- `test_llm_providers.py` is the on-ramp for validating Anthropic, Gemini, OpenAI, or OpenRouter credentials before running the CLI end to end.

## Python Environment & Tooling
- Target Python 3.11+ and work inside an activated virtual environment (`python -m venv venv && source venv/bin/activate`).
- Install everything once with `pip install -e ".[dev]"` (or `uv pip install .[dev]`); rerun after dependency bumps.
- Use `ruff check .` followed by `ruff format .` and `mypy src/` as non-negotiable gates before any push.

## Build, Test, and Development Commands
- `notebookmaker path/to/lecture.pdf -o outputs` exercises the Click CLI; keep logic in libraries so this stays thin.
- `pytest -v` runs the suite; use `pytest tests/test_cli.py::test_command` when iterating on a single case and `cram tests/*.t` for shell transcripts.
- `python test_llm_providers.py anthropic` (swap provider name) verifies API keys; capture failures in PR notes.
- `coverage run -m pytest && coverage report -m` (target ≥90% module coverage) and `coverage html` to inspect gaps.

## Coding Style & Naming Conventions
- Ruff enforces PEP 8, 88-column formatting, and import order; prefer early returns, descriptive names, and helper functions over nested branches.
- Every function (production or test) needs full type hints; document public surfaces with concise docstrings and avoid bare `except:`.
- Keep CLI flags lowercase-hyphenated, modules snake_case, classes PascalCase, and prompt files declarative. Never embed credentials or user data in checked-in files.

## Testing Guidelines
- Mirror module names (`tests/test_cli.py`, `tests/llm/test_providers.py`, etc.) so pytest discovery (`test_*.py`, `Test*`, `test_*`) matches `pyproject.toml`.
- Use `click.testing.CliRunner` for CLI units, Pydantic factories for datum validation, and fixtures to mock LLM responses. Add cram `.t` files whenever a CLI flow spans multiple shell steps.
- Keep coverage above 80% by focusing on library code rather than the thin CLI wrapper; record manual credential checks in PR descriptions. (80% is the goal - no need to thrash beyond it.)

## Commit & Pull Request Guidelines
- Follow the existing imperative tense seen in `git log` (e.g., "Add NotebookMaker package structure"); keep subjects ≤72 chars and limit each commit to one concern.
- **Before each commit**, maintain documentation:
  * Update `README.md` if user-facing features, installation steps, or usage patterns changed
  * Update `Project_Progress.md` with a new evolution section explaining:
    - What changed from the previous commit (not just what the commit did)
    - Why those changes matter (architectural impact, user benefits)
    - Migration impact and key differences (before/after comparison)
    - Status percentage updates for completed/in-progress work
- A PR description must summarize intent, list the quality gates you ran (`ruff`, `mypy`, `pytest`, coverage, cram, credential smoke tests), and cross-link issues or design docs. Include screenshots only when notebook UX shifts.
- Ensure `~/.notebookmaker_config.yaml` stays out of version control, scrub API keys from notebooks/logs, and rotate shared keys if any provider command reports unauthorized access.

## API & Security Notes
- Configure Anthropic, Gemini, OpenAI, or OpenRouter keys through `~/.notebookmaker_config.yaml` (see `.notebookmaker_config.yaml.example`) or environment variables, and prefer sandbox-scoped tokens.
- The YAML config file takes priority over environment variables and should be protected with `chmod 600 ~/.notebookmaker_config.yaml`.
- Enforce runtime validation with Pydantic models for any external payload; fail fast rather than allowing unchecked dictionaries through the pipeline.
