# Configuration Troubleshooting

- **`only support yaml files for now`**: pass a `.yml`/`.yaml` file, not an exported `infer_cfg.yml` to training config loading unless the workflow explicitly expects it.
- **`Please specify --config`**: `ArgsParser` requires `-c/--config` even for train/eval/infer/export parsers. Use `--help` before constructing a command.
- **`No module named ...` for a custom component**: import the module that performs `@register` before config loading, or package the custom component so the target Python can import it.
- **Missing `architecture`/`num_classes`**: the YAML is incomplete or the wrong base was selected. Load the config and inspect both fields before starting the job.
- **Wrong class count or metric**: change the dataset label list and `num_classes` together; choose `COCO`, `VOC`, `MOT`, or keypoint metrics consistent with the annotation schema.
- **Remote config 404 at `configs/0.0.0.tar`**: the source build's advertised package version is `0.0.0`, so the remote versioned archive is unavailable. Use a local config or a released package/cache; do not repeatedly retry the same URL.
- **Model construction exhausts memory**: switch to a smaller family/config, use `mode='test'`, lower input/batch size, or validate only YAML syntax before constructing the model.
