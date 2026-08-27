# CLI Reference

DALLE2-pytorch 1.15.6 native launcher help was verified for the two training entry points. The public native flag surface is minimal:

- Decoder launcher accepts `--config_file TEXT` with native default `./train_decoder_config.json`.
- Diffusion-prior launcher accepts `--config_file TEXT` with native default `configs/train_prior_config.example.json`.

This skill provides bundled wrappers so future work does not depend on a source checkout script. Use the bundled wrapper paths below.

## Validate Before Launch

```bash
python skills/disco/dalle2-pytorch/sub-skills/training-and-configs/scripts/inspect_training_config.py --kind decoder --config decoder.json
python skills/disco/dalle2-pytorch/sub-skills/training-and-configs/scripts/inspect_training_config.py --kind prior --config prior.json
```

The inspector returns nonzero for JSON errors, Pydantic config errors, and additional launch-safety errors such as resampling without `epoch_samples` or prior `eval_timesteps` outside the allowed range.

## Build a Command Without Executing

```bash
python skills/disco/dalle2-pytorch/sub-skills/training-and-configs/scripts/training_command_builder.py --kind decoder --config decoder.json --launcher python
python skills/disco/dalle2-pytorch/sub-skills/training-and-configs/scripts/training_command_builder.py --kind prior --config prior.json --launcher accelerate --num-processes 2
```

The command builder prints one shell-quoted command and never executes it.

## Python Launcher Commands

Use `python` for a single-process run or for local CPU/GPU smoke checks:

```bash
python skills/disco/dalle2-pytorch/sub-skills/training-and-configs/scripts/run_decoder_training.py --config_file decoder.json
python skills/disco/dalle2-pytorch/sub-skills/training-and-configs/scripts/run_diffusion_prior_training.py --config_file prior.json
```

Training can run for a long time. The wrappers import the installed `dalle2_pytorch` package and use the validated JSON config to construct models, dataloaders, trackers, and trainers.

## Accelerate Launcher Commands

Use Accelerate after configuring the machine with the normal `accelerate config` workflow, or provide explicit launch flags:

```bash
accelerate launch --num_processes 2 skills/disco/dalle2-pytorch/sub-skills/training-and-configs/scripts/run_decoder_training.py --config_file decoder.json
accelerate launch --num_processes 2 skills/disco/dalle2-pytorch/sub-skills/training-and-configs/scripts/run_diffusion_prior_training.py --config_file prior.json
```

Notes:

- `--num_processes` belongs to `accelerate launch`, not to the DALLE2-pytorch wrapper.
- Accelerate mixed precision and DeepSpeed settings are launch/environment configuration, not JSON config keys.
- For decoder training, DeepSpeed fp16 with `decoder.learned_variance: true` is refused by the wrapper because that combination is unsupported.
- If using a CLIP adapter with DeepSpeed, use float32 precision unless you have verified a supported path.

## Wrapper Defaults

The bundled wrappers default to the safe templates inside this sub-skill tree:

- Decoder wrapper default: `references/config-templates/decoder-cpu-smoke.json`.
- Prior wrapper default: `references/config-templates/prior-minimal.json`.

Those templates contain placeholder data locations. Copy and edit them before any real training launch.

## Config Path Conventions

- Prefer explicit `--config_file` paths.
- Keep dataset URLs, tracker `data_path`, and local checkpoint destinations under a project run directory.
- Do not put API tokens directly in JSON configs. Use provider CLIs, environment variables, or token files managed outside the config and route details to `../data-and-tracking/`.
