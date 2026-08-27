---
name: model-summary-usage
description: "Use torchsummary.summary and torchsummary.summary_string to
  inspect PyTorch nn.Module shapes, parameter counts, devices, dtypes, and
  memory estimates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# model-summary-usage

Use this sub-skill when a task needs to call `torchsummary.summary` or
`torchsummary.summary_string` for a PyTorch `nn.Module` without reopening the
source repository.

## Read this when

- You need a Keras-style printed summary table for a PyTorch model.
- You need programmatic total/trainable parameter counts from `summary_string`.
- The model has one input, multiple inputs, or per-input dtype requirements.
- A summary run is failing because of CPU/CUDA placement, dtype, input-size, or
  shape issues.
- You need to decide whether this lightweight package is enough or whether to
  use `torchinfo` for a newer or more advanced model-inspection task.

## Do not use this for

- Editing package source, changing tests, packaging metadata, or release work;
  route those tasks to [repo-maintenance](../repo-maintenance/SKILL.md).
- General PyTorch debugging unrelated to this package's summary calls.
- Precise memory profiling or complex input/output model introspection; prefer
  `torchinfo` or a PyTorch profiler workflow for those cases.

## Start here

1. Confirm the runtime has `torchsummary`, `torch`, and `numpy` available.
2. Import only the public API:

   ```python
   from torchsummary import summary, summary_string
   ```

3. For CPU-safe usage, pass the device explicitly and move the model yourself:

   ```python
   import torch

   device = torch.device("cpu")
   model = model.to(device)
   summary(model, input_size=(channels, height, width), device=device)
   ```

4. Use the bundled smoke helper from this sub-skill directory when you need a
   quick verification of the installed package:

   ```bash
   python scripts/smoke_summary.py --help
   python scripts/smoke_summary.py --case all --device cpu
   ```

   From the root generated skill directory, use:

   ```bash
   python sub-skills/model-summary-usage/scripts/smoke_summary.py --case all --device cpu
   ```

## References

- [API reference](references/api-reference.md): exact signatures, return values,
  `input_size`, `batch_size`, device, dtype, hook, and memory-estimate semantics.
- [Workflows](references/workflows.md): single-input, multiple-input, dtype,
  device, `summary_string`, and output-interpretation recipes.
- [Troubleshooting](references/troubleshooting.md): workflow-specific failures
  and fixes.
- [Root shared troubleshooting](../../references/troubleshooting.md): package
  install/import and cross-cutting backend issues shared with other sub-skills.

## Key facts to preserve

- Distribution/package name: `torchsummary`; version evidenced for this skill:
  `1.5.1`.
- Public exports: `summary` and `summary_string` from `torchsummary`.
- `summary(...)` prints the formatted table and returns the parameter-info tuple
  produced by `summary_string(...)`.
- `summary_string(...)` returns `(summary_str, (total_params, trainable_params))`.
- `input_size` excludes the batch dimension. A tuple means one input; a list of
  tuples means multiple inputs.
- The default device is CUDA (`cuda:0`), so CPU-only calls should pass
  `device="cpu"` or `torch.device("cpu")`.
