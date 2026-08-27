# Search Workflows

## Purpose

Read this for the recipe-level search flows. The bundled smoke script covers the
no-download path; this reference covers the real predictor-driven workflow.

## 1. Offline smoke search

Use the bundled `scripts/tiny_search.py` when you only need to verify that the
search controller and accuracy predictor work.

The smoke uses:

- `AccuracyPredictor(pretrained=False)`
- a small dummy efficiency predictor
- a short evolutionary loop

This is the fastest way to prove the search route works without public downloads.

## 2. FLOPs-constrained search

Use this when the user wants the tutorial-style FLOPs curve or a published
architecture search run.

Typical flow:

1. Build an `AccuracyPredictor`.
2. Build or load a `FLOPsTable`.
3. Create `EvolutionFinder` with `constraint_type='flops'`.
4. Set `efficiency_constraint` to a value in the published range.
5. Run `run_evolution_search()` and inspect `best_info`.

The notebook examples use a constraint range in the hundreds of MFLOPs.

## 3. Latency-constrained search

Use this when the user wants a device-specific search curve.

Typical flow:

1. Build an `AccuracyPredictor`.
2. Build a `LatencyTable` for the target device family.
3. Create `EvolutionFinder` with `constraint_type='note10'` or the matching device family.
4. Search with a latency constraint inside the valid range.
5. Inspect the best sample and its predicted latency.

The tutorial notebook uses device families such as `note10` and `flops` as
constraint types.

## 4. Notebook-derived route

The source notebook demonstrates:

- accuracy predictor setup
- latency table setup
- FLOPs table setup
- repeated evolution search with different constraints
- plotting the resulting tradeoff curve

Use the notebook workflow reference when you need the published sequence, but use
`tiny_search.py` for a fast smoke.
