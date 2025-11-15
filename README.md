# NotebookMaker

Convert lecture PDFs into interactive Jupyter notebooks using a two-phase, vision-enabled LLM architecture.

## Overview

NotebookMaker is a command-line tool that processes lecture PDFs and generates two Jupyter notebooks:
1.  **Instructor Notebook**: Contains complete, runnable code examples extracted from the lecture.
2.  **Student Notebook**: Contains the same examples but with key code sections removed for students to fill in as exercises.

It uses a sophisticated **two-phase architecture**:
-   **Phase 1 (Analysis)**: A vision-capable LLM analyzes the PDF to identify logical sections and extract code (from text and images), equations, and key concepts. This produces a structured JSON analysis file.
-   **Phase 2 (Generation)**: A second LLM uses the structured analysis to generate clean, code-focused notebooks, ensuring higher relevance and quality.

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

#### Option 3: (Not Required) Google Cloud Application Default Credentials

NotebookMaker does **not** require Google Cloud Application Default Credentials (ADC) for the lecture-to-notebook workflow. Configure Gemini access with an explicit API key instead of relying on `gcloud auth application-default login`.

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

The tool operates in two phases. The first time you run it on a PDF, it will perform the analysis phase, which can take some time. The result is saved as a `.analysis.json` file. Subsequent runs will use this cached analysis, making them much faster.

```bash
# Basic usage (uses Google Gemini for analysis by default)
notebookmaker path/to/lecture.pdf

# Specify a different provider for analysis
notebookmaker path/to/lecture.pdf --analysis-provider anthropic

# Specify providers for both phases
notebookmaker path/to/lecture.pdf --analysis-provider google --generation-provider anthropic

# Specify models for each phase
notebookmaker path/to/lecture.pdf --analysis-model gemini-1.5-pro-latest --generation-model claude-3-5-sonnet-20240620

# Specify output directory and minimum priority for code sections
notebookmaker lecture.pdf -o my_notebooks --min-priority 7
```

### Supported File Formats

- PDF (`.pdf`)

## Project Structure

```
notebookmaker/
├── src/notebookmaker/       # Main package
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Command-line interface
│   ├── utils.py             # Main pipeline orchestrator
│   ├── analysis.py          # Phase 1: PDF analysis logic
│   ├── generation.py        # Phase 2: Notebook generation logic
│   ├── vision.py            # Vision LLM interaction
│   ├── models.py            # Pydantic data models
│   └── llm/                 # LLM integration layer
│       ├── __init__.py      # LLM module exports
│       ├── credentials.py   # Secure credential discovery
│       └── providers.py     # LLM provider implementations
├── tests/                   # Test suite
├── prompts/                           # Prompt templates
├── examples/                          # Example lecture files
├── outputs/                           # Generated notebooks (gitignored)
├── .notebookmaker_config.yaml.example # Config template (commit this)
├── test_llm_providers.py              # LLM integration test script
├── pyproject.toml                     # Package configuration
├── GEMINI.md                          # Development guidelines for Gemini
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
source venv/bin/activate  # or prefix commands with venv/bin/python
pytest -v

# Run with coverage
coverage run -m pytest
coverage report -m

# Generate HTML coverage report
coverage html
```

## License

MIT License
