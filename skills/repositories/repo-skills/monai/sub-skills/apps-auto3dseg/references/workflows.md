# Apps and Auto3DSeg Workflows

This reference covers high-level MONAI application orchestration. It intentionally distinguishes safe inspection from execution that may download data, analyze images, train models, run HPO, or spawn multi-GPU jobs.

## Workflow Ownership

| User goal | Use this route | Cross-link |
|---|---|---|
| Build an Auto3DSeg plan from a task YAML and Decathlon-style datalist | `AutoRunner`, `DataAnalyzer`, `BundleGen`, `EnsembleRunner` | `../../data-transforms/SKILL.md` for datalist/layout validation |
| Inspect or customize generated algorithm bundles | Auto3DSeg generates them; Bundle route edits/runs them | `../../bundle-config/SKILL.md` |
| Select model/loss/inferer/postprocessing by hand | Not this sub-skill | `../../modeling-inference/SKILL.md` |
| Build a custom training/evaluation loop | Not this sub-skill | `../../training-evaluation/SKILL.md` |
| Bridge a MONAI datalist into nnU-Net V2 | `nnUNetV2Runner` | data route for datalist; external nnU-Net tooling required |
| Use app dataset wrappers for examples or benchmarks | `MedNISTDataset`, `DecathlonDataset`, `TciaDataset`, `CrossValidation` | data route for transforms/caching details |

## Safe Versus Expensive Actions

| Action | Safe for quick inspection? | Why |
|---|---:|---|
| Import `monai.apps.auto3dseg` and inspect signatures | Yes | No training, no image reads, no downloads. |
| `python -m monai.apps.auto3dseg -- --help` | Yes | Fire help only, assuming `fire` is installed. |
| Construct `AutoRunner` with a valid config | Caution | Creates/uses a work directory and validates config path/dict. |
| `DataAnalyzer.get_all_case_stats()` | Expensive | Reads images and labels, may use CUDA/multiprocessing, writes stats. |
| `BundleGen.generate()` | Expensive/side-effecting | May download/extract templates and writes generated bundle folders. |
| `AutoRunner.run()` | Expensive | Can run analysis, bundle generation, training, HPO, and ensemble inference. |
| HPO with `NNIGen` or `OptunaGen` | Expensive and optional | Requires optional HPO backends and launches repeated training trials. |
| `nnUNetV2Runner.run()` or training commands | Expensive and external | Requires nnU-Net V2 package/data conventions and can spawn long GPU jobs. |
| Dataset helper `download=True` | Network side effect | Downloads and extracts external datasets when missing. |

## AutoRunner Planning Pattern

Use this pattern to prepare an Auto3DSeg plan without immediately training:

1. Validate the task input dictionary or YAML has at least `modality`, `datalist`, `dataroot`, `multigpu`, and `class_names` when segmentation labels are used.
2. Validate the datalist independently: `training` items should include `image`, `label`, and optional `fold`; `testing` items may include only `image` for unlabeled prediction.
3. Decide which phases are intended: analysis (`analyze`), algorithm generation (`algo_gen`), training (`train`), HPO (`hpo`), and ensemble inference (`ensemble`). Leave execution disabled until the user confirms runtime and hardware.
4. Decide `algos`: `None` uses available templates, a string/list narrows templates, and a dict is for custom algorithm definitions.
5. Use `templates_path_or_url` only when the template source is trusted and available; a remote/default template path may download content.
6. If running, start with minimal folds and training params only when the user explicitly wants a tiny smoke job; otherwise stop at config inspection.

Minimal input shape:

```yaml
name: my_segmentation_task
task: segmentation
modality: MRI
datalist: datalist.json
dataroot: data
multigpu: false
class_names: [lesion]
```

Example unlabeled test split:

```json
{
  "training": [
    {"fold": 0, "image": "imagesTr/case001.nii.gz", "label": "labelsTr/case001.nii.gz"},
    {"fold": 1, "image": "imagesTr/case002.nii.gz", "label": "labelsTr/case002.nii.gz"}
  ],
  "testing": [
    {"image": "imagesTs/case101.nii.gz"}
  ]
}
```

## DataAnalyzer Statistics Workflow

`DataAnalyzer` computes per-case and summary stats used by Auto3DSeg algorithms.

1. Confirm the datalist points to readable image files relative to `dataroot`.
2. Use `device="cpu"` for safe validation unless the user explicitly wants CUDA; default device is CUDA.
3. Set `label_key=None` or `label_key="None"` for unlabeled analysis; otherwise labels are expected for the selected key, typically `training`.
4. Keep `worker` low for local smoke checks; higher worker counts can multiply memory use.
5. Choose `fmt="yaml"` or `fmt="json"`; output defaults to `datastats.yaml`.
6. Inspect stats for channel count, spacing, label indices, foreground statistics, and shape uniformity before generating bundles.

