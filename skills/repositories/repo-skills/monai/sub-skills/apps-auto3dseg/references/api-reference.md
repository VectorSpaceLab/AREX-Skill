# Apps and Auto3DSeg API Reference

This reference summarizes public high-level APIs verified from MONAI imports, live signatures, docs, and tests. Optional dependencies are noted where relevant; do not assume broad extras are installed.

## CLI Routers

| CLI | Router contents | Safe inspection |
|---|---|---|
| `python -m monai.apps.auto3dseg -- --help` | `DataAnalyzer`, `BundleGen`, `BundleAlgo`, `AlgoEnsembleBuilder`, `EnsembleRunner`, `AutoRunner`, `NNIGen`, `OptunaGen` | Help only; requires `fire` for CLI rendering. |
| `python -m monai.apps.nnunet -- --help` | `nnUNetV2Runner` | Help only; actual use requires nnU-Net V2 dependencies. |

The Auto3DSeg CLI is a Python Fire router. Command examples generally follow:

```bash
python -m monai.apps.auto3dseg AutoRunner run --input=input.yaml
python -m monai.apps.auto3dseg DataAnalyzer get_all_case_stats --datalist=datalist.json --dataroot=data
```

## Core Auto3DSeg Signatures

| API | Signature | Primary use |
|---|---|---|
| `AutoRunner` | `(work_dir='./work_dir', input=None, algos=None, analyze=None, algo_gen=None, train=None, hpo=False, hpo_backend='nni', ensemble=True, not_use_cache=False, templates_path_or_url=None, allow_skip=True, mlflow_tracking_uri=None, mlflow_experiment_name=None, **kwargs)` | One-interface orchestration for analysis, algorithm generation, training, HPO, and ensemble prediction. |
| `DataAnalyzer` | `(datalist, dataroot='', output_path='./datastats.yaml', average=True, do_ccp=False, device='cuda', worker=4, image_key='image', label_key='label', hist_bins=0, hist_range=None, fmt='yaml', histogram_only=False, **extra_params)` | Reads image/label files and writes dataset statistics used by Auto3DSeg. |
| `BundleGen` | `(algo_path='.', algos=None, templates_path_or_url=None, data_stats_filename=None, data_src_cfg_name=None, mlflow_tracking_uri=None, mlflow_experiment_name=None)` | Generates algorithm bundle folders from templates and datastats. |
| `EnsembleRunner` | `(data_src_cfg_name, work_dir='./work_dir', num_fold=5, ensemble_method_name='AlgoEnsembleBestByFold', mgpu=True, **kwargs)` | Runs trained algorithm ensembles and saves predictions. |
| `NNIGen` | `(algo=None, params=None)` | Generates NNI-compatible HPO trials for an algorithm. |
| `OptunaGen` | API class for Optuna trial-driven HPO | Wrap in an Optuna study; optional `optuna` dependency required. |

## AutoRunner Input Schema

The `input` argument accepts a dict or a YAML/JSON path. The minimum practical segmentation source config contains:

| Key | Required? | Notes |
|---|---:|---|
| `name` | Recommended | Human-readable task name used in outputs/logging. |
| `task` | Recommended | Use `segmentation` for Auto3DSeg segmentation workflows. |
| `modality` | Yes | A string such as `CT` or `MRI`; nnU-Net bridge also accepts modality lists in some cases. |
| `datalist` | Yes | Path to a Decathlon-style JSON/YAML datalist. |
| `dataroot` | Yes | Base directory for relative image and label paths in the datalist. |
| `multigpu` | Yes for common templates | Set deliberately; `false` is safer for local/smoke plans. |
| `class_names` | Yes for labeled segmentation | Foreground class names, for example `[lesion]`. |
| `work_dir` | Optional | Can override the `AutoRunner(work_dir=...)` constructor value. |

Datalist shape:

```json
{
  "training": [
    {"fold": 0, "image": "imagesTr/case001.nii.gz", "label": "labelsTr/case001.nii.gz"}
  ],
  "testing": [
    {"image": "imagesTs/case101.nii.gz"}
  ]
}
```

Notes:

- `training` items need labels for supervised segmentation analysis/training.
- `testing` items may be unlabeled and are used for prediction/inference.
- If a `validation` key exists, AutoRunner can use it; otherwise cross-validation folds are used or inferred.
- File formats flow through MONAI loading and common support includes NIfTI, PNG/JPEG/BMP, NumPy arrays, and DICOM when appropriate readers are available.

## DataAnalyzer Outputs

`DataAnalyzer.get_all_case_stats()` returns/writes a dictionary with:

