---
name: fx-graph-workflows
description: "Operate Optimum Torch FX graph transformations and version-gated
  tensor parallelism guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# fx-graph-workflows

Use this sub-skill when a task involves Optimum's Torch FX graph workflow surface:

- CPU-compatible graph rewrites from `optimum.fx.optimization`.
- Custom `Transformation` / `ReversibleTransformation` classes, `compose(...)`, and `reverse=True` restoration.
- GraphModule lint/recompile behavior and computation-preserving validation.
- Cautious triage for optional automatic tensor parallelism from `optimum.fx.parallelization`.

Do **not** use this sub-skill for GPTQ quantization, exporter task mapping, CLI export commands, dummy inputs, or normalized configs. Route those to the generated `gptq-quantization`, `exporters-and-cli`, or `utilities-and-configs` sub-skills.

## Linked runtime files

- [references/fx-optimization.md](references/fx-optimization.md) — transformation APIs, GraphModule expectations, built-in transformations, compose/reverse behavior, and local validation patterns.
- [references/tensor-parallelism.md](references/tensor-parallelism.md) — optional automatic tensor-parallel API map, backend/version gates, layer replacements, and safe triage.
- [references/troubleshooting.md](references/troubleshooting.md) — common failures and recoveries for FX imports, graph mutation, preservation checks, native-test downloads, Python 3.11 tensor-parallel import errors, and CUDA/NCCL requirements.
- [scripts/fx_transform_smoke.py](scripts/fx_transform_smoke.py) — deterministic CPU smoke test adapted from transformation behavior tests using only a tiny local `torch.nn.Module`.

## Operating sequence

1. Confirm the user is asking for FX graph transformations or tensor-parallel triage, not export/quantization/config utilities.
2. For optimization work, require a `torch.fx.GraphModule` or trace a local `torch.nn.Module` into one. Keep inputs local and deterministic; avoid Hub downloads unless the user explicitly authorizes them.
3. Read [references/fx-optimization.md](references/fx-optimization.md) before changing a graph. Apply transformations with default lint/recompile unless batching a compose chain.
4. Run the bundled smoke test when validating the local environment:

   ```bash
   python scripts/fx_transform_smoke.py
   python scripts/fx_transform_smoke.py --check-compose
   ```

5. For tensor parallelism, read [references/tensor-parallelism.md](references/tensor-parallelism.md) first. Treat it as optional/advanced unless the environment has a compatible Python, CUDA-capable PyTorch with `torch.compile`, initialized distributed/NCCL process groups, and enough GPUs for the requested world size.
6. Use [references/troubleshooting.md](references/troubleshooting.md) whenever import, graph lint/recompile, preservation, reverse, or backend errors appear.
