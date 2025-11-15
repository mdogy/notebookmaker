# NotebookMaker Project Progress

**Last Updated**: 2025-11-14

## 📊 Project Status Overview

### ✅ **COMPLETED - Core Architecture (100%)**

The foundational architecture is complete and functional.

1.  **LLM Infrastructure** ✅
    -   Unified provider interface for Anthropic, Google, OpenAI, and OpenRouter.
    -   Secure credential management (`~/.notebookmaker_config.yaml` + environment variables).
    -   Full type safety with Pydantic models and strict mypy checking.

2.  **Two-Phase Pipeline** ✅
    -   **Phase 1: Analysis**: A vision-capable LLM analyzes the PDF in chunks, extracting sections, code (from text and images), equations, and concepts into a structured JSON file.
    -   **Phase 2: Generation**: A second LLM uses the analysis JSON to generate code-focused instructor and student notebooks.
    -   This architecture solves major limitations of the previous single-pass approach, including handling visual content and avoiding token limits.

3.  **Pydantic Data Models** ✅
    -   `LectureAnalysis`, `Section`, `CodeSnippet`, and `Equation` models provide a robust, validated structure for data passed between Phase 1 and Phase 2.

4.  **Prompt Engineering** ✅
    -   Modular prompt system with fragments for both analysis and generation phases.
    -   Prompts are stored as external `.md` files for easy editing and experimentation.

5.  **CLI Interface** ✅
    -   Updated CLI (`cli.py`) supports the two-phase workflow.
    -   Separate controls for analysis and generation providers/models (`--analysis-provider`, `--generation-model`, etc.).
    -   Options to control generation logic, such as `--min-priority`.

### 🚧 **IN PROGRESS - Testing and Documentation**

1.  **Testing** (Medium Priority) - Not Started
    -   Unit tests for `analysis.py`, `generation.py`, and `vision.py`.
    -   Integration tests for the full two-phase pipeline.
    -   Target: 80%+ code coverage.

2.  **Documentation Updates** (Low Priority) - Partially complete
    -   Update `README.md` with new usage instructions for the two-phase CLI.
    -   Document the `LectureAnalysis` JSON format.
    -   Update `AGENTS.md` to reflect the new architecture.

### 🎯 **Recommended Next Steps**

With the core two-phase architecture now implemented, the highest priority is to build a comprehensive test suite to ensure reliability and prevent regressions.

1.  **Write Unit Tests**: Create `pytest` tests for the key functions in `analysis.py`, `generation.py`, and `vision.py`.
2.  **Write Integration Tests**: Build a test that runs the full `process_lecture` pipeline on an example PDF and verifies the outputs (analysis JSON and notebooks).
3.  **Update Documentation**: Ensure the `README.md` and other documentation files are updated to reflect the new CLI commands and workflow.

---

## 📈 Development Metrics

-   **Lines of Code**: ~2,000 (src/)
-   **Test Coverage**: Not yet measured
-   **Type Coverage**: 100% (mypy strict mode)
-   **Linting**: 100% (ruff passing)
-   **Dependencies**: 10 core, 5 dev

---

## Appendix: Project History

### Evolution from `[previous]` → `[current]` (2025-11-14)

**From**: Single-phase, text-only pipeline
**To**: Two-phase, vision-enabled analysis-generation architecture

**What Changed Between Commits**:

This commit fundamentally refactors the application from a simple text-extraction pipeline to a sophisticated two-phase architecture. This addresses the critical limitations of the previous approach, which could not handle visual content (like code in images) and was prone to hitting LLM token limits.

**Key Changes**:

1.  **Architecture Split**:
    -   **Phase 1: Analysis**: A new `analysis.py` module uses a vision-capable LLM (via `vision.py`) to analyze the source PDF. It processes the document in chunks, identifies logical sections, and extracts code, equations, and concepts into a structured `LectureAnalysis` JSON file.
    -   **Phase 2: Generation**: A new `generation.py` module takes the `LectureAnalysis` JSON as input and uses an LLM to generate code-focused notebooks, respecting dependencies and priorities defined in the analysis.

2.  **New Modules**:
    -   `src/notebookmaker/analysis.py`: Orchestrates the Phase 1 analysis.
    -   `src/notebookmaker/vision.py`: Handles multimodal LLM calls for analyzing PDF pages.
    -   `src/notebookmaker/generation.py`: Manages the Phase 2 notebook generation.

3.  **Pydantic Models (`models.py`)**:
    -   Introduced `LectureAnalysis`, `Section`, `CodeSnippet`, and `Equation` to formally define the data structure passed between the two phases. This ensures type safety and runtime validation.

4.  **Pipeline Rewrite (`utils.py`)**:
    -   `process_lecture` was completely rewritten to be a high-level orchestrator of the two-phase workflow. It now calls `analyze_pdf` followed by `generate_notebook_from_analysis`.
    -   The old text-extraction and single-pass generation logic has been removed.

