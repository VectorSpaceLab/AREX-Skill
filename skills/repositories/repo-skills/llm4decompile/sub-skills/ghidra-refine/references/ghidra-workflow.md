# Ghidra Refinement Workflow

This sub-skill covers the repo's `ghidra/` refinement family: extract pseudo-code with the bundled postscript helper, then refine that pseudo-code with an LLM4Decompile V2 checkpoint.

## Route Summary

Use this route when the user wants to:

> **Backend note:** the repository naming is inconsistent here. The folder is named `ghidra`, but the supplied postscript helper uses decompiler-specific APIs. Treat the backend as a matched pair supplied by the user environment and verify it before running.

- run `analyzeHeadless` over a binary,
- collect Ghidra pseudo-code per function,
- convert pseudo-code into the prompt format used by the V2 refinement model,
- run the refinement model on the pseudo-code,
- compare the refined output against the original function or benchmark data.

## Typical two-stage flow

### Stage 1: Ghidra decompilation

- Build or open a binary.
- Run Ghidra in headless mode.
- Use the bundled postscript to write one pseudo-code block per function.
- Keep the function delimiters stable so later parsing can recover the correct function name.

### Stage 2: LLM refinement

- Feed the pseudo-code into the V2 model family.
- Use the same prompt banner as the direct decompilation route, but substitute pseudo-code for raw assembly.
- Save the refined C output and any intermediate logs.

## Key commands and paths

- Headless analyzer binary supplied by the user environment
- Postscript helper: `scripts/dump_pseudo.py`
- Demo / refinement runner: `scripts/run_demo.py`
- Common model family for this route: `LLM4Binary/llm4decompile-6.7b-v2`

## Data format signals

The Ghidra postscript writes output in a simple function-delimited form:

```text
/* function_name @ 0xADDRESS */
<decompiled C text>
```

The demo script converts that output into a prompt of the form:

```text
# This is the assembly code:
<pseudo-code>
# What is the source code?
```

## Read Next

- [`data-formats.md`](data-formats.md)
- [`troubleshooting.md`](troubleshooting.md)
- [`../../../references/model-overview.md`](../../../references/model-overview.md)
