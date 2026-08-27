---
name: data-pipelines
description: "Build and troubleshoot Ray Data pipelines for loading,
  transforming, writing, and tuning datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Ray Data Pipelines

Use this sub-skill when the task involves `ray.data`, `Dataset`, dataset readers such as `read_csv`, `read_parquet`, `read_images`, `read_text`, in-memory creation with `from_items`, row or batch transforms, `write_parquet`, schema or batch-format issues, optional Data dependencies, block sizing, concurrency, or Ray Data memory/performance behavior.

## Fast Routing

- For Ray Core task/actor internals, object refs, placement groups, or cluster resources outside Data APIs, route to `../core-runtime/SKILL.md`.
- For feeding datasets into Ray Train or Tune workflows, use this sub-skill for dataset construction and then route to `../train-tune/SKILL.md` for trainers, tuners, scaling configs, and checkpoints.
- For Serve request batching or online inference deployment, route to `../serve-deployments/SKILL.md` after any generic Ray Data preprocessing.
- LLM-specific data ingestion is out of default scope unless the solution only uses generic Ray Data APIs described here.

## Working Pattern

1. Confirm the environment has the narrow extra needed for Data work, usually `ray[data]`; avoid recommending `ray[all]` by default.
2. Pick a source pattern: local/cloud file reader, `from_items`, `from_pandas`, `from_numpy`, or `from_arrow`.
3. Choose the transform level: `map` for one row to one row, `flat_map` for one row to many rows, and `map_batches` for vectorized pandas, NumPy, or PyArrow logic.
4. Keep output and validation explicit: call `take`, `schema`, `materialize`, `stats`, or a writer such as `write_parquet` to trigger lazy execution.
5. Tune only after the basic pipeline works: inspect blocks with `materialize().stats()`, then adjust `override_num_blocks`, `concurrency`, `ray_remote_args`, `batch_size`, and `DataContext` options.

## Bundled References

- `references/api-reference.md` lists the core Ray Data APIs, signatures, parameters, and validation checks.
- `references/workflows.md` gives self-contained recipes for local/cloud/in-memory reads, batch transforms, writes, and Core/Train/Tune handoff.
- `references/performance-and-troubleshooting.md` covers block sizing, fusion/materialization, optional dependencies, schema errors, OOMs, and path/cloud issues.
- `scripts/data_pipeline_smoke.py` is a safe helper adapted from Ray Data key-concept examples; it defaults to `--help`/argument parsing and only runs a tiny local in-memory pipeline when `--run` is passed.

## Minimal Sanity Check

Run the bundled smoke helper before debugging larger pipelines:

```bash
python scripts/data_pipeline_smoke.py --help
python scripts/data_pipeline_smoke.py --run --rows 4 --num-blocks 2
```

Add `--write-parquet` only when you want the smoke helper to create a temporary Parquet output as part of the check.