5.  **CLI Overhaul (`cli.py`)**:
    -   The command-line interface was redesigned to support the new architecture.
    -   Users can now specify different providers and models for the analysis and generation phases (e.g., `--analysis-provider`, `--generation-model`).
    -   New options like `--min-priority` and `--chunk-size` provide finer control over the process.

6.  **New Prompt Fragments**:
    -   **Analysis**: `analysis_instructions.md`, `analysis_output_format.md`.
    -   **Generation**: `generation_instructions.md`, `instructor.md`, `student.md`.

**Why This Evolution Matters**:

This is the most significant architectural change in the project's history. It elevates NotebookMaker from a simple script to a robust content processing system.

-   **Handles Visuals**: Can now extract code from screenshots and properly formatted equations.
-   **Scalability**: By processing PDFs in chunks, it can handle documents of any length without hitting token limits.
-   **Higher Quality Output**: Notebooks are generated from a pre-analyzed, structured summary, leading to more relevant, code-focused content and less verbose narrative.
-   **Modularity & Reusability**: The analysis phase produces a reusable `analysis.json` file, which can be used to generate different kinds of notebooks or other materials without re-analyzing the source PDF.

**Migration Impact**:

-   The CLI is not backward-compatible. Users must adapt to the new flags (`--analysis-provider`, etc.).
-   The workflow now produces an intermediate `.analysis.json` file, which is cached for subsequent runs.

---
### Evolution from `01e96de` → `[previous]` (2025-11-14)

**From**: Percent-format prompts with JSON parsing issues
**To**: Working end-to-end pipeline generating Jupyter notebooks

**What Changed Between Commits**:

The previous commit implemented prompt fragments but still requested JSON output from the LLM, which led to parsing failures. This commit completes the full pipeline by switching to percent-formatted Python output and implementing the main `process_lecture()` orchestration.

**Key Changes**:

1. **Output Format Refactoring** (`prompts/fragments/output_format.md`):
   - **Before**: Requested JSON array with `{"type": "markdown", "content": "..."}` objects
   - **After**: Requests percent-formatted Python with `# %% [markdown]` and `# %%` markers
   - Why: LLMs excel at generating Python code; JSON string escaping is error-prone
   - Example format matches VSCode/PyCharm/Spyder cell conventions

2. **Parser Rewrite** (`utils.py:_parse_llm_response_to_notebook`):
   - Completely replaced JSON parsing with line-by-line percent-format parsing
   - Handles markdown code block wrapping automatically
   - Strips `# ` prefix from markdown cell lines
   - No JSON escaping issues, no quote/newline problems
   - Robust error handling: creates error notebook if parsing fails

3. **Pipeline Implementation** (`utils.py:process_lecture`):
   - Orchestrates full workflow: PDF/PPTX → content → LLM → notebooks
   - Extracts content using `extract_pdf_content()` or `extract_powerpoint_content()`
   - Generates both instructor and student notebooks in single run
   - Auto-increments filenames if outputs already exist (e.g., `_instructor1.ipynb`)
   - Validates input file exists and has supported extension
   - Returns dictionary with paths to both generated notebooks

4. **CLI Enhancements** (`cli.py`):
   - Added `--provider` / `-p` option to select LLM provider
   - Added `--model` / `-m` option to override default model
   - Improved output messaging with clear status updates
   - Returns proper exit codes

**Why This Evolution Matters**:

This commit transforms NotebookMaker from "infrastructure with failing output" to **a working end-to-end system**. The switch from JSON to percent-formatted Python was the critical breakthrough:

- **Reliability**: No more JSON parsing errors from LLM responses
- **Natural for LLMs**: Python code generation is what they do best
- **Standard format**: Percent format is already used by major IDEs
- **Token efficiency**: Less overhead than JSON structure
- **Human readable**: Intermediate format can be inspected/debugged

**Testing Results**:

Tested on `examples/L12-HypothesisTesting.pdf` (42 pages, 5,903 characters):
- **Instructor notebook**: 14 cells generated successfully (12KB file)
- **Student notebook**: 13 cells generated successfully (14KB file)
- Both notebooks contain proper markdown explanations and code examples
- Process completed in ~45 seconds using Google Gemini

**Design Decisions**:

1. **Percent format over JSON**: Based on analysis of options (A-F), chose established IDE format that LLMs handle naturally
2. **Single LLM call per notebook**: Rather than chunking, let LLM see full context
3. **Auto-incrementing filenames**: Prevents accidental overwrites while allowing multiple runs
4. **Provider/model CLI options**: Gives users flexibility without editing config files

**Migration Impact**:

For users: The pipeline now works! Generated notebooks are production-ready.

