# Configuration and CLI troubleshooting

Use this when static config validation or `imagen` CLI commands fail before, during, or immediately after command dispatch. For model-quality, tensor-shape, dataloader, checkpoint-internals, or video semantics, follow the route links in `SKILL.md`.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `imagen` command not found | Package is not installed in the active environment or console scripts are not on `PATH`. | Activate the intended package environment or install the package. Then run the bundled quickcheck script. |
| `imagen_pytorch` prints nothing or appears to do nothing | `imagen_pytorch` is a no-op entry point. | Use `imagen config`, `imagen train`, or `imagen sample`. |
| `No such option: --epochs` | The CLI option is misspelled in the package as `--epoches`. | Use `--epoches INTEGER`, for example `imagen train --epoches 1`. |
| `Invalid value for --unet` or third-stage training cannot be selected | Click range is `[1<=x<3]`, so only unet 1 and 2 are accepted by CLI train. | Train unet 1 or 2 via CLI. For a third cascade stage, use a custom training script or patch the CLI. |
| `config not found at ...` | `imagen train --config` points to a missing file. | Run `imagen config --path ...`, copy a template, or fix the path before training. |
| `checkpoint path not found in config` | Top-level `checkpoint_path` key is missing. | Add a string path such as `"checkpoint_path": "./imagen.pt"`. A missing file starts new training; an existing file resumes. |
| Final checkpoint save fails with missing parent directory | `checkpoint_path` parent does not exist. | Create the parent directory before training or use a simple local path such as `./imagen.pt`. |
| `A batch_size is required in the config file` | `dataset.batch_size` is missing. | Add positive integer `dataset.batch_size`; start small for smoke/preflight configs. |
| DataLoader complains about batch size | `dataset.batch_size` is not a positive integer. | Use an integer >= 1. Large values such as the default 2048 require substantial hardware. |
| Dataset loading is slow, downloads unexpectedly, or needs credentials | `dataset_name` is loaded through Hugging Face `load_dataset`, and `url_label` triggers image URL downloads. | Route dataset design to `../data-and-text-conditioning/SKILL.md`; use a small known dataset/cache for preflight. |
| T5 or tokenizer downloads occur | CLI collator and config creation can use the configured T5 model name. | Prefer explicit local/cache planning; use tiny validation configs only for static checks. |
| `validate_at_every must be an integer`, `sample_at_every must be an integer`, or `save_at_every must be an integer` | Interval field is not a JSON integer. | Use integers, not strings or floats. Prefer positive integers to avoid modulo errors. |
| `ZeroDivisionError` near validation or save/sample intervals | The CLI computes modulo before all guard conditions and uses zero when a guarded interval is considered disabled. | Include positive integer `validate_at_every` and `save_at_every`; set `trainer.split_valid_from_train: true` when using validation; consider disabling in-loop sample on first runs. |
| `sample_texts must not be empty when sample_at_every is set` | Sampling during training is enabled but prompt list is empty. | Either remove `sample_at_every` and `sample_texts` for first training runs, or provide a non-empty list of strings. |
| In-loop samples receive unexpected text shape | The CLI wraps `sample_texts` as `[sample_texts]` in the sample call. | Prefer separate `imagen sample` or a Python sampling script for reliable sampling workflows. |
| `Imagen only support 1 to 4 channels L, LA, RGB, RGBA` | `imagen.channels` is outside 1-4. | Use 1, 3, or 4 for CLI runs. Channel 2 is intended as `LA` but has a CLI assignment typo. |
| Channel 2 still behaves like RGB | The CLI source compares instead of assigning `channels == 'LA'`. | Avoid channel 2 through CLI or patch the command before relying on it. |
| Config validation says `image_sizes` length differs from `unets` | Pydantic decoder config requires one image size per unet. | Add/remove cascade stages so lengths match. |
| Config validation warns about `random_crop_sizes[0]` | Decoder asserts base unet should not random-crop. | Use `null` for the first crop value, e.g. `[null, 64, 256]`. |
| `imagen sample` says model not found | `--model` points to a missing checkpoint. | Use the correct path. For training configs, this is often the top-level `checkpoint_path`. |
| `unknown imagen type ...` or `imagen type and configuration not saved in this checkpoint` | Checkpoint was not saved with config metadata. | Save through `ImagenTrainer.save` after constructing the decoder with `ImagenConfig` or `ElucidatedImagenConfig`; raw `state_dict` files are not CLI-sample compatible. |
| CUDA error or no CUDA device during `imagen sample` | The sample command calls `.cuda()` unconditionally. | Run sampling CLI only on CUDA-capable machines; for CPU/debug loading, write a Python path via `../image-generation/SKILL.md`. |
| `--load_ema` behaves unexpectedly in shell scripts | The option is typed as a Click boolean. | Pass explicit `--load_ema true` or `--load_ema false`. |
| Generated LAION config is too large for local testing | Default config targets LAION, T5-large, 1024px cascade, and batch size 2048. | Treat it as a schema template. Convert to a tiny static-validation config before any local training attempt. |
