# nnU-Net troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `nnUNet_raw_data_base`, `nnUNet_preprocessed`, or `RESULTS_FOLDER` missing | The public path variables were not set | Set all three before planning, training, or inference |
| `nnUNet_plan_and_preprocess` cannot find the dataset | The Task folder name or layout is wrong | Use `TaskXXX_Name/imagesTr`, `labelsTr`, and `imagesTs` with clean file names |
| Hidden files break conversion or validation | macOS / IDE metadata files were left in the task folder | Remove dotfiles from the task directories before conversion |
| `ImportError: cannot import name 'MultiThreadedAugmenter'` | `batchgenerators` is too new for this snapshot | Pin or reinstall a compatible release; the inspected snapshot needed `batchgenerators==0.21` |
| `ModuleNotFoundError: matplotlib` during CLI import | `nnUNet_train` imports trainer code that expects matplotlib | Install `matplotlib` in the nnU-Net environment |
| `ModuleNotFoundError: requests` for pretrained-model helpers | The pretrained-model CLI needs `requests` | Install `requests` before using download/list/info helpers |
| Prediction or training command mentions an unexpected trainer class | The checkpoint metadata or CLI trainer name is stale | Use `nnUNet_change_trainer_class` carefully after backing up the model folder |
| Multi-GPU DP/DDP script fails or looks inconsistent with the default path | The advanced entry point is older and more brittle than the default training route | Prefer the default single-node trainer unless you need multi-GPU specifically |
| Predictions complain about output size or tmp `.npy` files | Python process communication is too large for the requested volume | Let the helper spill to disk; keep enough local disk space |
| `nnUNet_download_pretrained_model` overwrites a model | The archive targets an existing trainer/plans folder | Check the target and use a backup-first workflow |
| `RESULTS_FOLDER` warnings appear in every CLI | The env vars are unset in a shell that only imported the package | Export the variables in the active environment before running any CLI |

## Good recovery sequence

1. Check the path variables.
2. Check `pip check`.
3. Check that `batchgenerators.dataloading.MultiThreadedAugmenter` imports.
4. Check `torch.cuda.is_available()`.
5. Re-run the CLI with `--help` before attempting a full workflow.

## Safety note

Do not treat `nnUNet_train --help` or a plain package import as proof that the
GPU training path is ready. Use the CUDA-aware smoke script and the backend plan
from the creation workflow.