For developers: The percent-format parser in `_parse_llm_response_to_notebook()` is simpler and more maintainable than JSON parsing. Future prompt improvements won't fight JSON escaping issues.

---

### Evolution from `01e96de` (previous) → `01e96de` (2025-11-14)

**From**: Hardcoded LLM prompts in code
**To**: Fragment-based prompt template system

**What Changed Between Commits**:

The previous implementation had notebook generation prompts hardcoded as f-strings directly in the `_create_notebook_prompt()` function. This commit refactors the entire prompt system to use a modular, fragment-based architecture.

**Key Additions**:

1. **Prompt Fragments** (`prompts/fragments/`):
   - `role.md` - Defines the instructor persona for the LLM
   - `notebook_structure.md` - Specifies the Markdown → Code cell pattern
   - `student_version.md` - Guidelines for creating incomplete code with `....` markers
   - `instructor_version.md` - Requirements for complete, runnable code
   - `tone.md` - Conversational style guidelines
   - `output_format.md` - JSON response format specification

2. **Template Files** (`prompts/`):
   - `student_notebook_template.md` - Assembles student-specific fragments
   - `instructor_notebook_template.md` - Assembles instructor-specific fragments
   - Both use `{placeholder}` syntax for fragment injection

3. **Prompt Loading System** (`utils.py`):
   - `_load_prompt_fragment()` - Loads and processes individual fragment files
   - `_create_notebook_prompt()` - Completely refactored to:
     * Load the appropriate template based on notebook_type
     * Load all required fragments
     * Replace placeholders with fragment content
     * Return assembled prompt

4. **Type Safety Improvements**:
   - Added TYPE_CHECKING guard for nbformat import
   - Runtime validation of provider parameter with cast to Literal type
   - Added type: ignore comments for untyped nbformat calls
   - Updated pyproject.toml to ignore missing imports for nbformat, pypdf, pptx, tiktoken

**Why This Evolution Matters**:

This refactoring addresses a critical design flaw identified by the user: prompts should be **editable text files**, not hardcoded strings in Python. The new architecture provides several benefits:

- **Maintainability**: Prompt engineering happens in markdown files, not Python code
- **Experimentation**: Try different prompt variations without code changes
- **Reusability**: Fragment composition allows mixing and matching components
- **Separation of Concerns**: LLM instructions (prompts) are separate from orchestration logic (code)
- **Version Control**: Prompt changes are tracked independently of code changes

---

### Evolution from `b52f945` → `[previous]` (2025-11-14)

**From**: Documentation standards with no content extraction
**To**: Working PDF and PowerPoint extraction

**What Changed Between Commits**:

The previous commit (`b52f945`) finalized the development guidelines and documentation standards. This commit implements the first major application feature: document content extraction.

**Key Additions**:

1. **Dependencies** (`pyproject.toml`):
   - Added `pypdf>=4.0.0` for PDF text extraction
   - Added `python-pptx>=0.6.23` for PowerPoint slide extraction
   - Added `nbformat>=5.9.0` for Jupyter notebook generation (future use)
   - All dependencies installed and verified working

2. **PDF Extraction** (`utils.py:extract_pdf_content`):
   - Implemented complete PDF text extraction using pypdf
   - Page-by-page extraction with clear page markers (`--- Page N ---`)
   - Proper error handling (FileNotFoundError, ValueError)
   - Type-safe with full mypy compliance
   - Tested on 42-page lecture PDF (5,903 characters extracted)

3. **PowerPoint Extraction** (`utils.py:extract_powerpoint_content`):
   - Implemented complete PPTX text extraction using python-pptx
   - Slide-by-slide extraction with slide markers (`--- Slide N ---`)
   - Extracts all text from shapes on each slide
   - Same error handling and type safety as PDF extraction
   - Supports both .ppt and .pptx formats

**Why This Evolution Matters**:

This commit transforms NotebookMaker from "infrastructure only" to "can process lecture materials." The extraction functions are the **foundation of the entire pipeline** - without them, we can't get content to send to the LLM.

---

### Evolution from `d39d7bc` → `601f883` (2025-11-14)

**From**: LLM infrastructure with `.env` file support
**To**: YAML-based configuration in user's home directory

**What Changed Between Commits**:

The previous commit (`d39d7bc`) had implemented a working LLM layer, but it relied on `.env` files in the project directory for API key storage. This commit completely replaced that approach with a more secure and user-friendly YAML configuration system.

---

### Evolution from `5076402` → `d39d7bc` (2025-11-14)

**From**: Empty project with configuration files
**To**: Working LLM integration layer

**What Changed Between Commits**:

The initial commit (`5076402`) set up the project structure, development guidelines, and tooling configuration, but contained no actual application code. This commit added the entire LLM integration layer.

---

### Commit: `5076402` - Initial commit: project configuration (2025-11-14)

**What Was Created**:

The foundation for a high-quality Python project with strict development standards.