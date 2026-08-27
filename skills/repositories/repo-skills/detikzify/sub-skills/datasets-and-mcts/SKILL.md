---
name: datasets-and-mcts
description: "Work with DeTikZify dataset helpers, local dataset fallbacks,
  Paper2Fig and SciCap builders, and the generic Monte Carlo tree-search
  engine."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Datasets and MCTS

Use this sub-skill when the task is about DeTikZify's dataset helpers, local dataset fallback behavior, Paper2Fig or SciCap builders, or the standalone `Node` / `MonteCarlo` tree-search engine.

Route away from this sub-skill when the main task is programmatic inference, training, or evaluation scoring. Those workflows depend on these helpers, but they have their own dedicated sub-skills.

## Fast Path

1. Run the safe MCTS helper if you only need to confirm the search engine imports correctly:
   ```bash
   python scripts/mcts_smoke.py
   ```
2. Check the API snapshot if you need the loader and tree-search signatures:
   ```bash
   python scripts/api_smoke.py
   ```
3. Read the data reference before using the dataset builders:
   ```text
   references/data-and-mcts.md
   ```

## What This Sub-Skill Owns

- `detikzify.dataset.load_dataset(...)` and its local fallback behavior
- the `Paper2Fig` and `SciCap` dataset builders
- dataset feature shapes and field expectations for the figure datasets
- the generic `Node` and `MonteCarlo` classes from `detikzify.mcts`
- tree-search behavior such as `simulate`, `expand`, `random_rollout`, `make_choice`, and `make_exploratory_choice`

## Common Decisions

- Use the local dataset fallback when a package-relative dataset directory is present.
- Use the dataset builder references to understand feature names before trying a conversion or load.
- Use `Node` / `MonteCarlo` when you need generic search behavior rather than the inference-specific wrapped tree used by the pipeline.
- Keep the state object compatible with the tree-printing helpers if you want debug output.

## Bundled References

- [references/data-and-mcts.md](references/data-and-mcts.md): dataset builder fields, local fallback behavior, and tree-search semantics.
- [references/workflows.md](references/workflows.md): how the dataset loaders and generic MCTS engine are typically used.
- [references/troubleshooting.md](references/troubleshooting.md): missing local datasets, empty child lists, and state-shape issues.

## Related Helpers

- [../../scripts/mcts_smoke.py](../../scripts/mcts_smoke.py): safe dummy-state MCTS sanity check.
- [../../scripts/api_smoke.py](../../scripts/api_smoke.py): safe import and signature snapshot.

## Guardrails

- Do not treat a successful dataset import as proof that the remote dataset or its artifacts are reachable.
- Do not assume the generic `Node` state shape matches the inference pipeline's wrapped internal state.
- Do not call the generic search engine a success if `child_finder` never adds children.
