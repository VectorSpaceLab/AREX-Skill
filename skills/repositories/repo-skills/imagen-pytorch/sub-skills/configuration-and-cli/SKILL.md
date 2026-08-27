---
name: configuration-and-cli
description: "Author and validate imagen-pytorch configs and safely use the
  imagen config, train, and sample CLI commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# configuration-and-cli

Use this sub-skill when the task mentions imagen config JSON, `default_config.json`, `UnetConfig`, `ImagenConfig`, `ElucidatedImagenConfig`, `ImagenTrainerConfig`, CLI train/sample commands, config validation, command generation, or safe preflight checks for the `imagen` console command.

## Fast route

1. Read [configuration](references/configuration.md) to choose the JSON schema (`type: "original"` or `"elucidated"`), cascade length, image sizes, channel count, dataset/checkpoint keys, and sample/save/validation interval keys.
2. Use [default-config-template.json](references/default-config-template.json) only as a LAION-scale template. It is not a safe local training default.
3. From this sub-skill directory, validate before running anything expensive:
   ```bash
   python scripts/validate_imagen_config.py path/to/imagen_config.json --mode train --unet 1
   ```
4. From this sub-skill directory, check the installed CLI surface without training or sampling:
   ```bash
   python scripts/imagen_cli_quickcheck.py
   ```
5. Generate or run commands from [CLI reference](references/cli-reference.md). Use the exact `--epoches` spelling for training.
6. If validation or CLI use fails, consult [troubleshooting](references/troubleshooting.md).

## Command workflow

- Create a starter config: `imagen config --path ./imagen_config.json`.
- Edit the config, especially `dataset_name`, `dataset.batch_size`, labels, `checkpoint_path`, `imagen.image_sizes`, `imagen.unets`, interval keys, and practical model sizes.
- Preflight with the bundled validator; do not let `imagen train` be the first validator because it loads datasets and can enter expensive training.
- Train with `imagen train --config ./imagen_config.json --unet 1 --epoches 1` only after dataset and hardware are intentionally chosen.
- Sample with `imagen sample --model ./imagen.pt --cond_scale 5 --load_ema true "prompt"` only from a commandable trainer checkpoint and on a CUDA-capable runtime.

## Boundaries and handoffs

- Training loop internals, checkpoint save/load mechanics, EMA behavior, and distributed training: route to [training-and-checkpointing](../training-and-checkpointing/SKILL.md).
- Image sampling tensor semantics, prompt conditioning, inpainting image tensors, and quality/performance tuning: route to [image-generation](../image-generation/SKILL.md).
- Video configs and 3D/video tensor details beyond the `video: true` config switch: route to [video-and-inpainting](../video-and-inpainting/SKILL.md).
- Dataset construction, collators, URL/image/text labels, and T5 embedding/data-loader details: route to [data-and-text-conditioning](../data-and-text-conditioning/SKILL.md).

Keep this sub-skill focused on static configuration, CLI flags, command preflights, and safe command construction. Do not use it as proof of generation quality; CUDA import smoke was verified for the package, but realistic Imagen training and sampling remain practical CUDA-scale work.
