---
name: configuration-and-models
description: "Safely inspect and validate Det3D Python configurations,
  registries, model-family composition, anchors, tasks, and checkpoint metadata
  without constructing data pipelines or training jobs."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Det3D Configuration and Models

Use this sub-skill when a Researcher must understand, compare, edit, or safely
preflight a Det3D configuration or detector checkpoint. It is an inspection
and construction guide, not a promise that an old CUDA model can run in a
modern environment.

## Scope and safety boundary

- Covers `Config.fromfile`, Python-config conventions, configuration
  overrides, registries/builders, VoxelNet/SECOND/PointPillars composition,
  anchors/tasks, box coders, and checkpoint metadata.
- Start with the bundled non-constructive inspector:
  `python scripts/inspect_config.py PATH_TO_CONFIG`.
- The default inspector parses a config statically. It does not import model
  modules, build a detector, instantiate a dataset, read annotations, or start
  training. Use `--execute-python` only when executing the supplied config is
  explicitly acceptable; even then it never builds a model or dataset.
- Treat a configuration as executable Python. Do not run an untrusted config
  merely to “see its values”; inspect it statically first.
- Do not infer runtime support from a successful static parse. Full model
  construction generally needs the historical dependency and compiled-op
  stack described in [troubleshooting](references/troubleshooting.md).

## Fast routing

1. Identify the dataset, point-cloud range, voxel size, class list, and
   annotation/info paths. Keep those paths as user-supplied values; do not
   silently rewrite them.
2. Identify `model.type` and follow the family map in
   [model overview](references/model-overview.md):
   - `PointPillars` → `PillarFeatureNet` → `PointPillarsScatter` → `RPN` →
     `MultiGroupHead`.
   - `VoxelNet` with `SpMiddleFHD` is the repository's SECOND-style family.
   - `VoxelNet` with `SpMiddleResNetFHD` is the CBGS-style example family.
   - “SECOND” and “CBGS” are example/configuration families here, not separate
     detector registry names.
3. Check that `tasks` and `anchor_generators` partition classes in the same
   order. Check that the box coder's encoded dimension agrees with the head's
   regression output.
4. Check the spatial contract: voxel grid, backbone `ds_factor`, neck strides,
   and `assigner.out_size_factor` must agree. Use the formula in
   [configuration](references/configuration.md).
5. Only after those checks and a dependency gate, consider
   `build_detector(cfg.model, train_cfg=cfg.train_cfg, test_cfg=cfg.test_cfg)`.
   Never call `build_dataset` as part of configuration inspection.

## Configuration contract

Expected example-style sections are `model`, `train_cfg`, `test_cfg`, `data`,
`tasks`, `target_assigner`, `box_coder`, voxel/pipeline settings, optimizer,
checkpoint, and runtime settings. A section may be absent in a reduced config,
but a training or evaluation command will later require the sections it
accesses.

Important source behavior:

- `Config.fromfile` supports `.py`, `.yml/.yaml`, and `.json`; Python files are
  executed and all non-dunder module names become config entries.
- This version has no general `_base_` inheritance or merge API. Python
  variables, imports, and explicit post-load assignments are the available
  composition mechanisms. CLI training overrides are limited and should not
  be mistaken for a generic config merge.
- Anchor constructor spelling is normalized by `det3d.builder`: config uses
  `matched_threshold`/`unmatched_threshold`, while the generator stores
  match/unmatch thresholds.
- `tasks[i]["class_names"]` is authoritative for head class counts; preserve
  the declared `num_class` and verify it equals the list length.

## Registry and builder use

The public model builders and registry names are summarized in
[API reference](references/api-reference.md). A builder requires a mapping with
`type`; a list is built as an `nn.Sequential`. Registry imports register classes
as a side effect, so a missing type can mean a missing import as well as a bad
spelling. Never “fix” an unknown type by constructing an arbitrary Python
class from a config value.

Safe inspection should answer:

- What detector, reader, backbone/scatter, neck, and head types are named?
- Which task names and anchor classes are present, and in what order?
- Which box coder, loss, NMS, and output stride settings are declared?
- Which checkpoint path, `load_from`, or `resume_from` is intended, and what
  metadata is expected?

## Checkpoint and workflow guardrails

Det3D checkpoints saved by its trainer normally contain `meta`, `state_dict`,
and optionally `optimizer`. Training stores version/config/class metadata;
evaluation restores `CLASSES` from `checkpoint["meta"]` when present and falls
back to the dataset classes otherwise. Inspect metadata before loading weights.
Use `strict=False` only as a deliberate compatibility choice: missing,
unexpected, and shape-mismatched keys still indicate an architecture or class
contract to investigate.

Do not use the bundled inspector as a replacement for `tools/train.py`,
`tools/test.py`, or distributed test launchers. Those workflows construct
CUDA-dependent datasets/models and have their own required arguments. See
[troubleshooting](references/troubleshooting.md) for common CLI/API misuse and
failure triage.

## Evidence and limits

This sub-skill is distilled from the pinned Det3D source baseline, its
PointPillars, SECOND, and CBGS example configs, model/anchor builders, config
loader, checkpoint trainer, setup/install documentation, and getting-started
workflow. The historical baseline targets Python 3.6, PyTorch 1.1–1.6, CUDA
10.0/10.1, CMake ≥3.13.2, spconv, and nuscenes-devkit. Do not claim modern
full parity, CPU-only training, or successful spconv/custom-op execution when
those prerequisites are absent.

## Bundled operating material

- [api-reference.md](references/api-reference.md): public APIs, registries,
  model inputs, and checkpoint fields.
- [configuration.md](references/configuration.md): config loading, validation,
  model-family checks, task/anchor alignment, and safe editing.
- [model-overview.md](references/model-overview.md): detector/component graph,
  tensor contracts, box coders, and family-specific choices.
- [troubleshooting.md](references/troubleshooting.md): compatibility, import,
  CLI, checkpoint, and workflow failure triage.
- [inspect_config.py](scripts/inspect_config.py): static-by-default config
  inspector with an explicit opt-in Python execution mode.
