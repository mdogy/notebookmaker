# Analysis Instructions

Your task is to analyze lecture slides/pages and extract **structured information** about code-worthy content.

## Goals

1. **Identify executable code sections** - Focus on parts with actual code examples, not just theory
2. **Extract code and equations** - Capture code snippets and mathematical equations from images
3. **Determine priorities** - Rate how essential each section is for hands-on learning
4. **Track dependencies** - Note which sections build on earlier material

## What to Look For

### High Priority Sections (7-10):
- Working code examples with actual implementation
- Simulations or data analysis demonstrations
- Algorithm implementations
- Interactive visualizations
- Code that students should run and modify

### Medium Priority Sections (4-6):
- Code snippets that illustrate a concept
- Short examples showing syntax
- Setup/configuration code
- Helper functions

### Low Priority Sections (1-3):
- Pure theory with no executable code
- Definitions and conceptual explanations
- Background information
- Literature reviews

## Code Extraction

When you find code in images:
- Extract the complete code as text
- Preserve indentation and structure
- Note the programming language
- Include comments if visible

## Equation Extraction

When you find equations in images:
- Convert to LaTeX notation
- Add a brief description of what it represents
- Examples:
  - `p = \frac{n_{heads}}{n_{total}}` (proportion of heads)
  - `H_0: p = 0.5` (null hypothesis)

## Section Structure

For each section you identify, provide:
- **section_id**: Unique snake_case identifier (e.g., `coin_flip_simulation`)
- **title**: Human-readable title (e.g., "Simulating Coin Flips")
- **pages**: Page numbers where this appears (e.g., `[5, 6]`)
- **has_code**: `true` if there's executable code, `false` otherwise
- **code_snippets**: List of code blocks found
- **equations**: List of mathematical equations
- **concepts**: Key concepts (brief, 2-4 words each)
- **dependencies**: Other section_ids this depends on
- **priority**: 1-10 rating for inclusion in notebook

## Guidelines

- **Be selective**: Only mark `has_code: true` if there's actual executable code
- **Avoid narrative**: Don't extract long text explanations
- **Focus on exercises**: Prioritize content students should run/experiment with
- **Think practically**: Would a student learn by running this code?
