# Evaluation Workflows

This sub-skill covers direct decompilation inference and benchmark scoring for the LLM4Decompile family.

## Route Summary

Use this route when the user wants to:

- generate C from assembly prompts,
- run the vLLM or text-generation-inference evaluation paths,
- score outputs with compile/run or edit-similarity metrics,
- compare model outputs against HumanEval-Decompile, MBPP, or Decompile-Bench style datasets,
- inspect the legacy single-GPU path without using it as the primary route.

## Main evaluation modes

### vLLM inference + benchmark scoring

This is the recommended direct path in the repository README.

Typical shape:

```bash
python evaluation/scripts/run_vllm_eval.py \
  --model_path <local-or-hf-model> \
  --testset_path <dataset.json> \
  --output_path <predictions-dir> \
  --gpus 8 \
  --max_total_tokens 8192 \
  --max_new_tokens 512
```

Use this route for the normal GPU inference and re-executability workflow.

### Text-generation-inference (TGI) path

The repo also includes a server-backed path that launches a text-generation server and queries it asynchronously.

Use this route when the user already relies on the TGI stack or wants a multi-process server/client split.

### Benchmark-only metric computation

If predictions already exist, the metric helpers can compute:

- compile/run success rates,
- edit similarity,
- per-optimization-level summaries.

## Benchmark families

- **HumanEval-Decompile**: standard-C function recovery with assertions.
- **MBPP**: additional function-recovery benchmark data.
- **Decompile-Bench**: large benchmark and evaluation set with C/C++ support.
- **ExeBench / legacy test data**: older or historical evaluation examples; use them as context, not as the primary route.

## Prompt shape

Direct evaluation expects the familiar repo prompt:

```text
# This is the assembly code:
<assembly or pseudo-code>
# What is the source code?
```

The v2/Ghidra-related prompt shapes are handled in the `ghidra-refine` sub-skill instead.

## Read Next

- [`data-formats.md`](data-formats.md)
- [`benchmark-catalog.md`](benchmark-catalog.md)
- [`troubleshooting.md`](troubleshooting.md)
- [`../../../references/model-overview.md`](../../../references/model-overview.md)
