---
name: training
description: "Route NAVSIM learned-agent training plans, feature and target
  caches, Hydra configuration, resource selection, and checkpoint diagnosis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# NAVSIM training

Use this route when a researcher needs to plan or diagnose learned-agent
training, feature/target construction, gzip-pickle caches, or the Lightning
training wrapper. Keep this route planning-first: do not download data, build
large caches, launch training, or run benchmark workloads unless the researcher
has explicitly approved the concrete command and resource budget.

## Route by need

- Start with [workflows.md](references/workflows.md) for the safe sequence from
  agent selection through cache reuse and checkpoint handoff.
- Read [cache-and-builders.md](references/cache-and-builders.md) for builder
  contracts, cache file names, cache-only semantics, and cache compatibility.
- Read [configuration.md](references/configuration.md) for Hydra composition,
  exact override patterns, legal training splits, workers, and CPU/GPU planning.
- Use [troubleshooting.md](references/troubleshooting.md) for install/import,
  backend, data/config, CLI/API, and workflow-specific failures.
- Before any expensive action, run the read-only [training-config checker](scripts/inspect_training_config.py):
  `python scripts/inspect_training_config.py --help`, then provide a split and
  config/overrides as described in its help.

## Operating rules

1. Treat the selected `train_test_split`, log lists, agent configuration, and
   feature/target builder names as one cache identity. Do not reuse a cache
   merely because its directory exists.
2. For `use_cache_without_dataset=true`, require a non-null `cache_path` and
   `force_cache_computation=false`. The runner asserts this combination before
   constructing `CacheOnlyDataset`; it is not a performance hint.
3. For training, use a permitted training split such as `navtrain`, `trainval`,
   `mini`, or `navmini`. Never train on test, challenge, or private challenge
   splits; see the legality table in [configuration.md](references/configuration.md).
4. Prefer a small, explicit resource plan. A CPU plan is appropriate for
   imports and configuration checks, not for claiming TransFuser training
   parity. The documented GPU defaults use mixed precision and distributed
   strategy and must be reviewed against available devices.
5. Check the generated output/checkpoint contract before handing a model to an
   evaluation route. A checkpoint path is an input to learned-agent loading,
   not a substitute for matching agent configuration and cache builders.
