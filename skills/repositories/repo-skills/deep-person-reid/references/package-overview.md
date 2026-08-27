# Torchreid package overview

## When to read

Read this to orient a Torchreid/deep-person-reid task before choosing a sub-skill. It summarizes public modules, supported workflows, dependency/backends, and selected gaps.

## Package identity

- Public project: Torchreid / deep-person-reid.
- Python distribution/import: `torchreid`.
- Version distilled for this skill: `1.4.0`.
- Core domain: deep-learning person re-identification (ReID) in PyTorch.

## Public module map

| Module | Primary use | Route |
| --- | --- | --- |
| `torchreid.data` | `ImageDataManager`, `VideoDataManager`, dataset registration, transforms, samplers | `sub-skills/training-evaluation/` |
| `torchreid.engine` | Image/video softmax/triplet engines and `Engine.run(...)` | `sub-skills/training-evaluation/` |
| `torchreid.optim` | `build_optimizer`, `build_lr_scheduler` | `sub-skills/training-evaluation/` |
| `torchreid.losses` | Cross entropy with label smoothing, hard-mining triplet loss | `sub-skills/training-evaluation/` |
| `torchreid.models` | model registry, `show_avai_models`, `build_model` | `sub-skills/feature-extraction/` and `training-evaluation/` |
| `torchreid.utils` | `FeatureExtractor`, checkpoints, model complexity, ranked visualization, re-ranking | `sub-skills/feature-extraction/` |
| `torchreid.metrics` | distance matrices, rank CMC/mAP, accuracy | `sub-skills/feature-extraction/` |

## Runtime coverage

This generated skill covers three self-contained runtime areas:

1. Training/evaluation/data/config command planning and package API use.
2. Feature extraction, model building, metrics, re-ranking, and visualization.
3. Core checkpoint export planning and optional dependency checks.

It does not bundle advanced project-local code under `projects/` for DML, OSNet-AIN NAS, or PA-100K attribute recognition. Those workflows require substantial project sources plus external data/GPU resources; treat them as explicit long-tail gaps unless a future extension adds self-contained project scripts and verification fixtures.

## Backend status

| Backend / dependency family | Status in this skill | Practical guidance |
| --- | --- | --- |
| CPU PyTorch | Required for API inspection and smoke checks | Enough for imports, model construction, tiny feature extraction, parser checks, and synthetic metric cases. |
| CUDA PyTorch | Optional/unverified by default | Recommended for real training/evaluation and multi-GPU performance; do not claim CUDA verification from CPU checks. |
| Cython rank extension | Included in package install when build succeeds | `torchreid.metrics.rank` falls back to Python when Cython is unavailable, but the Cython path is faster. |
| ONNX | Optional export dependency | Needed for actual ONNX artifact writing and validation. |
| OpenVINO | Optional export dependency | Run only after ONNX succeeds; needs OpenVINO Model Optimizer tooling. |
| TensorFlow / openvino2tensorflow | Optional export dependency | Needed for TFLite-style conversion chain after OpenVINO. |
| Dataset downloads | Network/data dependent | Do not assume automated downloads work; many datasets require manual downloads or licenses. |

## Quick route chooser

- Need to train/test, prepare datasets, modify config, parse logs, or compute dataset stats: open `sub-skills/training-evaluation/SKILL.md`.
- Need embeddings, model keys, local checkpoint loading, distances, rank metrics, re-ranking, complexity, visrank, or activation maps: open `sub-skills/feature-extraction/SKILL.md`.
- Need ONNX/OpenVINO/TFLite-style export from a core Torchreid checkpoint: open `sub-skills/model-export/SKILL.md`.

## Safe root check

Run the root helper when you only need a non-training sanity check:

```bash
python scripts/check_torchreid_env.py --model-name osnet_x0_25
```

This imports Torchreid, reports package/backend facts, builds a small model with `pretrained=False`, and optionally probes CUDA when requested. It does not download datasets or weights.
