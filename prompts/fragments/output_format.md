# Output Format

Format your response as a **JSON list of cells**, where each cell has:

* `"type"`: Either `"markdown"` or `"code"`
* `"content"`: The cell content as a string

Example:
```json
[
  {
    "type": "markdown",
    "content": "# Introduction\n\nLet's explore this concept..."
  },
  {
    "type": "code",
    "content": "# This is a code example\nprint('Hello, world!')"
  }
]
```

**Respond with ONLY the JSON list, no other text.**
