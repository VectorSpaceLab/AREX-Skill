# Programming Workflows

## Source-code project analysis

GPT Academic has language-specific project analysis plugins for Python, Java, C/C++, Go, Rust, Lua, CSharp, Matlab, and frontend stacks. The workflow traverses source files, sends per-file summaries to the model, then performs iterative aggregation into an architecture report and often a Mermaid-style structure diagram.

Before running:

1. Exclude vendor/cache/build directories such as `.git`, `node_modules`, `__pycache__`, large generated outputs, minified bundles, model weights, and datasets.
2. Keep the file count under the practical limit (docs mention a default protection around 512 files).
3. Choose a stronger model for complex architecture or framework-specific projects.
4. Use manual patterns for mixed-language repos or unusual suffixes.

## Python docstrings and batch comments

`注释Python项目` and batch comment workflows use LLM calls to identify functions and add comments/docstrings. They are write-oriented.

Safe procedure:

1. Require a backup, copy, or clean version-control state.
2. Scope to a small directory first.
3. Review generated changes before applying broadly.
4. Preserve indentation and avoid translating/changing non-comment code.

## Jupyter Notebook analysis

Use notebook analysis when the input is `.ipynb` and the user wants a narrative explanation of cells, dependencies, or experimental flow. If notebooks include large outputs, advise clearing outputs or focusing on selected cells to save tokens.

## Markdown and README translation

Use Markdown translation when preserving headings, code fences, tables, and links matters. For technical repos, warn that API names, code blocks, formula syntax, and path strings should not be translated unless the user requests it.
