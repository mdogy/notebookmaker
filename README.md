# NotebookMaker

Convert lecture PDFs and PowerPoints into interactive Jupyter notebooks.

## Overview

NotebookMaker is a command-line tool that processes lecture materials (PDF or PowerPoint files) and generates two Jupyter notebooks for enhanced learning and note-taking.

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd notebookmaker

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## Usage

```bash
# Basic usage
notebookmaker path/to/lecture.pdf

# Specify output directory
notebookmaker path/to/lecture.pptx --output-dir my_notebooks

# Short form
notebookmaker lecture.pdf -o outputs
```

### Supported File Formats

- PDF (`.pdf`)
- PowerPoint (`.ppt`, `.pptx`)

## Project Structure

```
notebookmaker/
├── src/notebookmaker/    # Main package
│   ├── __init__.py       # Package initialization
│   ├── cli.py            # Command-line interface
│   └── utils.py          # Utility functions
├── tests/                # Test suite
├── prompts/              # Prompt templates
├── examples/             # Example lecture files
├── outputs/              # Generated notebooks (gitignored)
├── pyproject.toml        # Package configuration
├── CLAUDE.md             # Development guidelines
└── README.md             # This file
```

## Development

### Setup

```bash
# Install development dependencies
pip install -e ".[dev]"
```

### Code Quality

```bash
# Lint code
ruff check .

# Format code
ruff format .

# Type check
mypy src/
```

### Testing

```bash
# Run all tests
pytest -v

# Run with coverage
coverage run -m pytest
coverage report -m

# Generate HTML coverage report
coverage html
```

## License

MIT License
