# FastReID project extensions

FastReID v1.3 includes research extension projects that behave like small application packages layered on top of `fastreid`. They commonly add dataset registry entries, meta-architectures, heads, backbones, evaluators, trainers, and config keys. The safe rule is:

> Add the FastReID application root and the selected project directory to `sys.path`, import the project package, call its `add_*_config(cfg)` function when it has one, then merge project configs and build/train/evaluate.

Use `scripts/project_import_probe.py` before expensive work to verify that imports and registrations are available in the current environment.

## Generic import/config pattern

```python
from pathlib import Path
import sys

repo_root = Path("<fastreid-application-root>").resolve()
project_dir = repo_root / "projects" / "<ProjectName>"
for path in (repo_root, project_dir):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

from fastreid.config import get_cfg

# Importing the package performs registry side effects.
# Replace the import/config hook with the selected project package.
from fastattr import add_attr_config

cfg = get_cfg()
add_attr_config(cfg)          # only for projects that define project-only keys
cfg.merge_from_file("<project-or-user-config.yml>")
cfg.merge_from_list(["MODEL.DEVICE", "cuda"])
cfg.freeze()
```

Why order matters:

- Config merge must happen after project-specific keys are added. Otherwise YACS can reject keys such as `MODEL.LOSSES.BCE`, `MODEL.HEADS.PFC`, `DATASETS.RM_LT`, `TEST.DSR`, or `TEST.RECALLS`.
- Model and dataset build must happen after project package import. Otherwise registry lookups for project meta-architectures, heads, backbones, or datasets can fail.
- Dataset layout and custom dataset mechanics still belong to the data sub-skill; this page only identifies which package registers which project dataset names.

## Extension project map

| Project | Import package | Main purpose | Config hook | Registration / behavior | Extra dependency notes |
|---|---|---|---|---|---|
| `FastAttr` | `fastattr` | Pedestrian attribute recognition | `add_attr_config(cfg)` | Registers attribute datasets such as PA100k/Market1501Attr/DukeMTMCAttr, `AttrBaseline` meta-architecture, `AttrHead`, `AttrEvaluator`, and `AttrDataset`. Adds BCE loss keys and `TEST.THRES`. | Requires base FastReID/PyTorch stack; Market1501Attr/DukeMTMCAttr annotation parsing may require `mat4py`. Attribute dataset files are project-specific; route layout questions to data-and-datasets. |
| `FastClas` | `fastclas` | Image classification example using FastReID trainers/loaders | none | Registers classification-style datasets and `ClasTrainer`; stores `idx2class.json` beside checkpoints for eval-only class-name recovery. | This checkout's package initializer references a `distracted_driver` module that may be absent; probe imports before relying on package-wide `import fastclas`. |
| `FastDistill` | `fastdistill` | Knowledge distillation and overhaul distillation | usually none; uses KD keys from FastReID distiller configs | Registers `DistillerOverhaul` meta-architecture and distillation-specific ResNet backbone builder. Configs may set `MODEL.META_ARCHITECTURE Distiller` or `DistillerOverhaul` and require `KD.MODEL_CONFIG` / `KD.MODEL_WEIGHTS` teacher paths. | Requires SciPy for overhaul margin calculations; teacher configs/weights must be local. |
| `FastFace` | `fastface` | Face recognition, IResNet, Partial-FC, face verification datasets | `add_face_cfg(cfg)` | Registers face datasets (`ms1mv2`, LFW/CPLFW/CALFW/CFP/AgeDB/VGG variants), `FaceBaseline`, `FaceHead`, IResNet backbone, face evaluator, and `FaceTrainer`. Adds `DATASETS.REC_PATH`, `MODEL.BACKBONE.DROPOUT`, and `MODEL.HEADS.PFC` keys. | Requires `bcolz` for verification dataset arrays. `mxnet` is optional for direct `.rec` reading. Partial-FC is CUDA/training oriented. |
| `FastRetri` | `fastretri` | Fine-grained image retrieval | `add_retri_config(cfg)` | Registers CARS-196, CUB, Stanford Online Products, and In-Shop retrieval datasets and `RetriEvaluator`. Adds `TEST.RECALLS`. | Dataset label files are project-specific; route dataset validation to data-and-datasets. |
| `FastTune` | `autotuner` | Ray Tune hyper-parameter optimization wrapper | none | Provides `TuneReportHook` and a tuner trainer pattern that reports Rank-1/mAP to Ray Tune and mutates `SOLVER.IMS_PER_BATCH` / `DATALOADER.NUM_INSTANCE`. | Requires `ray[tune]`, `hpbandster`, `ConfigSpace`, and `hyperopt`; it launches long-running trials and should not be used for quick validation. |
| `PartialReID` | `partialreid` | Partial/occluded person ReID with DSR/FPR-style heads/evaluator | `add_partialreid_config(cfg)` | Registers partial datasets (`PartialREID`, `PartialiLIDS`, `OccludedREID`), `PartialBaseline`, `DSRHead`, and `DsrEvaluator`. Adds `TEST.DSR`. | Datasets are query/gallery-only or partial-body layouts; route layout checks to data-and-datasets. |
| `NAIC20` | `naic` | NAIC ReID competition solution and submission evaluator | `add_naic_config(cfg)` | Registers NAIC19/NAIC20 dataset variants, `NaicEvaluator`, and submission/commit evaluation behavior. Adds `DATASETS.RM_LT` and `TEST.SAVE_DISTMAT`. | Competition datasets/lists are not generic ReID layouts. Submission output requires a trained checkpoint and configured output directory. |
| `FastRT` | no regular Python package | C++ TensorRT network-definition implementation | C++ constants, not YACS | Builds a TensorRT engine from C++ network API definitions and `.wts` checkpoint dumps; can build demo, FP16/INT8, shared library, or pybind interface variants. | Requires CMake, TensorRT, CUDA, compiler toolchain, and target NVIDIA GPU. No CPU substitute. |
| `CrossDomainReID`, `DG-ReID`, `HAA` | project-specific / research-note level in this checkout | Research extensions or notes | inspect package if present | Treat as experimental until a concrete import package, config hook, and registry side effects are identified. | Probe before use; do not assume the same support level as core FastReID. |

