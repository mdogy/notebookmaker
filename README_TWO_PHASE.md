# Two-Phase Architecture Guide

## Overview

NotebookMaker uses a **two-phase architecture** to generate high-quality, code-focused Jupyter notebooks from lecture PDFs:

1. **Phase 1 (Analysis)**: A multimodal vision LLM analyzes PDF pages to extract structured information about code-worthy content
2. **Phase 2 (Generation)**: An LLM generates Jupyter notebooks focusing only on executable code sections

This architecture addresses three critical issues:
- **Problem 1**: Generated notebooks had too much narrative text (not code-focused)
- **Problem 2**: Text extraction missed equations, code screenshots, and diagrams in images
- **Problem 3**: Token limits prevented processing large PDFs in a single API call

## Quick Start

### Prerequisites

1. Install system dependencies:
```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows (using Chocolatey)
choco install poppler
```

2. Install Python package:
```bash
pip install -e .
```

3. Configure API keys in `~/.notebookmaker_config.yaml`:
```yaml
# Copy example file
cp .notebookmaker_config.yaml.example ~/.notebookmaker_config.yaml

# Edit and add your API keys
vim ~/.notebookmaker_config.yaml
```

### Basic Usage

```bash
# Analyze and generate notebooks in one command
notebookmaker lecture.pdf -o outputs/

# Or run phases separately:

# Phase 1: Analyze PDF (creates lecture.analysis.json)
notebookmaker analyze lecture.pdf

# Phase 2: Generate notebooks from analysis
notebookmaker generate lecture.analysis.json -o outputs/
```

## Configuration

### Two-Phase Configuration

Recommended setup using **Gemini 2.0 Flash** for both phases (multimodal + fast):

```yaml
# ~/.notebookmaker_config.yaml

# API Keys
google_api_key: "your-google-api-key-here"

# Phase 1: Analysis (requires vision capabilities)
analysis:
  provider: "google"
  model: "gemini-2.0-flash-exp"  # Multimodal: supports image input
  max_tokens: 2000
  temperature: 0.3

# Phase 2: Generation (can use same or different model)
generation:
  provider: "google"
  model: "gemini-2.0-flash-exp"
  max_tokens: 16000
  temperature: 0.3
```

### Alternative Configurations

#### Claude 3.5 Sonnet (Excellent Vision + Reasoning)

```yaml
anthropic_api_key: "your-anthropic-key-here"

analysis:
  provider: "anthropic"
  model: "claude-3-5-sonnet-20241022"  # Multimodal
  max_tokens: 2000
  temperature: 0.3

generation:
  provider: "anthropic"
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 16000
  temperature: 0.3
```

#### Cost Optimization (Different Models Per Phase)

```yaml
# Fast, cheap multimodal for analysis
analysis:
  provider: "anthropic"
  model: "claude-3-5-haiku-20241022"  # Cheaper
  max_tokens: 2000
  temperature: 0.3

# Better quality for generation
generation:
  provider: "anthropic"
  model: "claude-3-5-sonnet-20241022"  # Higher quality
  max_tokens: 16000
  temperature: 0.3
```

#### GPT-4o

```yaml
openai_api_key: "your-openai-key-here"

analysis:
  provider: "openai"
  model: "gpt-4o"  # Excellent vision
  max_tokens: 2000
  temperature: 0.3

generation:
  provider: "openai"
  model: "gpt-4o-mini"  # Cheaper for generation
  max_tokens: 16000
  temperature: 0.3
```

## Supported Vision Models

| Provider | Model | Vision? | Notes |
|----------|-------|---------|-------|
| **Google** | gemini-2.0-flash-exp | ✅ | **Recommended** - Fast, multimodal |
| Google | gemini-1.5-pro | ✅ | High quality |
| **Anthropic** | claude-3-5-sonnet-20241022 | ✅ | Excellent vision + reasoning |
| Anthropic | claude-3-5-haiku-20241022 | ✅ | Fast, cheaper |
| **OpenAI** | gpt-4o | ✅ | Excellent vision |
| OpenAI | gpt-4o-mini | ✅ | Cheaper option |

⚠️ **Important**: Phase 1 (analysis) **requires** a vision-capable model. Phase 2 (generation) can use any model.

## Phase 1: Analysis

### What It Does

