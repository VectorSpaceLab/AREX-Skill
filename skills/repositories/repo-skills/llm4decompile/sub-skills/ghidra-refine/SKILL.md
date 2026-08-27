---
name: ghidra-refine
description: "Extract pseudo-code with Ghidra and refine it with the
  LLM4Decompile V2 model family."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Ghidra Refinement

Use this sub-skill when the user wants to run the repo's refinement path: extract per-function pseudo-code with the bundled decompiler postscript and feed that pseudo-code into a V2 refinement model.

## Covers

- headless extraction with the repo's bundled postscript helper
- pseudo-code dump parsing and prompt construction
- V2 refinement using `LLM4Binary/llm4decompile-6.7b-v2` or related V2 checkpoints
- demo-style compile → extract → refine loops

## Excludes

- direct assembly-only inference and benchmark scoring → use `evaluation`
- training or dataset preparation → use `training`
- SK²Decompile RL or BringUpBench → use `sk2decompile`

## Start Here

1. Read [`references/ghidra-workflow.md`](references/ghidra-workflow.md) for the two-stage flow.
2. Read [`references/data-formats.md`](references/data-formats.md) before changing the pseudo-code dump or prompt shape.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) if Java, Ghidra, or the model selection fails.
4. Use the bundled scripts in this sub-skill's `scripts/` directory rather than the source checkout.

## Common routes

### Pseudo-code extraction

Use this route when the user needs the raw Ghidra output or wants to batch decompile a binary.

Good entry points:

- `scripts/dump_pseudo.py`
- `scripts/run_demo.py`

### V2 refinement

Use this route when the user already has pseudo-code and wants the model to improve readability or syntax.

Good entry points:

- `scripts/run_demo.py`

## Environment signals

- Java 17 may be required by the surrounding demo flow, depending on the headless backend the user actually has installed.
- The repo's example scripts mix Ghidra naming with decompiler-specific postscript APIs; verify the backend pair before running.
- `clang-format` is needed when pseudo-code normalization is part of the flow.
- The V2 model family is the normal target for refinement.

## When to read the bundled references

- Use the workflow reference for the stage ordering and file expectations.
- Use the data-format reference to preserve the function delimiters and prompt wrapper.
- Use the troubleshooting reference when Ghidra or the refinement model fails.
