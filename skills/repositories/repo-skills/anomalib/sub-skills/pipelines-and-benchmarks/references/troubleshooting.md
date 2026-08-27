# Pipelines and Benchmarks Troubleshooting

Use this when a user has a benchmark or tiled ensemble config that parses poorly, picks the wrong runner/backend, or cannot find expected results. Prefer smoke checks and config edits before executing expensive jobs.

## Fast triage

1. Confirm whether the user wants **parsing/help**, **execution planning**, or **actual execution**.
2. If actual execution is requested, ask for dataset path, backend (`cpu` or `cuda`), expected runtime, output location, and permission to create result directories.
3. Run the bundled smoke helper on the config before `Pipeline.run`.
4. If the failure is about training/model/data/export internals rather than orchestration, route to the relevant sibling sub-skill.

## Symptom-to-fix table

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `--config` is missing or a config path is ignored | Anomalib pipeline base parses YAML only through the parser's `--config` argument unless a populated namespace is passed programmatically. | Pass `--config <file>` or `Namespace(config="<file>")`. Do not pass raw config dictionaries to `Pipeline.run`. |
| Benchmark raises unsupported accelerator | The benchmark pipeline only accepts `cpu` and `cuda` in its runner setup. | Change top-level `accelerator` to `cpu`, `cuda`, or a list containing only those values. |
| User requested CUDA but the host is CPU-only | The config asks the engine for CUDA. With no suitable device this can fail even if runner setup falls back to serial. | Change only the top-level `accelerator` to `cpu` or `[cpu]`; keep the `benchmark` grid unchanged. |
| Benchmark grid did not expand | A grid leaf was misspelled or placed at the wrong level. | Use `grid`, not `grid_search`, under the exact value to vary. Every `grid` list multiplies the job count. |
| Benchmark ran too many jobs | Multiple nested `grid` leaves multiply as a Cartesian product, and an accelerator list can run the same benchmark grid for more than one backend. | Count grid leaves first. Remove unneeded `grid` wrappers or split the benchmark into separate configs. |
| Benchmark results are not where expected | Benchmark jobs save under `runs/benchmark/<timestamp>/results.csv` relative to the process working directory. | Search under the working directory used for execution, or set/process-run from the intended output workspace. |
| Benchmark logs show “There were some errors” | A runner caught at least one job failure; full details are redirected to the pipeline log. | Inspect the pipeline log in the working directory, reduce the config to one grid point, and verify model/datamodule config separately. |
| Multiprocessing behaves differently from a patched or interactive test | `ParallelRunner` uses a spawned process pool, so monkeypatches and non-picklable state may not propagate. | Use CPU serial mode for debugging, or run a real CUDA benchmark without relying on in-process mocks. |
| Tiled ensemble config complains about missing sections | The train/eval pipelines expect specific top-level sections and job config names. | Ensure `seed`, `accelerator`, `default_root_dir`, `tiling`, `normalization_stage`, `thresholding_stage`, `data`, `SeamSmoothing`, and `TrainModels.model` are present. |
| Tiled ensemble creates many unexpected checkpoints | Tile count is larger than expected because `stride` is smaller than `tile_size` or image size is large. | Calculate tile grid first. Increase stride, reduce image size, or reduce tile overlap for smoke runs. |
| Tiled training skips statistics | Validation split mode is `none`. | Provide validation data or choose a val split mode that creates validation predictions. If stats are intentionally absent, avoid image-level normalization/thresholding assumptions. |
| Tiled evaluation cannot find checkpoints | `EvalTiledEnsemble(root_dir=...)` points to a parent directory or the dataset root instead of the exact versioned ensemble run. | Point `root_dir` at the run containing `weights/lightning/model<i>_<j>.ckpt` files. If training just ran, reuse `train_pipeline.root_dir`. |
| Tiled evaluation cannot find `stats.json` | Validation statistics were not produced, the wrong root was selected, or the config expects stats for `normalization_stage: none`. | Check the run root. If stats are required, rerun training with validation data or choose a normalization/thresholding mode that does not require missing stats. |
| Tiled visualization or metrics output is missing | Evaluation skipped the test phase or stopped before later serial stages. | Check `test_split_mode`; it must not be `none`. Also check earlier prediction/merge errors in the pipeline log. |
| Dataset root and results root are confused | `data.init_args.root` points to the dataset; `default_root_dir` and `EvalTiledEnsemble(root_dir=...)` point to generated results. | Keep them separate. Do not pass the dataset root as the evaluation results root. |
| MEBin benchmark request looks small but runs slowly | It loops over multiple models, categories, and post-processors, each with fit/test. | Treat as benchmark-scale; ask the user to narrow models/categories and approve runtime before running. |

## CPU serial recovery without losing a benchmark grid

When a benchmark config asks for CUDA but the user only wants CPU serial fallback, edit only this part:

```yaml
accelerator: cpu
```

or, if the rest of the config expects a list form:

```yaml
accelerator:
  - cpu
```

Do not modify the nested `benchmark:` tree. Keeping that tree unchanged preserves model, data, seed, and category grid expansion. After the change, run:

```bash
python sub-skills/pipelines-and-benchmarks/scripts/pipeline_config_smoke.py --benchmark-config benchmark.yaml
```

The helper should report a serial CPU runner plan and the same grid combination count.

## Wrong tiled-ensemble root recovery

If the user gives a path such as `results`, `results/Padim`, or a dataset directory, ask them to identify the exact run directory. A valid evaluation root usually looks like:

```text
results/Padim/MVTecAD/bottle/v0
```

and contains a `weights/lightning/` directory with per-tile checkpoints. For a 2×2 tile grid, the expected checkpoint names are:

```text
model0_0.ckpt
model0_1.ckpt
model1_0.ckpt
model1_1.ckpt
```

If the user trained in the same Python session, the safest fix is:

```python
eval_pipeline = EvalTiledEnsemble(root_dir=train_pipeline.root_dir)
```

If evaluating later, run the smoke helper with both the config and candidate root:

```bash
python sub-skills/pipelines-and-benchmarks/scripts/pipeline_config_smoke.py --tiled-config ensemble.yaml --eval-root results/Padim/MVTecAD/bottle/v0
```

## When not to execute

Stop at planning or smoke checks when any of these are unresolved:

- dataset root is missing or points to the wrong dataset layout;
- the user has not approved result-directory creation;
- benchmark grid count is high and no runtime budget was provided;
- CUDA is requested but visible CUDA hardware is unknown or unavailable;
- tiled ensemble root is ambiguous;
- the request mixes pipeline orchestration with deployment/export or Studio application work that belongs elsewhere.
