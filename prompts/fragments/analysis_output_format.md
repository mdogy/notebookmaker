# Analysis Output Format

Output your analysis as **valid JSON** matching this exact structure:

```json
{
  "lecture_title": "Title of the Lecture",
  "total_pages": 42,
  "sections": [
    {
      "section_id": "unique_identifier",
      "title": "Human-Readable Section Title",
      "pages": [1, 2, 3],
      "has_code": true,
      "code_snippets": [
        {
          "code": "import numpy as np\nprint('Hello')",
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
      "priority": 8
    }
  ],
  "metadata": {
    "author": "Instructor Name",
    "course": "Course Code",
    "date": "YYYY-MM-DD"
  }
}
```

## Field Descriptions

- **lecture_title** (string): Title of the lecture
- **total_pages** (integer): Total number of pages in this chunk/document
- **sections** (array): List of identified sections
  - **section_id** (string): Snake_case unique ID (e.g., `coin_flip_example`)
  - **title** (string): Display title (e.g., "Coin Flip Example")
  - **pages** (array of integers): Page numbers (1-indexed)
  - **has_code** (boolean): `true` if executable code present, `false` otherwise
  - **code_snippets** (array): Code blocks found
    - **code** (string): The actual code
    - **language** (string): "python", "r", "julia", etc.
    - **line_number** (integer or null): Optional line reference
  - **equations** (array): Mathematical equations
    - **latex** (string): LaTeX representation
    - **description** (string or null): Brief explanation
  - **concepts** (array of strings): Key concepts (2-4 words each)
  - **dependencies** (array of strings): Other section_ids this depends on
  - **priority** (integer 1-10): Importance for inclusion (10 = critical)
- **metadata** (object): Optional metadata about the lecture

## Important

- Output **only valid JSON**, no markdown code blocks, no extra text
- Escape special characters properly (quotes, backslashes, newlines)
- Use `null` for optional fields that are empty
- Ensure all brackets and braces are balanced
- Arrays can be empty `[]` if nothing found
