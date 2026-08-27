# CLI Map

Use `-h` on any command before relying on uncommon flags. Command behavior can vary across nnU-Net releases.

| Command | Owner | Use for | Safe verification |
| --- | --- | --- | --- |
| `nnUNetv2_convert_MSD_dataset` | `data-preparation` | Convert Medical Segmentation Decathlon layout to nnU-Net v2 format | `-h`; real conversion needs data |
| `nnUNetv2_convert_old_nnUNet_dataset` | `data-preparation` | Convert nnU-Net v1 raw datasets to v2 layout | `-h`; real conversion needs data |
| `nnUNetv2_plan_and_preprocess` | `planning-preprocessing` | Run fingerprinting, planning, and preprocessing in one command | `-h`; full run can be expensive |
| `nnUNetv2_extract_fingerprint` | `planning-preprocessing` | Generate or refresh dataset fingerprint only | `-h`; full run reads images |
| `nnUNetv2_plan_experiment` | `planning-preprocessing` | Generate plans/configurations from fingerprint | `-h`; requires fingerprint/data |
| `nnUNetv2_preprocess` | `planning-preprocessing` | Materialize preprocessed arrays for configurations | `-h`; full run can be large |
| `nnUNetv2_move_plans_between_datasets` | `planning-preprocessing` | Reuse plan identifiers for pretraining/fine-tuning workflows | `-h`; requires plans files |
| `nnUNetv2_train` | `training-configuration` | Train, continue, validate, export validation probabilities, or use pretrained weights | `-h`; training is expensive |
| `nnUNetv2_predict` | `inference-evaluation` | Predict from `nnUNet_results` by dataset/configuration/fold/checkpoint | `-h`; full run needs trained model |
| `nnUNetv2_predict_from_modelfolder` | `inference-evaluation` | Predict from an explicit model folder | `-h`; full run needs model folder |
| `nnUNetv2_find_best_configuration` | `inference-evaluation` | Compare trained configurations and determine postprocessing/inference commands | `-h`; requires validation outputs |
| `nnUNetv2_accumulate_crossval_results` | `inference-evaluation` | Aggregate cross-validation outputs | `-h`; requires trained folds |
| `nnUNetv2_determine_postprocessing` | `inference-evaluation` | Determine postprocessing separately | `-h`; requires validation predictions |
| `nnUNetv2_apply_postprocessing` | `inference-evaluation` | Apply stored postprocessing to predictions | `-h`; requires prediction folder and metadata |
| `nnUNetv2_ensemble` | `inference-evaluation` | Ensemble probability outputs from multiple prediction folders | `-h`; inputs need saved probabilities |
| `nnUNetv2_evaluate_folder` | `inference-evaluation` | Evaluate prediction folder against references | `-h`; requires image folders and metadata |
| `nnUNetv2_evaluate_simple` | `inference-evaluation` | Simpler evaluation entry point | `-h`; requires image folders |
| `nnUNetv2_export_model_to_zip` | `inference-evaluation` | Export a trained model bundle | `-h`; requires trained model output |
| `nnUNetv2_install_pretrained_model_from_zip` | `inference-evaluation` | Install a model bundle from zip | `-h`; mutates model storage |
| `nnUNetv2_download_pretrained_model_by_url` | `inference-evaluation` | Download/install model bundle by URL | `-h`; network side effects |
| `nnUNetv2_plot_overlay_pngs` | `inference-evaluation` | Create overlay PNGs for visual inspection | `-h`; writes image outputs |

## Programmatic API Anchors

- `nnunetv2.paths`: lazy path objects for `nnUNet_raw`, `nnUNet_preprocessed`, `nnUNet_results`, and `nnUNet_extTrainer`.
- `nnunetv2.experiment_planning.plan_and_preprocess_api.extract_fingerprints`: API for fingerprint extraction.
- `nnunetv2.experiment_planning.plan_and_preprocess_api.preprocess`: API for preprocessing existing plans/configurations.
- `nnunetv2.run.run_training.run_training`: API behind training workflows.
- `nnunetv2.inference.predict_from_raw_data.nnUNetPredictor`: reusable predictor class for Python inference workflows.
- `nnunetv2.utilities.find_class_by_name` and related discovery utilities: class lookup for custom trainers and extension points.

## Command Safety

- Help checks are safe: `COMMAND -h`.
- Dry-run helpers bundled in this skill are safe because they only inspect files or print commands.
- Dataset conversion, preprocessing, training, prediction, ensembling, postprocessing, model install/download, and overlay generation can read/write large data, use GPUs, or require network/model artifacts.
