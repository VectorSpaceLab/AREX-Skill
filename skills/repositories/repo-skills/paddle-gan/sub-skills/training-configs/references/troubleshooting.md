# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `config file(...) is not exist` | Wrong `-c` path | Point `--config-file` at an existing YAML file. |
| `option(...) should contain a =` or a key-path error | Malformed `-o` token | Use `key=value` pairs and make sure the key path already exists. |
| `No object named 'X' found in 'MODEL' registry!` | Wrong `name` value or missing import path | Use a registered class name from the config reference. |
| `Trainer` fails before `test()` in `--evaluate-only` mode | The trainer still builds the train dataloader, scheduler, and optimizers | Keep `dataset.train`, `optimizer`, and `lr_scheduler` valid, or use `--show-config` for a parse-only check. |
| `Can not find state dict of net ...` | The loaded weights do not contain every network key | Use a checkpoint from the same model family or a per-net weight dict with matching names. |
| `checkpoint only contain weight of one net...` | Single-network weights were passed to a multi-network model | Use the matching checkpoint format or a config-consistent checkpoint. |
| `visualdl` import error | Optional dependency is not installed | Install VisualDL or leave `enable_visualdl` off. |
| AMP errors, NaNs, or unstable loss with `--amp` | The model does not support the AMP path, or `O2` is too aggressive | Start with `--amp_level O1`; only use `O2` when the model handles pure fp16 well. |
| Distributed training hangs or warns about unused parameters | Launch shape or `find_unused_parameters` mismatch | Use `CUDA_VISIBLE_DEVICES=... python -m paddle.distributed.launch ...` and keep the config's `find_unused_parameters` setting. |
| Validation tries to download Inception weights | `FID` was enabled without a cached `premodel_path` | Set `validate.metrics.fid.premodel_path` to a local file. |
| Output folder name does not match the model class | The runner names outputs from the config file stem | This is expected: use `output_dir/<config-stem>-<timestamp>/`. |
| `--no-cuda` seems to do nothing | The current setup auto-selects the backend from the Paddle build | Use a CPU-only Paddle build if you need CPU-only execution. |
| `--val-interval` does not change validation cadence | The trainer reads `validate.interval` from YAML | Override `validate.interval` instead. |
| `checkpoints_dir` does not affect generic output paths | The trainer writes its own artifacts under `output_dir` | Treat `checkpoints_dir` as model-specific if a config uses it. |

## When to stop and switch paths

- Dataset download or preprocessing errors belong to the data-preparation sub-skill.
- Export / inference / deployment errors belong to the deployment-export sub-skill.
- Image or video application inference errors belong to the app sub-skills.