The analysis phase:
1. Converts PDF pages to images (5-10 pages per chunk)
2. Sends images to vision LLM with analysis prompt
3. LLM extracts structured information:
   - Sections with executable code
   - Code snippets (from images or text)
   - Equations (as LaTeX)
   - Conceptual dependencies
4. Aggregates chunk analyses into single `analysis.json`

### Output Format

The analysis produces a JSON file with this structure:

```json
{
  "lecture_title": "Hypothesis Testing",
  "total_pages": 42,
  "sections": [
    {
      "section_id": "coin_flip_simulation",
      "title": "Simulating Coin Flips",
      "pages": [5, 6],
      "has_code": true,
      "code_snippets": [
        {
          "code": "import numpy as np\nflips = np.random.randint(0, 2, size=(10000, 100))",
          "language": "python",
          "line_number": null
        }
      ],
      "equations": [
        {
          "latex": "p = \\frac{n_{heads}}{n_{total}}",
          "description": "Proportion of heads in coin flips"
        }
      ],
      "concepts": ["simulation", "probability", "randomness"],
      "dependencies": [],
      "priority": 9
    }
  ],
  "metadata": {
    "author": "Dr. Data Science",
    "course": "STAT 101"
  }
}
```

### Token Management

- **Input**: 5-10 pages as images (~5,000 tokens per chunk)
- **Output**: Compact JSON (~500-1000 tokens per chunk)
- **Example**: 42-page PDF = ~8-9 API calls, ~4,500 output tokens total

### Customization

```bash
# Adjust chunk size (pages per API call)
notebookmaker analyze lecture.pdf --chunk-size 5

# Use different provider/model
notebookmaker analyze lecture.pdf --analysis-provider anthropic --analysis-model claude-3-5-sonnet-20241022

# Save analysis to custom location
notebookmaker analyze lecture.pdf -o custom_analysis.json
```

## Phase 2: Generation

### What It Does

The generation phase:
1. Loads `analysis.json`
2. Filters sections where `has_code: true`
3. Generates Jupyter notebook cells:
   - **Markdown cells**: Brief introduction with LaTeX equations
   - **Code cells**: Working examples (instructor) or incomplete (student)
4. Outputs instructor and student notebooks

### Priority Filtering

Only sections with sufficient priority are included:

```python
# Default: priority >= 5
analysis.get_code_sections(min_priority=5)

# High priority only
analysis.get_code_sections(min_priority=7)
```

**Priority Scale**:
- **7-10**: Working code examples, simulations, algorithm implementations
- **4-6**: Code snippets illustrating concepts, setup code
- **1-3**: Pure theory, definitions, background (excluded by default)

### Dependency Order

Notebooks respect section dependencies:

```python
# Sections are ordered to respect dependencies
ordered_sections = analysis.get_dependency_order()
```

Example: If "permutation_test" depends on "coin_flip_simulation", the coin flip section comes first in the notebook.

### Customization

```bash
# Generate from existing analysis
notebookmaker generate analysis.json -o outputs/

# Use different provider/model for generation
notebookmaker generate analysis.json --generation-provider anthropic

# Control notebook type
notebookmaker generate analysis.json --notebook-type instructor
notebookmaker generate analysis.json --notebook-type student
```

## Command Line Reference

### Analyze Command

```bash
notebookmaker analyze <PDF_FILE> [OPTIONS]

Options:
  -o, --output PATH            Output path for analysis.json
  --chunk-size INTEGER         Pages per API call (default: 10)
  --analysis-provider TEXT     LLM provider (google, anthropic, openai)
  --analysis-model TEXT        Model name (overrides config)
  --dpi INTEGER               Image resolution (default: 150)
```

### Generate Command

```bash
notebookmaker generate <ANALYSIS_JSON> [OPTIONS]

Options:
  -o, --output-dir PATH        Output directory for notebooks
  --generation-provider TEXT   LLM provider for generation
  --generation-model TEXT      Model name (overrides config)
  --notebook-type TEXT         'instructor', 'student', or 'both' (default)
  --min-priority INTEGER       Minimum section priority (default: 5)
```

### Combined Command

```bash
notebookmaker <PDF_FILE> [OPTIONS]

# Runs both phases automatically
# Analysis is saved to <PDF_FILE>.analysis.json
# Notebooks are generated to output directory
```

## Python API

### Programmatic Usage

