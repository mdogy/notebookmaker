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

#### Option 1: Configuration File (Recommended)

Create a configuration file in your home directory:

```bash
# Copy the example configuration file to your home directory
cp .notebookmaker_config.yaml.example ~/.notebookmaker_config.yaml

# Edit the file and add your API keys
nano ~/.notebookmaker_config.yaml

# Protect the file (recommended)
chmod 600 ~/.notebookmaker_config.yaml
```

The configuration file should look like this:

```yaml
# Add your API keys (you only need keys for providers you plan to use)
anthropic_api_key: "sk-ant-your-key-here"
google_api_key: "your-google-key-here"
openai_api_key: "sk-your-openai-key-here"
openrouter_api_key: "sk-or-your-openrouter-key-here"
```

**Security Note**: NEVER commit `~/.notebookmaker_config.yaml` to version control. Keep this file in your home directory only.

#### Option 2: Environment Variables

If you prefer, you can use environment variables instead:

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

**Priority**: The configuration file (`~/.notebookmaker_config.yaml`) takes precedence over environment variables.

#### Option 3: Google Cloud Application Default Credentials

For Google Gemini, if you have Google Cloud CLI installed:

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
├── prompts/                           # Prompt templates
├── examples/                          # Example lecture files
├── outputs/                           # Generated notebooks (gitignored)
├── .notebookmaker_config.yaml.example # Config template (commit this)
├── test_llm_providers.py              # LLM integration test script
├── pyproject.toml                     # Package configuration
├── CLAUDE.md                          # Development guidelines
└── README.md                          # This file

Note: User configuration file (~/.notebookmaker_config.yaml) lives in your home directory, NOT in the project.
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