Common call shape:

```python
from monai.apps.auto3dseg import DataAnalyzer

analyzer = DataAnalyzer(
    datalist="datalist.json",
    dataroot="data",
    output_path="work_dir/datastats.yaml",
    device="cpu",
    label_key="label",
)
stats = analyzer.get_all_case_stats()
```

## BundleGen and Generated Bundle Handoff

`BundleGen` consumes datastats and a data-source YAML to create algorithm bundle folders.

1. Ensure `datastats.yaml` exists and matches the current datalist/dataroot.
2. Ensure the data-source config includes `datalist`, `dataroot`, `modality`, `multigpu`, and `class_names` for segmentation tasks.
3. Use `templates_path_or_url` deliberately; missing templates may trigger downloads.
4. Use `num_fold=1` only for explicit tiny checks; production plans commonly use cross-validation folds from data or defaults.
5. After generation, each algorithm folder behaves like a MONAI bundle-like artifact; route config editing and run overrides to `../../bundle-config/SKILL.md`.

Typical generated work directory contents include `input.yaml`, `datastats.yaml`, `algorithm_templates`, per-algorithm folders such as `segresnet_0`, and later `ensemble_output` after inference.

## EnsembleRunner Workflow

Use `EnsembleRunner` only after algorithms have been generated and trained enough to expose prediction outputs or importable algorithm histories.

1. Verify `data_src_cfg_name` points to the same data source used for training.
2. Set `num_fold` to match generated/trained folds.
3. Pick `ensemble_method_name`, commonly `AlgoEnsembleBestByFold`.
4. Treat `mgpu=True` as a multi-GPU assumption; set `mgpu=False` for CPU/single-device planning unless hardware is confirmed.
5. Prediction parameters such as `files_slices`, `mode`, `sigmoid`, and `image_save_func` affect output selection and saving.

## HPO With NNIGen and OptunaGen

HPO is optional and training-heavy.

- `NNIGen` integrates with NNI and prints or exposes trial command patterns; it does not by itself run an NNI controller.
- `OptunaGen` is intended to be wrapped by an Optuna study and calls training for sampled hyperparameters.
- Confirm `nni` or `optuna` is importable before proposing execution.
- Keep search spaces tiny for smoke checks and document that real searches multiply training time and storage.
- Generated HPO trial folders contain copied/filled algorithm configs, checkpoints, and serialized algorithm objects.

## nnU-Net Bridge

`monai.apps.nnunet.nnUNetV2Runner` bridges MONAI-style datalists into nnU-Net V2 workflows.

1. Confirm optional `nnunetv2`, `batchgenerators`, and medical image IO dependencies are installed.
2. Input config requires `datalist`, `dataroot`, and `modality`.
3. Optional keys include `nnunet_raw`, `nnunet_preprocessed`, `nnunet_results`, `nnUNet_trained_models`, and `dataset_name_or_id`.
4. `dataset_name_or_id` must match a safe dataset identifier such as `Dataset001` or `1`.
5. Conversion and planning mutate nnU-Net working directories and environment variables; training is long-running.
6. Treat nnU-Net CLI examples as reference-only unless the user confirms external tooling, data layout, and GPU/runtime budget.

## Built-In Dataset and App Helpers

- `MedNISTDataset` creates train/validation/test sections from a MedNIST folder or archive and caches via `CacheDataset`; `download=True` can fetch external data.
- `DecathlonDataset` loads Medical Segmentation Decathlon tasks, exposes dataset properties, and expects task names like `Task09_Spleen`; `download=True` fetches/extracts data.
- `TciaDataset` uses TCIA metadata/download helpers and may require network access and DICOM readers.
- `CrossValidation` helps split existing datasets into folds; route transform/caching details to `../../data-transforms/SKILL.md`.

## Hard Synthetic Usability Cases

1. Dry-run AutoRunner plan: a user has a new 3D MRI segmentation dataset with `training` image/label pairs and an unlabeled `testing` split. The agent must validate config/datalist shape, choose CPU-safe inspection commands, avoid launching training/downloads, and explain when to route generated bundles to Bundle config help.
2. HPO/datastats triage: a user reports Auto3DSeg HPO fails. The agent must distinguish missing `datastats.yaml`, stale datalist/dataroot paths, missing optional `nni`/`optuna`, and accidental multi-GPU assumptions before suggesting any expensive rerun.
