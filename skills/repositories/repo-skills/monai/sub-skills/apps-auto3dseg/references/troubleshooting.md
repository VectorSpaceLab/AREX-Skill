# Apps and Auto3DSeg Troubleshooting

Use this matrix to diagnose high-level MONAI application failures before launching expensive reruns.

## Quick Triage Order

1. Confirm MONAI imports: `monai`, `monai.apps.auto3dseg`, `monai.auto3dseg`, and any optional backend package.
2. Inspect the Auto3DSeg or nnU-Net CLI help instead of running workflows.
3. Validate YAML/JSON configs and datalist structure independently.
4. Confirm image/label paths exist relative to `dataroot` and match expected channel/label layout.
5. Check whether missing outputs are from skipped cached phases, missing datastats, or an intentionally disabled phase.
6. Ask before running analysis, training, HPO, ensemble inference, nnU-Net conversion/training, or dataset downloads.

## Configuration and YAML Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `input is not a valid file or dict` from `AutoRunner` or `nnUNetV2Runner` | `input`/`input_config` is not a dict and not an existing config file | Pass a Python dict or a real YAML/JSON path; avoid shell quoting mistakes with JSON strings. |
| Missing `datalist`, `dataroot`, or `modality` | Incomplete Auto3DSeg task config | Add the required keys and verify paths before constructing the runner. |
| Generated bundles use stale data | `datastats.yaml` or `input.yaml` came from an older datalist/dataroot | Delete/recompute stale outputs or set `not_use_cache=True` only after confirming an expensive rerun is intended. |
| Config parses but training fails immediately | Template-specific required fields are missing, such as `class_names` or `multigpu` | Compare the data-source config against the schema in `api-reference.md`. |
| Fire CLI receives malformed arguments | Shell quoting broke nested JSON/YAML/override strings | Prefer a config file over inline JSON for complex inputs. |

## Datalist and Image/Label Layout

| Symptom | Likely cause | Fix |
|---|---|---|
| `training` key not found | Datalist does not use Decathlon-style sections | Use `training`, optional `validation`, and optional `testing` keys. |
| `label` missing for training cases | Segmentation analysis/training expects labels unless `label_key=None` | Add labels for supervised training or explicitly run unlabeled analysis only. |
| Testing split has no labels | Normal for prediction | Keep testing items as `{"image": ...}` and do not force label stats for testing. |
| Shape mismatch between image and label | Spacing/cropping/export issue or label saved differently | Validate with data route; small differences may be handled by `allowed_shape_difference`, but large mismatches need data repair. |
| Multi-modal image stats fail or look inconsistent | Channels/modalities have different affine/spacing | Normalize layout and metadata before Auto3DSeg; route detailed transform fixes to `../../data-transforms/SKILL.md`. |
| Label stats look wrong | Labels are one-hot, missing channel dimension, or use unexpected class indices | Prefer label shape `(1,H,W,D)` with index values; verify class indices match `class_names`. |
| Image reader error | Optional reader dependency missing or unsupported format | Install the needed reader package or convert data to a supported format; use data route for reader selection. |

## DataAnalyzer Problems

| Symptom | Likely cause | Fix |
|---|---|---|
| CUDA error during stats | Default `device='cuda'` used on unavailable/insufficient GPU | Use `device='cpu'` for inspection or confirm GPU availability before rerunning. |
| Multiprocessing or memory failure | `worker` too high or images too large | Lower `worker`, use CPU first, reduce concurrent jobs, or analyze a representative subset. |
| Output file overwritten warning | `output_path` already exists | Confirm whether overwriting datastats is intended; otherwise choose a new work directory. |
| NaN/inf in stats | Image intensity contains invalid numeric values | Validate and clean images before using stats to generate algorithms. |
| Histogram request is slow | `hist_bins`/`histogram_only` still reads all selected images | Use a small subset for smoke checks or skip histograms until needed. |

## BundleGen and Generated Bundle Handoff