| Field | Meaning |
|---|---|
| `stats_summary` | Dataset-level summary statistics. |
| `stats_by_cases` | Per-image/per-label case statistics. |
| `image_stats` | Shape, channel, spacing, and intensity-style image summaries. |
| `image_foreground_stats` | Foreground intensity stats when labels are available. |
| `label_stats` | Label classes, pixel/voxel percentages, and label intensity summaries. |

Practical parameters:

- `device='cpu'` avoids accidental CUDA requirements for inspection.
- `label_key=None` or `label_key='None'` skips label handling for unlabeled analysis.
- `histogram_only=True` limits analysis to histograms but still reads images.
- `allowed_shape_difference` can be passed via `extra_params` to tolerate small image/label shape mismatches.

## BundleGen and BundleAlgo Notes

`BundleGen` expects:

- `algo_path`: working directory where algorithm folders and histories are written.
- `data_stats_filename`: `datastats.yaml` or JSON from `DataAnalyzer`.
- `data_src_cfg_name`: the same data-source YAML/JSON used by AutoRunner.
- `templates_path_or_url`: trusted template directory or URL; default behavior may download templates.

`BundleAlgo` represents one generated algorithm. It can set data stats/source, fill template configs, export bundle-like folders to disk, train, predict, and serialize history. Generated bundles should be edited or run using the Bundle config route, not by copying source repo templates.

## Ensemble Notes

`AlgoEnsembleBuilder` and `EnsembleRunner` use generated/trained algorithm histories.

Common prediction options include:

| Option | Meaning |
|---|---|
| `files_slices` | Restrict inference to a subset of files. |
| `mode` | `mean` or `vote` ensemble mode. |
| `sigmoid` | Use sigmoid thresholding instead of argmax class conversion. |
| `image_save_func` | Save predictions using `SaveImage`-style configuration. |
| `algo_spec_params` | Per-algorithm prediction override dictionary. |

## HPO APIs

`NNIGen` responsibilities:

- Serialize an existing `Algo`/`BundleAlgo` into trial folders.
- Fetch next parameters from NNI when `nni` is installed.
- Generate per-trial output directories and run `algo.train(params)`.
- Report final scores back to NNI if available.

`OptunaGen` responsibilities:

- Accept an Optuna `trial` object through a subclass/wrapper.
- Suggest/update hyperparameters.
- Run training and return accuracy/score to the Optuna study.

HPO execution requires optional packages and real training resources.

## nnU-Net Bridge Signature

| API | Signature | Notes |
|---|---|---|
| `nnUNetV2Runner` | `(input_config, trainer_class_name='nnUNetTrainer', work_dir='work_dir', export_validation_probabilities=True)` | Requires nnU-Net V2 tooling; mutates nnU-Net work dirs/env vars. |

Input config keys:

| Key | Required? | Notes |
|---|---:|---|
| `datalist` | Yes | MONAI-style datalist with training/testing entries. |
| `dataroot` | Yes | Dataset base path. |
| `modality` | Yes | String or list of modality names. |
| `nnunet_raw` | Optional | nnU-Net raw data directory. |
| `nnunet_preprocessed` | Optional | nnU-Net preprocessed directory. |
| `nnunet_results` | Optional | nnU-Net results directory. |
| `dataset_name_or_id` | Optional | Must be a safe identifier like `Dataset001` or `1`. |

Main methods include dataset conversion, MSD conversion, planning/preprocessing, training, single-model training, best-configuration search, prediction, ensemble, and post-processing. All are side-effecting and most are expensive.

## App Dataset Helper Signatures

| API | Signature | Use |
|---|---|---|
| `MedNISTDataset` | `(root_dir, section, transform=(), download=False, seed=0, val_frac=0.1, test_frac=0.1, cache_num=sys.maxsize, cache_rate=1.0, num_workers=1, progress=True, copy_cache=True, as_contiguous=True, runtime_cache=False)` | Classification-style MedNIST sections backed by `CacheDataset`; may download external archive. |
| `DecathlonDataset` | `(root_dir, task, section, transform=(), download=False, seed=0, val_frac=0.2, cache_num=sys.maxsize, cache_rate=1.0, num_workers=1, progress=True, copy_cache=True, as_contiguous=True, runtime_cache=False)` | Medical Segmentation Decathlon task sections backed by `CacheDataset`; may download task archives. |
| `CrossValidation` | Dataset/fold helper | Splits datasets into folds for validation schemes. |
| `TciaDataset` | TCIA helper | Uses TCIA metadata/download flows and DICOM readers; network and optional dependencies may apply. |

Dataset wrappers inherit caching behavior from MONAI data utilities. Route transform composition, reader choices, metadata, and cache tuning to `../../data-transforms/SKILL.md`.
