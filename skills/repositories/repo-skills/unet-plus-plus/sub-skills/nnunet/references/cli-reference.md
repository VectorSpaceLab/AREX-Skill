# nnU-Net CLI reference

## Main console scripts

| Command | Purpose | Important flags |
| --- | --- | --- |
| `nnUNet_convert_decathlon_task` | Convert a Medical Segmentation Decathlon 4D task folder into nnU-Net's expected format | `-i`, `-p`, `-output_task_id` |
| `nnUNet_plan_and_preprocess` | Plan experiments and optionally preprocess tasks | `-t`, `-pl3d`, `-pl2d`, `-no_pp`, `-tl`, `-tf`, `--verify_dataset_integrity` |
| `nnUNet_train` | Train or validate a model | `network`, `network_trainer`, `task`, `fold`, `-val`, `-c`, `-p`, `--use_compressed_data`, `--deterministic`, `--npz`, `--find_lr`, `--valbest`, `--fp32`, `--val_folder` |
| `nnUNet_train_DP` | Data-parallel multi-GPU training | same core args as `nnUNet_train` plus `-gpus` and `--dbs` |
| `nnUNet_train_DDP` | Distributed data-parallel multi-GPU training | same core args as `nnUNet_train` plus `--local_rank`, `--dbs` |
| `nnUNet_predict` | Predict segmentations from a trained model folder | `-i`, `-o`, `-t`, `-tr`, `-ctr`, `-m`, `-p`, `-f`, `-z`, `-l`, `--part_id`, `--num_parts`, `--num_threads_preprocessing`, `--num_threads_nifti_save`, `--disable_tta`, `--overwrite_existing`, `--mode`, `--all_in_gpu`, `--step_size`, `-chk`, `--disable_mixed_precision` |
| `nnUNet_ensemble` | Merge `.npz` softmax predictions and optionally postprocess | `-f`, `-o`, `-t`, `-pp`, `--npz` |
| `nnUNet_determine_postprocessing` | Select postprocessing from validation outputs | `-m`, `-t`, `-tr`, `-pl`, `-val` |
| `nnUNet_find_best_configuration` | Compare model families and emit test-time prediction commands | `-m`, `-t`, `-tr`, `-ctr`, `-pl`, `-f`, `--strict` |
| `nnUNet_download_pretrained_model` | Download a built-in pretrained model by task name | `task_name` |
| `nnUNet_print_available_pretrained_models` | List all built-in pretrained models | none |
| `nnUNet_print_pretrained_model_info` | Print the dataset / modality summary for a pretrained model | `task_name` |
| `nnUNet_export_model_to_zip` | Package trained folds and postprocessing into a shareable zip | `-t`, `-o`, `-m`, `-tr`, `-trc`, `-pl`, `--disable_strict`, `-f` |
| `nnUNet_install_pretrained_model_from_zip` | Install a pretrained model archive | zip path |
| `nnUNet_change_trainer_class` | Rewrite trainer metadata in a saved model folder | `-i`, `-tr` |

## Common task/model choices

- `2d`, `3d_lowres`, `3d_fullres`, and `3d_cascade_fullres` are the main model
  families for training and inference.
- `nnUNetPlusPlusTrainerV2` is the default trainer class for this repository's
  UNet++ variant.
- `TaskXXX` may be either a task name or an integer task id, depending on the
  CLI.

## Flag notes that matter in practice

- `--use_compressed_data` trades disk space for more CPU/RAM pressure.
- `--npz` is needed if you plan to ensemble predictions later.
- `--disable_tta` speeds up inference but reduces accuracy.
- `--disable_mixed_precision` should be left off unless you have a reason.
- `--overwrite_existing` can replace predictions in a target output folder.

## Advanced / cautionary commands

- Treat `nnUNet_train_DP` and `nnUNet_train_DDP` as advanced multi-GPU routes.
- Treat `nnUNet_change_trainer_class` as an advanced checkpoint-metadata repair
  tool; back up the folder first.
- Treat the pretrained-model download commands as network- and license-sensitive
  operations.
