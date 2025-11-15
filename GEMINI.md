# GEMINI.md

This file provides guidance to Gemini when working with code in this repository.

# Project Overview

This is a Python project following modern best practices with strict type checking, linting, runtime validation, and comprehensive testing.

# Code Organization

- **Core Principle**: Factor common utility functionality into library modules under `lib/` or `utils/`. Scripts should be thin orchestration layers that import and compose library functions.
- **Project Structure**:
  - `src/`: Main application code and library modules
  - `tests/`: Test suite using pytest
  - `scripts/`: CLI entry points (should delegate to library code)

# Python Environment

- Use Python 3.11+
- Manage dependencies with `pip` or `uv`
- Always activate virtual environment before running commands

# Code Quality Standards

## Linting with Ruff
- Run `ruff check .` before committing
- Run `ruff format .` to auto-format code
- Fix all linting errors; warnings should be addressed or explicitly ignored
- Configuration in `pyproject.toml` or `ruff.toml`

## Type Checking with mypy
- Run `mypy src/` to check type hints
- All functions must have type annotations for parameters and return values
- Use strict mode: aim for zero mypy errors
- Configuration in `pyproject.toml` under `[tool.mypy]`

## Runtime Validation with Pydantic
- Use Pydantic models for all data validation at runtime
- Define models for API inputs, configuration, and external data
- Leverage Pydantic's type coercion and validation features
- Example:
  ```python
  from pydantic import BaseModel, Field

  class UserConfig(BaseModel):
      username: str = Field(min_length=1)
      age: int = Field(ge=0)
  ```

# Testing Requirements

## Testing with pytest
- Run tests: `pytest -v`
- Run single test: `pytest tests/test_module.py::test_function`
- Use fixtures for shared test setup
- Test edge cases, invalid inputs, and error conditions

## CLI Testing with CliRunner
- Use `click.testing.CliRunner` for testing CLI commands
- Test both success and failure paths
- Validate output, exit codes, and side effects
- Example:
```python
from click.testing import CliRunner

def test_cli_command():
    runner = CliRunner()
    result = runner.invoke(cli_command, ['--arg', 'value'])
    assert result.exit_code == 0
```

## Cram Tests
- Use `cram` for shell-based integration tests
- Place `.t` files in `tests/` directory
- Run with `cram tests/*.t`
- Test full CLI workflows and expected outputs

## Code Coverage with coverage.py
- Run with coverage: `coverage run -m pytest`
- Generate report: `coverage report -m`
- Generate HTML: `coverage html` (view at `htmlcov/index.html`)
- Target: 80%+ coverage for all modules (aim for this minimum, no need to obsess beyond it)
- Focus coverage on library code, not thin script wrappers

# Workflow

1. **Before coding**: Review project structure and identify where new functionality belongs (library vs. script)
2. **During coding**:
   - Write library functions with full type hints
   - Add Pydantic models for data validation
   - Keep scripts minimal—delegate logic to libraries
3. **After coding**:
   - Run `ruff check . && ruff format .`
   - Run `mypy src/`
   - Write tests and run `pytest -v`
   - Check coverage: `coverage run -m pytest && coverage report -m` (aim for 80%+)
4. **Before committing**:
   - Ensure all quality checks pass
   - Update `README.md` if user-facing features, installation, or usage changed
   - Update `Project_Progress.md` with:
     * Status changes (% completion updates for completed/in-progress sections)
     * New evolution section explaining commit-to-commit changes
     * Semantic context: what changed, why it matters, migration impact

# Code Style

- Follow PEP 8 (enforced by Ruff)
- Use descriptive variable names; avoid abbreviations
- Prefer early returns over nested conditionals
- Extract complex logic into helper functions
- Document public functions with docstrings (Google or NumPy style)

# Refactoring Guidelines

- **Extract utilities**: If code is repeated across scripts, move it to a library module
- **Single Responsibility**: Each function should do one thing well
- **Type safety first**: Add type hints before refactoring logic
- **Test before refactoring**: Ensure tests pass, refactor, verify tests still pass

# Do Not

- Do not write business logic directly in CLI scripts—use library functions
- Do not skip type hints on any function
- Do not commit code that fails `ruff check`, `mypy`, or `pytest`
- Do not write tests without checking coverage gaps
- Do not use bare `except:` clauses—catch specific exceptions

# Commands Reference

- `ruff check .` — Lint codebase
- `ruff format .` — Format code
- `mypy src/` — Type check
- `pytest -v` — Run all tests
- `pytest tests/test_file.py` — Run specific test file
- `coverage run -m pytest` — Run tests with coverage
- `coverage report -m` — Show coverage report
- `coverage html` — Generate HTML coverage report
- `cram tests/*.t` — Run integration tests

# Documentation Synchronization

This repository is developed by multiple code agents. To ensure all agents can easily analyze the current project state and adhere to established styles, the following documentation files must be kept in sync:

- `Project_Progress.md`: Tracks the overall project history, status, and next steps.
- `GEMINI.md`: Provides guidance specific to Gemini when working with this codebase.
- `CLAUDE.md`: Provides guidance specific to Claude when working with this codebase.
- `AGENTS.md`: Provides general guidance for all agents.

When making changes to project guidelines, workflow, or status, ensure these files are updated consistently. Do not delete these files.
