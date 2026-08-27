---
name: fast-reid
description: "Operate FastReID setup, configuration, datasets, model/inference
  APIs, training/evaluation workflows, deployment/export paths, and extension
  projects for person and vehicle re-identification."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# FastReID repo skill

Use this skill when a task involves FastReID (`fastreid`), person or vehicle
re-identification, Market1501/DukeMTMC/MSMT17/VeRi/VehicleID style datasets,
FastReID YAML configs, ReID feature extraction, rank/mAP/mINP evaluation,
training/eval command construction, ONNX/Caffe/TensorRT export, or FastReID
extension projects.

## First checks

1. Confirm FastReID is importable. This inspected commit is source-only, so use
   a local checkout import path or a bundled script's `--repo-root` option when
   no installed distribution exists.
2. Confirm the intended backend. `MODEL.DEVICE` defaults to `cuda`; CPU smoke
   checks must override it explicitly.
3. Confirm required data/checkpoints. Real train/eval/inference requires local
   datasets and often local checkpoints or pretrain weights.
4. Run the safe root helper when setup or optional dependencies are unclear:

```bash
python scripts/check_fastreid_environment.py \
  --repo-root <FASTREID_REPO> \
  --config-file <CONFIG_YAML> \
  --device cpu
```

The helper imports modules and merges config only; it does not train,
evaluate, download, or write checkpoints.

## Route by task

| Task signal | Read |
|---|---|
| Source-only import, dependencies, Python version, `get_cfg`, `_BASE_`, YAML merge, `opts`, model-zoo recipe/config selection | [`sub-skills/setup-and-configuration/`](sub-skills/setup-and-configuration/) |
| `FASTREID_DATASETS`, built-in dataset layouts, custom dataset registration, dataloaders, transforms, samplers, data preflight | [`sub-skills/data-and-datasets/`](sub-skills/data-and-datasets/) |
| `build_model`, backbones/heads/losses/meta-architectures, `DefaultPredictor`, feature tensors, CPU model smoke, rank import quirks | [`sub-skills/modeling-and-inference/`](sub-skills/modeling-and-inference/) |
| Training/eval command building, `DefaultTrainer`, distributed flags, checkpoints/resume, solvers, metrics, logs, custom loops | [`sub-skills/training-and-evaluation/`](sub-skills/training-and-evaluation/) |
| ONNX/Caffe/TensorRT export/inference, optional deployment deps, FastRT, project-extension imports/config hooks | [`sub-skills/deployment-and-projects/`](sub-skills/deployment-and-projects/) |

## Shared references

- [`references/package-map.md`](references/package-map.md) — compact module,
  registry, signature, dependency, and route map for this FastReID version.
- [`references/troubleshooting.md`](references/troubleshooting.md) —
  cross-cutting install/import, config, backend, dataset, checkpoint,
  inference, deployment, and project-extension failures.
- [`references/repo-provenance.md`](references/repo-provenance.md) — source
  commit, package version, evidence paths, and refresh baseline.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json)
  — structured metadata for managed repo-skills-router import.

## Shared script

- [`scripts/check_fastreid_environment.py`](scripts/check_fastreid_environment.py)
  — safe import/config/optional-backend probe. Use it before deeper workflow
  debugging or before deciding whether CUDA/ONNX/Caffe/TensorRT dependencies
  are available.

## Operating boundaries

- This skill teaches FastReID operation; it does not reproduce model-zoo
  benchmarks by itself.
- Do not run long training/evaluation, network downloads, dataset acquisition,
  Caffe/TensorRT builds, or multi-node jobs without explicit user data,
  hardware, runtime, and budget approval.
- CPU checks can validate imports/config/model plumbing, but they do not prove
  CUDA training performance or TensorRT/Caffe runtime equivalence.
- Extension projects add registry entries after importing their packages or
  config hooks. If a project config fails with unknown keys or missing registry
  entries, route to `deployment-and-projects` before editing configs.
