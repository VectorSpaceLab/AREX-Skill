# BringUpBench Workflow

BringUpBench is the long-form evaluation path for SK²Decompile.

## What the benchmark does

- compiles 90 self-contained C programs at O0-O3,
- decompiles each binary with the chosen frontend,
- builds function-level maps across source, pseudo-code, and assembly,
- runs SK²Decompile inference on the mapped functions,
- rebuilds each benchmark in an isolated workspace and runs its tests.

## Key files

- `evaluation/bringupbench/config.env`
- `evaluation/bringupbench/scripts/build-host-opt-levels.sh`
- `evaluation/bringupbench/scripts/decompile-all-pseudo.sh`
- `evaluation/bringupbench/scripts/disasm-all-objdump.sh`
- `evaluation/bringupbench/scripts/build-func-maps.py`
- `evaluation/bringupbench/scripts/eval_infer_out.py`

## Important environment variables

- `BENCH_REPO_ROOT`: path to the upstream BringUpBench checkout
- `IDA_BIN`: decompiler binary used by the source benchmark scripts
- `DEFAULT_TARGET`: usually `host`

## Output layout

The benchmark scripts create per-benchmark JSONL artifacts such as:

- `merged.O0.func_map.jsonl`
- `merged.O1.func_map.jsonl`
- `merged.O2.func_map.jsonl`
- `merged.O3.func_map.jsonl`
- `merged.O0.func_map.infer.jsonl`

The evaluation step also writes per-run JSON and Markdown summaries under a reports directory.

## Decision points

- Use the pre-built function maps when you only want to run the evaluation step.
- Use the full build/decompile/disassembly pipeline when you need to reproduce the whole benchmark from scratch.
- Keep the upstream benchmark checkout separate from the generated skill tree; the skill should only describe how to operate on it.