| Symptom | Likely cause | Fix |
|---|---|---|
| Template download or extraction fails | Remote template URL unavailable or network blocked | Provide a trusted local template directory or defer generation. |
| Algorithm skipped unexpectedly | `allow_skip=True` and datastats indicate unsuitable conditions | Inspect skip reason, datastats, image dimensions, and class metadata before forcing `allow_skip=False`. |
| Generated folder exists but bundle run fails | Bundle config/script issue rather than app-level routing | Use `../../bundle-config/SKILL.md` for config syntax, CLI overrides, metadata, and run verification. |
| Imported algorithm history missing | Work directory moved or serialized paths no longer resolve | Use Auto3DSeg history import/export utilities or regenerate from current work directory. |
| MLflow/tracking errors | Optional tracking dependencies or tracking URI unavailable | Disable tracking or install/configure the tracking backend deliberately. |

## Training, HPO, and Runtime Cost

| Symptom | Likely cause | Fix |
|---|---|---|
| AutoRunner starts long GPU jobs | `train=True` or default phase auto-detection enabled after analysis/generation | Set phase switches deliberately and ask before `AutoRunner.run()`. |
| HPO command fails with missing `nni` | NNI optional dependency not installed | Install NNI only if HPO is required, or run without `hpo=True`. |
| Optuna study import fails | Optuna optional dependency not installed | Install Optuna only for Optuna workflows; do not claim it is part of the base install. |
| HPO creates many folders/checkpoints | Search space and folds multiply training runs | Reduce folds/search space for smoke checks and document storage needs. |
| Multi-GPU launch fails | `multigpu=True`, `mgpu=True`, torchrun/bcprun environment, or CUDA device assumptions mismatch hardware | Set single-device flags for local checks; confirm scheduler/launcher before production. |
| TensorBoard/summary writer skip | Optional tracking dependency absent | Install the optional dependency or disable related tests/tracking. |

## EnsembleRunner Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| No files for inference | Datalist has no `testing` key or wrong data key | Add `testing` items or pass `infer_files` explicitly. |
| No trained algorithms found | Bundle generation ran but training did not complete | Confirm checkpoint/history availability before ensemble. |
| Ensemble output has unexpected labels | `sigmoid`, `mode`, or class/channel settings mismatch the task | Check `mode` (`mean`/`vote`), `sigmoid`, class count, and postprocessing route. |
| SaveImage output path surprise | `image_save_func` controls output writing | Inspect `image_save_func` config and route lower-level save behavior to data/modeling routes. |

## nnU-Net Bridge Failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Import error for `nnunetv2` or `batchgenerators` | Optional nnU-Net dependencies absent | Install and validate nnU-Net V2 separately before using the bridge. |
| Invalid `dataset_name_or_id` | ID does not match `Dataset###` or numeric format | Use a safe value such as `Dataset001` or `1`. |
| Conversion mutates unexpected directories | Optional nnU-Net paths default under the work directory and env vars are set | Provide explicit nnU-Net directories and review before conversion. |
| Training ignores `CUDA_VISIBLE_DEVICES` expectations | nnU-Net runner has its own GPU command patterns | Use runner arguments such as GPU selections where supported and confirm hardware. |
| Best configuration or prediction fails | Prior planning/training outputs missing | Run required nnU-Net stages in order after confirming external tooling and runtime budget. |

## Dataset Helper and Download Issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `Root directory root_dir must be a directory` | Dataset wrapper root does not exist | Create the root directory before constructing the wrapper. |
| Dataset directory missing with `download=False` | Archive/folder not already present | Place data manually or ask before using `download=True`. |
| Network/hash failure | Dataset download unavailable or corrupted | Retry in a network-enabled environment or provide a verified local archive. |
| Cache initialization is slow or memory-heavy | `cache_rate=1.0` and large dataset | Lower `cache_rate`, `cache_num`, or route cache tuning to `../../data-transforms/SKILL.md`. |
| TCIA/DICOM load failure | Network, metadata, or optional DICOM reader issue | Confirm TCIA access and DICOM dependencies; use data route for reader details. |

## When to Escalate to Other MONAI Routes

- Use `../../data-transforms/SKILL.md` for datalist conversion, image readers, metadata, transforms, channel-first conversion, caching, and collate failures.
- Use `../../bundle-config/SKILL.md` for generated bundle config syntax, `_target_`, overrides, metadata validation, bundle CLI run/export, and generated bundle reproducibility.
- Use `../../modeling-inference/SKILL.md` for loss/metric/inferer/postprocessing, sliding-window inference, and prediction tensor shape issues.
- Use `../../training-evaluation/SKILL.md` for custom training loops, Ignite engines, handlers, checkpointing, AMP, and distributed training patterns.