```python
from pathlib import Path
from notebookmaker.analysis import analyze_pdf
from notebookmaker.models import LectureAnalysis

# Phase 1: Analyze PDF
analysis = analyze_pdf(
    pdf_path=Path("lecture.pdf"),
    output_path=Path("lecture.analysis.json"),
    chunk_size=10,
    provider="google",
    model="gemini-2.0-flash-exp"
)

# Access results
print(f"Title: {analysis.lecture_title}")
print(f"Code sections: {len(analysis.get_code_sections())}")

# Filter by priority
high_priority = analysis.get_code_sections(min_priority=7)
for section in high_priority:
    print(f"  - {section.title} (priority {section.priority})")
    print(f"    Code snippets: {len(section.code_snippets)}")
    print(f"    Equations: {len(section.equations)}")

# Get dependency-ordered sections
ordered = analysis.get_dependency_order()

# Phase 2: Generate notebooks (implementation in progress)
# generate_notebooks(analysis, output_dir=Path("outputs/"))
```

### Loading Existing Analysis

```python
import json
from pathlib import Path
from notebookmaker.models import LectureAnalysis

# Load from file
analysis_path = Path("lecture.analysis.json")
with open(analysis_path) as f:
    data = json.load(f)

# Validate with Pydantic
analysis = LectureAnalysis(**data)

# Use as normal
code_sections = analysis.get_code_sections()
```

## Troubleshooting

### Common Issues

#### 1. "poppler-utils not installed"

**Error**: `Unable to get page count. Is poppler installed and in PATH?`

**Solution**: Install poppler system package (see Prerequisites)

#### 2. Vision model not supported

**Error**: `Vision analysis not yet supported for provider: openrouter`

**Solution**: Use a vision-capable provider for Phase 1 (google, anthropic, openai)

#### 3. API key not found

**Error**: `No API key found for GoogleProvider`

**Solution**:
- Check `~/.notebookmaker_config.yaml` exists
- Verify API key is not a placeholder value
- For Google: Can use Application Default Credentials (`gcloud auth application-default login`)

#### 4. Invalid JSON from LLM

**Error**: `LLM returned invalid JSON in chunk X`

**Solution**:
- Check prompt fragments in `prompts/fragments/`
- Try different model (some models better at structured output)
- Reduce chunk size to give more context per chunk

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set in code:

```python
from notebookmaker.analysis import logger
logger.setLevel(logging.DEBUG)
```

## Advanced Topics

### Custom Prompts

Modify analysis behavior by editing prompt fragments:

- `prompts/fragments/analysis_instructions.md` - What to extract
- `prompts/fragments/analysis_output_format.md` - Output structure

### Image Processing

Control image quality vs. token usage:

```python
from notebookmaker.vision import extract_pdf_images

# Higher DPI = better quality, more tokens
images = extract_pdf_images(
    pdf_path,
    chunk_size=10,
    dpi=200  # Default: 150
)
```

### Caching

Analysis results are cached to `<PDF_FILE>.analysis.json`. To regenerate:

```bash
# Force re-analysis
rm lecture.analysis.json
notebookmaker analyze lecture.pdf
```

## Performance

### Typical Processing Times

For a 42-page lecture PDF:

- **PDF to images**: ~30 seconds
- **Phase 1 analysis**: ~2-5 minutes (8-9 API calls)
- **Phase 2 generation**: ~30 seconds (2 API calls)
- **Total**: ~3-6 minutes

### Cost Estimates

Using Google Gemini 2.0 Flash (as of 2024):

- **Phase 1**: ~$0.10-0.20 per 100 pages
- **Phase 2**: ~$0.05-0.10 per notebook
- **Total**: ~$0.20-0.40 per 100-page lecture

## Future Enhancements

Planned features:

- **Interactive mode**: Let user select which sections to include
- **Diagram extraction**: Convert diagrams to matplotlib code
- **Multi-language support**: R, Julia, JavaScript notebooks
- **Slide deck generation**: Create presentation from analysis
- **Web interface**: Browser-based notebook generation

## See Also

- [DESIGN_TWO_PHASE.md](DESIGN_TWO_PHASE.md) - Detailed architecture documentation
- [Project_Progress.md](Project_Progress.md) - Development history
- [.notebookmaker_config.yaml.example](.notebookmaker_config.yaml.example) - Configuration template
