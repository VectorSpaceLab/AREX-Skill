# Benchmark Configuration Details

## Where configs live

Benchmark YAMLs live under `boxmot/configs/benchmarks/`.

## Main sections

A benchmark YAML usually contains:

- `id`
- `dataset`
- `benchmark`
- `detector`
- `reid`
- `download`
- `evaluation`
- `storage`

## What each section does

### `dataset`
Holds the dataset root, split mapping, layout, and class metadata.

### `detector`
Selects the detector profile or model and the detector defaults used by the benchmark.

### `reid`
Selects the ReID profile or model and its preprocessing defaults.

### `download`
Declares where BoxMOT should fetch benchmark assets from when they are missing.

### `evaluation`
Declares metric backend, box type (`aabb` or `obb`), class bridge information, and class remapping.

### `storage`
Describes where the benchmark data or split caches live.

## Important helpers

- `resolve_benchmark_cfg_path(name)` resolves the YAML path.
- `load_benchmark_cfg(name)` loads the benchmark bundle.
- `load_benchmark_cfg_from_args(args)` reads the active benchmark from the CLI namespace.
- `resolve_eval_box_type(args, bench_cfg)` determines whether evaluation uses AABB or OBB.
- `resolve_obb_eval_class_pairs(args, bench_cfg)` maps MMOT-style OBB evaluation classes.

## Config-driven command rule

`eval`, `tune`, and `research` require `--benchmark`. `generate` can use either a benchmark or a direct dataset source, but not both.

## Common benchmark fields the skill should mention

- benchmark ids such as `mot17`, `sportsmot`, `mmot`, and `mmot-mini`
- split names such as `ablation`, `train`, `val`, and `test`
- detector/ReID defaults sourced from the YAML
- OBB datasets using `box_type: obb`

## Quick inspect recipe

Use the bundled summary script when you only need the config shape, not a full run:

```bash
python sub-skills/benchmark-workflows/scripts/benchmark_config_summary.py --benchmark mmot-mini --json
```
