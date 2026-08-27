# Evaluation Data Formats

## Direct evaluation JSON

The repo's direct-evaluation datasets use JSON lists. Common fields include:

- `task_id`: benchmark identifier,
- `type`: optimization level such as `O0`, `O1`, `O2`, or `O3`,
- `c_func`: reference C implementation,
- `c_test`: executable test harness,
- `input_asm_prompt`: assembly prompt or Ghidra-derived pseudo-code prompt,
- `opt`: optimization tag used by benchmark scripts,
- `language`: usually `c` or `cpp`,
- `asm`, `ida_asm`, `ida_pseudo`, `ghidra_asm`, `ghidra_pseudo`: optional benchmark-specific fields.

## Decompile-Bench JSON

The benchmark dataset described in `decompile-bench/readme.md` uses entries with:

- `name`
- `code`
- `asm`
- `file`

The evaluation JSON variant also carries `func_name`, `func_dep`, `func`, `test`, `opt`, and `language` fields.

## Output layout

The direct benchmark scripts usually write a directory tree keyed by optimization level:

```text
<output-root>/
  O0/
  O1/
  O2/
  O3/
```

The files inside those directories use the benchmark index and language extension.

## Prompt generation rules

- Strip or preserve includes consistently across the function body and tests.
- Keep the `# This is the assembly code:` and `# What is the source code?` markers stable.
- Make sure the prompt text matches the model family: direct assembly for V1.5, pseudo-code for V2/Ghidra routes.

## Validation checks

Before launching a long inference or benchmark run, verify:

1. The model path resolves to a local checkpoint or a reachable hub id.
2. The dataset JSON contains the fields expected by the chosen script.
3. The output directory is writable and empty enough for the planned run.
4. The compiler toolchain is present if re-executability metrics will run.
