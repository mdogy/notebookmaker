# Output Format

Format your response as **Python code with cell markers** using the percent format.

Use these markers:
* `# %% [markdown]` - Start a markdown cell
* `# %%` - Start a code cell

In markdown cells, prefix each line with `# ` (hash-space).

Example:
```python
# %% [markdown]
# # Introduction
#
# Let's explore this concept with a simple example.

# %%
# This is a code cell
import numpy as np
print('Hello, world!')

# %% [markdown]
# ## Next Section
#
# Here's what we'll do next...

# %%
# More code here
x = 5
y = x * 2
print(f"Result: {y}")
```

**Respond with ONLY the Python code with cell markers, no other text.**
