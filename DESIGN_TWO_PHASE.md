# Two-Phase Architecture Design

## Overview

NotebookMaker now uses a **two-phase architecture** to address three critical issues:

1. **Problem 1**: Current notebooks have too much narrative text (not code-focused)
2. **Problem 2**: Images contain equations, code screenshots, and diagrams that text extraction misses
3. **Problem 3**: Token limits (input and output) prevent processing large PDFs in one call

## Architecture

### Phase 1: Multimodal Analysis (Vision LLM)

**Purpose**: Extract structured information about what content is code-worthy.

**Input**: PDF file (processed in chunks)

**Process**:
1. Convert PDF pages to images (5-10 pages per chunk)
2. Send images to multimodal LLM with analysis prompt
3. LLM extracts:
   - Sections/slides with executable code examples
   - Code snippets (from images or text)
   - Equations (as LaTeX)
   - Conceptual flow and dependencies
4. Aggregate chunk analyses into single `analysis.json`

**Output**: `analysis.json` with structure:
```json
{
  "lecture_title": "Hypothesis Testing",
  "sections": [
    {
      "section_id": "coin_flip_simulation",
      "title": "Simulating Coin Flips",
      "pages": [5, 6],
      "has_code": true,
      "code_snippets": [
        "import numpy as np\nflips = np.random.randint(0, 2, size=(10000, 100))"
      ],
      "equations": [
        "p = \\frac{n_{heads}}{n_{total}}"
      ],
      "concepts": ["simulation", "probability", "randomness"]
    },
    {
      "section_id": "introduction",
      "title": "What is Hypothesis Testing?",
      "pages": [1, 2, 3],
      "has_code": false,
      "concepts": ["a priori reasoning", "a posteriori reasoning"]
    }
  ],
  "dependencies": {
    "coin_flip_simulation": [],
    "permutation_test": ["coin_flip_simulation"]
  }
}
```

**Token Management**:
- Input: 5-10 pages as images (~5,000 tokens per chunk)
- Output: Compact JSON (~500-1000 tokens per chunk)
- Total for 42-page PDF: ~8-9 API calls, ~4,500 output tokens total

### Phase 2: Notebook Generation (Text or Vision LLM)

**Purpose**: Generate Jupyter notebooks focusing only on code-heavy content.

**Input**: `analysis.json` (compact, ~5KB for 42-page PDF)

**Process**:
1. Filter sections where `has_code: true`
2. Generate cells for each code section:
   - Markdown: Brief introduction with equations
   - Code: Working example (instructor) or incomplete (student)
3. Use extracted code snippets as starting point
4. Include LaTeX equations in markdown cells

**Output**: Instructor and student `.ipynb` files

**Token Management**:
- Input: ~5KB analysis JSON (~2,000 tokens)
- Output: Notebook in percent format (~10,000 tokens)
- Single API call per notebook (or chunked by section if needed)

## Configuration

### Two-LLM Setup

Users can configure different LLMs for each phase:

```yaml
# ~/.notebookmaker_config.yaml

# Phase 1: Analysis (requires vision capabilities)
analysis:
  provider: "google"  # or "anthropic", "openai"
  model: "gemini-2.0-flash-exp"  # has vision
  max_tokens: 2000

# Phase 2: Generation (can use text-only or vision)
generation:
  provider: "anthropic"
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 16000
```

### Supported Vision Models

| Provider | Model | Vision? | Notes |
|----------|-------|---------|-------|
| Anthropic | claude-3-5-sonnet-20241022 | ✅ | Best for analysis |
| Anthropic | claude-3-5-haiku-20241022 | ✅ | Fast, cheaper |
| Google | gemini-2.0-flash-exp | ✅ | Good balance |
| Google | gemini-1.5-pro | ✅ | High quality |
| OpenAI | gpt-4o | ✅ | Excellent vision |
| OpenAI | gpt-4o-mini | ✅ | Cheaper option |

## Implementation Plan

### Dependencies

Add to `pyproject.toml`:
```toml
dependencies = [
    # ... existing ...
    "Pillow>=10.0.0",      # Image processing
    "pdf2image>=1.16.0",   # PDF → images (requires poppler)
]
```

System requirement: `poppler-utils` (for pdf2image)

### New Modules

1. **`src/notebookmaker/analysis.py`**
   - `extract_pdf_images(pdf_path, chunk_size=10) -> List[List[Image]]`
   - `analyze_chunk(images, provider, model) -> Dict`
   - `aggregate_analyses(chunk_results) -> Dict`
   - `save_analysis(analysis, output_path)`

2. **`src/notebookmaker/vision.py`**
   - `encode_image_base64(image) -> str`
   - `create_vision_message(images, prompt) -> Message`
   - Vision-specific LLM provider wrappers

3. **Update `src/notebookmaker/utils.py`**
   - Modify `generate_notebook()` to accept analysis JSON
   - Add `filter_code_sections(analysis) -> List[Section]`

### Prompts

1. **`prompts/analysis_prompt.md`**
   - Instructions for vision LLM to extract structured data
   - Focus on: code presence, equations, concepts
   - Output schema specification

2. **Update `prompts/fragments/`**
   - Add filtering instructions: "Only create cells for executable code"
   - Add equation rendering instructions (LaTeX in markdown)

## CLI Changes

### New Workflow

```bash
# Phase 1: Analyze PDF
notebookmaker analyze lecture.pdf -o analysis.json

# Phase 2: Generate notebooks from analysis
notebookmaker generate analysis.json -o outputs/

# Or combined (automatic two-phase):
notebookmaker lecture.pdf -o outputs/
```

### New Options

```
--analysis-provider    LLM provider for analysis phase
--analysis-model       Model for analysis phase
--generation-provider  LLM provider for notebook generation
--generation-model     Model for notebook generation
--chunk-size          Pages per analysis chunk (default: 10)
--save-analysis       Save intermediate analysis.json
```

## Migration Strategy

1. **Keep existing single-phase workflow** for backwards compatibility
2. **Add opt-in two-phase workflow** with `--enable-vision` flag
3. **Make two-phase default** in future version after testing

## Benefits

### Quality Improvements

- ✅ **Code-focused**: Only sections with executable examples
- ✅ **Equations preserved**: LaTeX from images
- ✅ **Code from screenshots**: Vision extracts code text
- ✅ **Better filtering**: Narrative-only slides excluded

### Technical Improvements

- ✅ **Token efficiency**: Analysis is compact
- ✅ **Handles large PDFs**: Chunked processing
- ✅ **Debuggable**: `analysis.json` is human-readable
- ✅ **Flexible**: Can re-generate notebooks without re-analyzing

## Testing Plan

1. Test with `examples/L12-HypothesisTesting.pdf`:
   - Verify code sections identified correctly
   - Check equation extraction from images
   - Validate token usage stays within limits

2. Test with large PDF (100+ pages):
   - Verify chunking works
   - Check aggregation correctness
   - Monitor API costs

3. Compare outputs:
   - Old (text-only) vs. New (vision-based)
   - Measure: code density, equation accuracy, relevance

## Future Enhancements

- **Caching**: Save analyses to avoid re-processing
- **Interactive mode**: Let user select which sections to include
- **Diagram extraction**: Convert diagrams to code (matplotlib)
- **Multi-language**: Support R, Julia, etc.
