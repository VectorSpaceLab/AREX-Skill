---
name: lsc-benchmarks
description: "Routes OGB-LSC workflows for PCQM4M, MAG240M, WikiKG90M, and
  submission helpers."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# LSC Benchmarks

Use this subskill for the OGB-LSC family: `PCQM4M`, `PCQM4Mv2`, `MAG240M`,
`WikiKG90M`, `WikiKG90Mv2`, submission files, and evaluator smoke checks.

## Use this subskill when

- The task names `PCQM4M`, `PCQM4Mv2`, `MAG240M`, `WikiKG90M`,
  `WikiKG90Mv2`, or `OGB-LSC`.
- The task asks for `test-dev`, `test-challenge`, submission filenames, or
  evaluator-specific smoke checks.
- The task mentions `only_smiles`, `to_pyg_hetero_data`, `split_test`, or
  checkpointed inference helpers.

## First decisions

1. Read [`references/workflows.md`](references/workflows.md) for the dataset
   families and the main execution flow.
2. Read [`references/api-reference.md`](references/api-reference.md) for the
   public class names and evaluator expectations.
3. Read [`references/submission.md`](references/submission.md) when the task is
   about output filenames or submission shapes.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) when a
   dataset is deprecated, a checkpoint is missing, or a shape assertion fails.
5. If you only need to verify evaluator shapes without downloading a dataset,
   run [`scripts/lsc-smoke.py`](scripts/lsc-smoke.py).

## Main workflow

- Decide which LSC dataset family the request targets.
- Check whether the request is a data-loading task, an evaluator task, or a
  submission-format task.
- Use `only_smiles=True` when you only need the molecular strings for the
  PCQM4M family.
- Use `to_pyg_hetero_data()` when you need a PyG hetero representation for
  `MAG240M`.
- Treat `WikiKG90M` as deprecated and prefer the `v2` workflow for new work.

## Common routing choices

- `PCQM4M` / `PCQM4Mv2` -> molecular regression and submission helpers.
- `MAG240M` -> large heterogeneous node classification.
- `WikiKG90M` / `WikiKG90Mv2` -> knowledge-graph completion and top-10
  submission arrays.

## Optional backend note

The LSC examples may rely on PyG, DGL, or external frameworks such as
DGL-KE/SMORE. Those are optional or external to the core OGB package. If they
are missing, keep the workflow to the core dataset and evaluator surface unless
those extras are explicitly requested.

## What not to do here

- Do not run the full heavyweight benchmark training loops as the runtime
  answer.
- Do not treat `PCQM4M` or `WikiKG90M` as preferred starting points for new
  work.
- Do not depend on the source checkout for the final skill content.

## Related references

- [`../../references/api-overview.md`](../../references/api-overview.md)
- [`../../references/dataset-catalog.md`](../../references/dataset-catalog.md)
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md)
