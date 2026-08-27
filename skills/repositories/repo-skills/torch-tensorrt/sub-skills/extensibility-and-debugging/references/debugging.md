# Debugging Workflows

## Dryrun and coverage analysis

Use dryrun or compile analysis to answer: "What parts of my model will become TensorRT engines?"

Recommended steps:

1. Start from a tiny representative input.
2. Use `dryrun=True` or the package's debug/analysis mode if the installed version exposes it.
3. Inspect which ops are assigned to TensorRT and which remain in PyTorch.
4. If coverage is too small, lower `min_block_size` carefully or rewrite the model.
5. If the model must be all TensorRT, set `require_full_compilation=True` to make gaps fail early.

## `Debugger`

`torch_tensorrt.dynamo.Debugger(...)` captures:

- FX graphs before/after selected phases.
- Engine build/profile artifacts.
- Layer information.
- Build monitoring and logging directories.

Use it when the user needs a high-quality repro or wants to compare graph state before and after partitioning.

## Minimal repro recipe

A good repro usually includes:

- model definition or a tiny substitute,
- exact input shapes/dtypes/layout,
- compile settings,
- whether fallback is allowed,
- error text or unexpected output,
- package versions and feature gates.

## Capture/replay output checklist

If the user wants issue-quality evidence, collect:

- the generated FX graph or summary,
- the partitioned subgraph boundaries,
- a note of unsupported ops and their schemas,
- engine build errors or warnings,
- whether the model works when fallback is allowed.

## How to decide next

| Debug result | Next action |
| --- | --- |
| Unsupported op is a one-off and fallback is acceptable | Keep PyTorch fallback or raise `torch_executed_ops` for only the needed ops. |
| Unsupported op is performance-critical | Consider model rewrite or converter/plugin extension. |
| Many ops are unsupported because of layout/dtype | Adjust inputs or model format first. |
| Dryrun says coverage is good but runtime fails | Switch to runtime optimization or deployment troubleshooting. |