## Project-specific training/eval entrypoint pattern

Most Python projects use the same high-level structure:

1. Append the project directory to `sys.path` and import the project package.
2. Create `cfg = get_cfg()`.
3. Call a project-specific config hook if one exists.
4. Merge a project/user config and CLI `opts`.
5. Freeze the config and run FastReID `default_setup`.
6. For eval-only: defrost, set `MODEL.BACKBONE.PRETRAIN = False`, build the project trainer/model, load `MODEL.WEIGHTS`, and test.
7. For training: instantiate the project trainer, resume or load, and train.

Keep standard training CLI mechanics in the training-and-evaluation sub-skill; use this page only to decide which imports/config hooks must happen before that trainer workflow.

## Project import probe

Use the bundled probe to classify importability without training:

```bash
python sub-skills/deployment-and-projects/scripts/project_import_probe.py \
  --repo-root <fastreid-application-root> \
  --project FastAttr \
  --project PartialReID
```

Useful variants:

```bash
# Probe every supported project package; default exits 0 and reports failures.
python sub-skills/deployment-and-projects/scripts/project_import_probe.py --repo-root <fastreid-root> --project all

# Make missing packages/import failures fail CI-like checks.
python sub-skills/deployment-and-projects/scripts/project_import_probe.py --repo-root <fastreid-root> --project all --strict

# Emit machine-readable output.
python sub-skills/deployment-and-projects/scripts/project_import_probe.py --repo-root <fastreid-root> --project FastFace --json
```

The probe adds paths only for the explicit repo root and selected project directories. It reports package import results and, when FastReID registries are importable, registry entries added by each project.

## Registration checkpoints by failure symptom

- `KeyError` for a dataset name such as `PA100K`, `CUB`, `LFW`, `NAIC20_R2`, or `PartialREID`: import the matching project package first, then re-check dataset layout with the data sub-skill.
- `KeyError` for a meta-architecture such as `AttrBaseline`, `FaceBaseline`, `DistillerOverhaul`, or `PartialBaseline`: import the project package before `build_model(cfg)`.
- `KeyError` for a head such as `AttrHead`, `FaceHead`, or `DSRHead`: import the project package before model construction.
- Unknown YACS config key: call the project's `add_*_config(cfg)` before merging the config file or `opts`.
- Missing `ray`, `bcolz`, `mxnet`, `ConfigSpace`, `hyperopt`, or TensorRT/CUDA: classify as an optional project/runtime dependency gap, not a core FastReID import failure.
