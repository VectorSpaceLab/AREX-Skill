---
name: benchmark-workflows
description: "Use BoxMOT for cached benchmark generation, evaluation, tuning,
  research loops, and benchmark configuration debugging."
metadata:
  disco-role: operating
disable-model-invocation: true
license: AGPL 3.0
---

# Benchmark Workflows

Use this sub-skill when the task is about `generate`, `eval`, `tune`, or `research`, benchmark YAMLs, cache reuse, public detections, or replay-backend selection.

## Covers

- `boxmot generate`
- `boxmot eval`
- `boxmot tune`
- `boxmot research`
- benchmark config selection and split handling
- cache keys and reuse behavior
- public detections vs private detector runs
- postprocessing modes such as `gsi`, `gbrc`, and `gta`
- tracker replay backend selection (`python` vs `cpp`)
- `--tune-kf` and benchmark-dependent detector/ReID resolution

## Does not cover

- live tracking from raw video or webcam input
- ReID training/export workflows
- native C++ build instructions

Use the sibling routes when the request is about those tasks.

## Read first

- [Benchmark workflows](references/benchmark-workflows.md)
- [Configuration details](references/configuration.md)
- [Troubleshooting](references/troubleshooting.md)
- [Benchmark config summary script](scripts/benchmark_config_summary.py)

## Good prompts for this route

- "Generate caches for MOT17 and reuse them in eval."
- "How do I switch between public and private detections?"
- "Why does tune keep regenerating the cache?"
- "What benchmark YAML does mmot-mini use?"
- "How do I run research with a different tracker backend?"

## Typical workflow

1. Identify whether the user is starting from a benchmark name, a dataset path, or an existing cache directory.
2. Decide whether the command should use `--benchmark` or `--source`.
3. Check whether the user wants public detections, postprocessing, or native replay.
4. Confirm the benchmark split and cache identity before suggesting a rerun.
5. If the user only wants to inspect the config, use the bundled summary script instead of a full replay.

## Entry points

### Generate cache

```bash
boxmot generate --benchmark mot17 --split ablation
```

### Evaluate cached tracking

```bash
boxmot eval --benchmark mot17 --split ablation --tracker boosttrack
```

### Tune a tracker

```bash
boxmot tune --benchmark mot17 --split ablation --tracker bytetrack --n-trials 10
```

### Research a tracker change

```bash
boxmot research --benchmark mot17 --split ablation --tracker bytetrack --proposal-model openai/gpt-5.4
```

## What to hand off to nearby references

- Command semantics and cache rules belong in `references/benchmark-workflows.md`.
- YAML field layout and benchmark defaults belong in `references/configuration.md`.
- Missing benchmark configs, cache mismatches, and replay-backend errors belong in `references/troubleshooting.md`.

Use `scripts/benchmark_config_summary.py` when the user needs a quick, safe, inspect-only summary of a benchmark config.
