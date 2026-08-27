# Case study patterns

These prompt shapes are distilled from the repository's example analyses. They are meant to help future agents build strong client prompts, not to mirror any single case verbatim.

## Single-file analytical case

Use this when the data lives in one CSV or similar table and the goal is a focused statistical answer.

### Prompt shape

```text
# Instruction
Analyze the file, identify its columns, and answer the research question.

# Data
File 1: {"name": "example.csv", "size": "4.8KB"}
```

### Good habits

- Ask for schema inspection before conclusions.
- Name the target outcome and treatment variables if they are known.
- Ask the model to report missing values, obvious confounders, and any columns that are absent.
- If the column names are uncertain, tell the model to verify them first instead of assuming them.

## Multi-file exploratory case

Use this when a task spans mixed CSV/XLSX files and the analysis must reconcile several inputs.

### Prompt shape

```text
# Instruction
Generate a data science report from the uploaded files.
Inspect all files first, reconcile schema differences, and then summarize the main findings.

# Data
File 1: {"name": "bool.xlsx", "size": "4.8KB"}
File 2: {"name": "person.csv", "size": "10.6KB"}
File 3: {"name": "enrolled.csv", "size": "20.4KB"}
```

### Good habits

- Start with file discovery and column inspection.
- Ask the model to describe each file's role before merging conclusions.
- If a variable does not exist, have the model say so explicitly.
- Keep the file inventory in the prompt even when `thread_id` persists the workspace.

## Two-turn refinement

This is the most common client pattern for follow-up analysis.

### Turn 1

- Attach the relevant `file_ids` to the latest user message.
- Ask for structure, missingness, and first-pass findings.
- Capture the returned `thread_id`.

### Turn 2

- Keep the full conversation history.
- Put the same `file_ids` on the new latest user message when the files are still relevant.
- Put `thread_id` only on the latest user message.
- Ask for a deeper summary, a report, or a new artifact.

### Minimal conversation skeleton

```python
messages = [
    {"role": "user", "content": "Inspect these files first.", "file_ids": file_ids},
]
# after the first reply
messages.append({"role": "assistant", "content": first_reply})
messages.append({
    "role": "user",
    "content": "Now produce a final report.",
    "file_ids": file_ids,
    "thread_id": thread_id,
})
```

## What to tell the model

For this repo, the safest client prompts usually say:
- inspect the file structure first
- generate code only when needed
- write outputs into the active workspace
- return a final report plus any useful artifacts

That keeps the conversation aligned with the runtime contract and the generated file reporting flow.
