---
name: libmtl
description: "Routes LibMTL installation, core APIs, customization, and
  benchmark workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LibMTL

Use this skill for the LibMTL package, its shared training engine, and the
benchmark examples that ship with the repository.

## First checks

- Read [`references/repo-provenance.md`](references/repo-provenance.md) when you need to confirm whether this
  skill matches the current checkout or before asking for a refresh.
- Use the repository's own install flow first:
  `pip install -r requirements.txt && pip install -e .`
- Then run the bundled install smoke check:
  `python -I scripts/check_install.py`
- LibMTL's benchmark workflows assume a CUDA-capable PyTorch environment.
  `LibMTL.Trainer` hard-codes `cuda:0`, so there is no CPU fallback for the
  training examples.
- Each benchmark sub-skill bundles the launch pattern and validation helpers
  for its workflow. Several older docs and tests in the source checkout use
  outdated benchmark names; rely on the current sub-skill guidance and bundled
  scripts instead.

## Route map

- `sub-skills/core-api/` — install/import details, `Trainer`, shared config,
  built-in losses/metrics/models/architectures/weightings, and direct API
  usage.
- `sub-skills/customization/` — adding a new dataset, new task dictionary,
  new loss or metric, new architecture, or new weighting strategy.
- `sub-skills/vision-benchmarks/` — NYUv2 and Cityscapes scene understanding
  workflows, including DeepLabV3+, SegNet+MTAN, and the shared vision helpers.
- `sub-skills/office-benchmarks/` — Office-31 and Office-Home multi-input
  image classification workflows with a bundled self-contained runtime package.
- `sub-skills/qm9/` — QM9 graph regression with torch-geometric and
  `random_split.t`.
- `sub-skills/paws-x/` — PAWS-X / XTREME multilingual sentence classification,
  cache generation, and preprocessing caveats.

## What this root skill covers

- Shared installation and import verification.
- Which public modules exist and how to choose them.
- Which sub-skill owns a dataset- or workflow-specific question.
- Cross-cutting runtime pitfalls such as CUDA-only training, stale docs/tests,
  or configuration flags that are accepted by help output but not fully wired.

## When to stay at the root

Use the root when the request is only about:

- the package name, version, or install command;
- whether LibMTL can be imported in the current environment;
- which sub-skill to use;
- the repo provenance or staleness check;
- a cross-cutting troubleshooting question that is not tied to one benchmark.

## When to open a sub-skill

Open the matching sub-skill if the request mentions any of these signals:

- `Trainer`, `prepare_args`, `weight_args`, `arch_args`, `rep_grad`, or
  `multi_input` → `core-api`.
- new dataset, new metric/loss, new architecture, or new weighting strategy →
  `customization`.
- NYUv2, Cityscapes, semantic segmentation, depth, surface normals, DeepLab,
  ASPP, SegNet, or MTAN → `vision-benchmarks`.
- Office-31, Office-Home, domain adaptation, or multi-input image
  classification → `office-benchmarks`.
- QM9, `torch_geometric`, `NNConv`, `Set2Set`, or molecular regression →
  `qm9`.
- PAWS-X, XTREME, `bert-base-multilingual-cased`, cached features, or the raw
  TSV preprocess scripts → `paws-x`.

## Shared guidance

- Pass `weighting` and `architecture` as string names such as `"EW"` and
  `"HPS"`; the trainer resolves them internally.
- If you instantiate `Trainer` manually, include both `weight_args={}` and
  `arch_args={}` unless you already ran `prepare_args`.
- `prepare_args` currently wires `optim=adam|sgd` and `scheduler=step`.
  `adagrad`, `rmsprop`, `cos`, and `exp` appear in the parser/help text but are
  not fully populated by the current implementation.
- Vision and PAWS-X example scripts may download pretrained backbones or model
  weights on first run; that is expected and should be called out when a user
  is offline.

## Read next

- `references/api-reference.md` for the verified Python API surface.
- `references/configuration.md` for shared CLI flags and method-specific
  options.
- `references/troubleshooting.md` for cross-cutting install, import, and
  runtime failures.
