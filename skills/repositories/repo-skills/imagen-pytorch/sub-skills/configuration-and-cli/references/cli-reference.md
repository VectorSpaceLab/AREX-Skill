# CLI reference

The public package installs two console entry points:

- `imagen`: Click command group with `config`, `train`, and `sample` subcommands.
- `imagen_pytorch`: calls a no-op function and is not the operational CLI.

From the `configuration-and-cli` sub-skill directory, use the bundled quickcheck before relying on an environment:

```bash
python scripts/imagen_cli_quickcheck.py
```

## Command group

```text
imagen [OPTIONS] COMMAND [ARGS]...
```

Commands:

- `config` - Generate a config for the Imagen model.
- `train` - Train the Imagen model.
- `sample` - Sample from the Imagen model checkpoint.

## `imagen config`

Verified help surface:

```text
imagen config [OPTIONS]

Options:
  --path TEXT  Path to the Imagen model config
  --help       Show this message and exit.
```

Default behavior:

```bash
imagen config
# writes ./imagen_config.json
```

Custom path:

```bash
imagen config --path ./configs/imagen_config.json
```

Safe notes:

- The command writes the package default JSON verbatim.
- It does not create missing parent directories; create `./configs` first.
- The generated config is LAION-scale and should be edited before training.
- From the `configuration-and-cli` sub-skill directory, validate after editing:
  ```bash
  python scripts/validate_imagen_config.py ./configs/imagen_config.json --mode train --unet 1
  ```

## `imagen train`

Verified help surface:

```text
imagen train [OPTIONS]

Options:
  --config TEXT              Path to the Imagen model config
  --unet INTEGER RANGE       Unet to train  [1<=x<3]
  --epoches INTEGER          Amount of epoches to train for
  --help                     Show this message and exit.
```

Defaults:

- `--config ./imagen_config.json`
- `--unet 1`
- `--epoches 50`

Example with exact option spelling:

```bash
imagen train --config ./imagen_config.json --unet 1 --epoches 1
```

Important constraints:

- The option is misspelled as `--epoches`; `--epochs` is not accepted.
- The Click range is `[1<=x<3]`, so CLI train accepts only unet 1 or 2 even if the config has three unets.
- The command asserts the config path exists and asserts `checkpoint_path` exists as a key inside JSON.
- If `checkpoint_path` already exists, it resumes via `trainer.load`; otherwise it starts a new checkpoint and saves at the end.
- The command loads a Hugging Face dataset before training, builds a CLI collator, and may download URL images and T5 assets.
- Training quality and realistic generation are practical CUDA-scale. A CUDA torch smoke can prove basic availability, but not model quality.
- The implementation performs interval modulo checks before all guard conditions. Keep positive integer `validate_at_every` and `save_at_every`; set `trainer.split_valid_from_train: true` if using validation through CLI train.

From the `configuration-and-cli` sub-skill directory, preflight before a real run:

```bash
python scripts/validate_imagen_config.py ./imagen_config.json --mode train --unet 1
```

Route after preflight:

- Training loop design, checkpoint format, resume semantics, and EMA: `../training-and-checkpointing/SKILL.md`.
- Dataset labels, URL/image loading, T5 encoding, and collator behavior: `../data-and-text-conditioning/SKILL.md`.

## `imagen sample`

Verified help surface:

```text
imagen sample [OPTIONS] TEXT

Options:
  --model TEXT          path to trained Imagen model
  --cond_scale INTEGER  conditioning scale (classifier free guidance) in decoder
  --load_ema BOOLEAN   load EMA version of unets if available
  --help               Show this message and exit.
```

Defaults:

- `--model ./imagen.pt`
- `--cond_scale 5`
- `--load_ema true`

Example:

```bash
imagen sample --model ./imagen.pt --cond_scale 5 --load_ema true "a squirrel raiding the birdfeeder"
```

Output behavior:

- The command saves a PNG in the current working directory using a slugified prompt such as `./a_squirrel_raiding_the_birdfeeder.png`.
- The prompt is a required positional `TEXT` argument.

Checkpoint constraints:

- `--model` must point to an existing trainer checkpoint.
- The checkpoint must contain commandable config metadata: `imagen_type` equal to `original` or `elucidated`, plus `imagen_params` saved by constructing the decoder through `ImagenConfig` or `ElucidatedImagenConfig` before `ImagenTrainer.save`.
- A raw `state_dict`, a checkpoint saved from a manually constructed `Imagen` without config metadata, or an arbitrary `.pt` file is not CLI-sample compatible.
- The command calls `.cuda()` unconditionally after loading. Use it only on a CUDA-capable runtime, or write a Python sampling script routed through `../image-generation/SKILL.md` for CPU/debug-only loading.
- `--cond_scale` is typed as an integer by the CLI. For non-integer classifier-free guidance scales, use the Python API rather than this CLI command.
- `--load_ema` is a Click boolean value; pass explicit values such as `true` or `false` to avoid shell/script ambiguity.

## Safe command-generation checklist

Before emitting a CLI command for another agent or user, confirm:

1. The executable is `imagen`, not `imagen_pytorch`.
2. The config path or model path exists, or the command intentionally creates the config file.
3. `imagen train` uses `--epoches`, not `--epochs`.
4. The target unet is 1 or 2 for CLI train.
5. `dataset.batch_size` is a positive integer.
6. `checkpoint_path` is present in training configs.
7. `validate_at_every`, `save_at_every`, and sampling interval fields are positive integers when present.
8. `sample_texts` is non-empty if `sample_at_every` is set.
9. `imagen.channels` is 1, 3, or 4 for CLI runs; avoid 2 unless the local CLI is patched.
10. `imagen sample` is run only with a commandable trainer checkpoint and CUDA availability.
