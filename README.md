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

### API Configuration

NotebookMaker uses LLM APIs to analyze lecture content and generate notebooks. You need to configure at least one LLM provider.

#### Option 1: Environment Variables (Recommended)

```bash
# For Anthropic Claude (recommended)
export ANTHROPIC_API_KEY="sk-ant-..."

# For Google Gemini
export GOOGLE_API_KEY="..."

# For OpenAI
export OPENAI_API_KEY="sk-..."

# For OpenRouter
export OPENROUTER_API_KEY="sk-or-..."
```

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) to make them permanent.

#### Option 2: .env File

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API keys
# NEVER commit this file to git (it's already in .gitignore)
```

#### Option 3: Google Cloud Application Default Credentials

If you have Google Cloud CLI installed:

```bash
gcloud auth application-default login
```

This allows NotebookMaker to use your Google Cloud credentials for Gemini API access.

#### Getting API Keys

- **Anthropic Claude**: https://console.anthropic.com/
- **Google Gemini**: https://makersuite.google.com/app/apikey
- **OpenAI**: https://platform.openai.com/api-keys
- **OpenRouter**: https://openrouter.ai/keys

#### Testing Your API Setup

```bash
# Test a specific provider
python test_llm_providers.py anthropic

# Test all configured providers
python test_llm_providers.py
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
├── src/notebookmaker/       # Main package
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Command-line interface
│   ├── utils.py             # Utility functions
│   └── llm/                 # LLM integration layer
│       ├── __init__.py      # LLM module exports
│       ├── models.py        # Pydantic models
│       ├── credentials.py   # Secure credential discovery
│       └── providers.py     # LLM provider implementations
├── tests/                   # Test suite
├── prompts/                 # Prompt templates
├── examples/                # Example lecture files
├── outputs/                 # Generated notebooks (gitignored)
├── .env.example             # API key template (commit this)
├── .env                     # Your API keys (NEVER commit)
├── test_llm_providers.py    # LLM integration test script
├── pyproject.toml           # Package configuration
├── CLAUDE.md                # Development guidelines
└── README.md                # This file
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
