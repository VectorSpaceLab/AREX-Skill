---
name: cvnets
description: "Router for CVNets training, evaluation, registry, data, and export workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# CVNets

CVNets is the top-level operating skill for the Apple `ml-cvnets` repository. Use this skill when a user mentions CVNets, `cvnets-*` commands, the model zoo, YAML configs under `config/`, the `examples/` recipes, or any of the repo's training, evaluation, model-building, data, or export workflows.

This root skill stays router-like. It points you to the smallest sub-skill that owns the requested workflow and to the shared references/scripts that are safe to use without reopening the source tree.

## Start here

- `references/repo-provenance.md` — repository snapshot and staleness baseline.
- `references/repo-routing-metadata.json` — scenario metadata used during import.
- `references/api-reference.md` — verified public APIs, entry points, and signatures.
- `references/cli-reference.md` — canonical command families and safe wrapper entry points.
- `references/configuration.md` — YAML flattening, overrides, and common config keys.
- `references/model-overview.md` — supported task families and model registry notes.
- `references/troubleshooting.md` — cross-cutting install/import/config/backend failures.
- `scripts/check_install.py` — safe import/backend smoke.
- `scripts/inspect_config.py` — resolve and print a config without training.

## Route map

| Sub-skill | Use it when | Owns | Excludes |
| --- | --- | --- | --- |
| `training-and-evaluation` | You need to train, finetune, resume, or evaluate a CVNets model. | `main_train.py`, `main_eval.py`, distributed setup, checkpoints, optimizer/scheduler/loss assembly, classification, detection, and segmentation evaluation flows. | CoreML conversion, model zoo details, and dataset-layout deep dives. |
| `models-and-architectures` | You need to choose, inspect, or debug a CVNets model family. | Model registry behavior, architecture families, pretrained loading, ByteFormer, CLIP, audio/bytes model variants, and exportability expectations. | Training loop mechanics and full dataset-layout walkthroughs. |
| `data-and-config` | You need to parse, edit, validate, or override configs; set dataset roots; or reason about samplers, collate fns, transforms, tokenizers, or video readers. | YAML config flattening, dotted option semantics, dataset roots, samplers, collate functions, image/audio/video transforms, and text-tokenizer layouts. | Model-family selection and export/runtime conversion. |
| `conversion-and-profiling` | You need CoreML conversion, benchmark throughput, or loss-landscape generation. | `main_conversion.py`, `main_benchmark.py`, `main_loss_landscape.py`, JIT/CoreML export, benchmark settings, and loss-landscape parameters. | Training orchestration and dataset-format design. |

## Shared facts

- Public package name: `cvnets`.
- Source version captured by this skill: `0.3`.
- The repo uses dotted option names in configs and argparse, but CLI flags still use hyphenated spellings such as `--common.config-file`.
- `setup.py` registers console scripts for train/eval/conversion, but some installed environments do not resolve the top-level `main_*` modules correctly. Prefer the bundled wrappers in this skill tree when you need a reliable entry point.
- Most workflows expect a YAML config file plus one or more dataset roots, pretrained weights, or override arguments.
- GPU usage is optional for some smoke checks but required for the repo's full distributed and benchmark-style examples.

## Operating notes

- Read the shared references before guessing at a workflow.
- If you are uncertain whether the question is about model selection, data/config, training, or export, start with the route map and then open the nearest sub-skill.
- Keep runtime commands inside the skill tree; do not tell future agents to rely on source checkout paths from this production batch.
