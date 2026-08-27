# Training CLI

## Purpose

Read this when a future agent must run, dry-run, or modify an H2O LLM Studio experiment command. This reference covers launch mechanics only; build or validate the YAML with the configuration/data sub-skill first.

## Direct CLI entry points

The current training entry point accepts exactly one primary config source:

```bash
python llm_studio/train.py -Y <config.yaml>
```

`-Y`/`--yaml` loads a YAML experiment config. The older `-C`/`--config` path loads a Python config and emits a deprecation warning; prefer YAML for new work:

```bash
python llm_studio/train.py -C <legacy-python-config.py>
```

If neither `-Y` nor `-C` is supplied, the trainer raises `Please, provide a configuration file`.

When running from a project managed by `uv`, the same command can be prefixed with `uv run`. When running from an already activated Python environment, omit `uv run`.

## Dynamic config overrides

After loading the config, the trainer scans unknown CLI arguments with the shape `--section.field`. If the section and field exist on the loaded config, the argument is parsed to that field's annotated type and assigned before `run(cfg)` starts.

Examples:

```bash
python llm_studio/train.py -Y cfg.yaml \
  --training.epochs 0 \
  --training.learning_rate 0.00005 \
  --training.save_checkpoint disable \
  --environment.mixed_precision false \
  --output_directory ./outputs/smoke-eval
```

Practical rules:

- Use the exact YAML section and field names, for example `training.epochs`, `environment.use_deepspeed`, or `prediction.metric`.
- Boolean overrides are parsed from common truthy/falsy strings such as `true`, `false`, `1`, and `0`.
- Unknown or misspelled override fields are skipped while the command continues. If a value did not change, inspect the final `cfg.yaml` saved in the experiment output directory.
- Overrides do not replace dataset/schema validation. If an override changes columns, problem type, or paths, validate with the configuration/data sub-skill first.

## Output directory startup behavior

`cfg.output_directory` is created before training starts. During a normal run, rank 0 writes the resolved config back to `<output_directory>/cfg.yaml`, initializes logging, trains/evaluates, saves artifacts, and writes `flags.json` with status `finished` plus a runtime string.

Use [experiment-artifacts.md](experiment-artifacts.md) to inspect output completeness.

## GUI-launched training behavior

The GUI writes a resolved `cfg.yaml` inside the experiment output directory and launches `llm_studio/train_wave.py -Y <that cfg.yaml>`. The Wave launcher adds status flags:

- before work starts: `flags.json` status `running`;
- normal completion: `flags.json` status `finished`;
- failure: `flags.json` or per-rank `flags<N>.json` status `failed` with short `info` such as `OOM error`, `Data error`, `Training error`, `Metric error`, `Model error`, or `See logs`.

The GUI launcher may queue experiments with `-Q <pid-list>` and waits for listed process IDs before starting the next experiment.

## Multi-GPU launch patterns

The repository's simple distributed launcher is equivalent to:

```bash
torchrun --nproc_per_node=<num_gpus> llm_studio/train.py -Y <config.yaml>
```

The bundled wrapper adds argument validation and dry-run safety:

```bash
sub-skills/training-and-experiments/scripts/distributed_train_wrapper.sh \
  --num-gpus 2 \
  --yaml cfg.yaml
```

That prints the command without running it. Add `--execute` only when the config, hardware, and output path have been checked:

```bash
sub-skills/training-and-experiments/scripts/distributed_train_wrapper.sh \
  --num-gpus 2 \
  --cuda-visible-devices 0,1 \
  --yaml cfg.yaml \
  --execute
```

For DeepSpeed launch, set `environment.use_deepspeed: true` in the config and use the wrapper's `--launcher deepspeed` mode when the `deepspeed` executable is installed:

```bash
sub-skills/training-and-experiments/scripts/distributed_train_wrapper.sh \
  --launcher deepspeed \
  --num-gpus 2 \
  --cuda-visible-devices 0,1 \
  --yaml cfg.yaml
```

H2O LLM Studio's config checks reject DeepSpeed with a single selected GPU and reject DeepSpeed with `int4`/`int8` backbone dtypes. Use `float16` or `bfloat16` for DeepSpeed and select at least two GPUs.

## Tiny config construction smoke

To create a self-contained tiny CSV and a CPU-like YAML template without downloading data or training a model:

```bash
python sub-skills/training-and-experiments/scripts/make_minimal_config.py \
  --output-dir ./llmstudio-smoke \
  --print-command
```

The generated YAML follows the shape of the repository's tiny integration configs: small sequence length, float32 backbone dtype, mixed precision disabled, a unit-test backbone name, one tiny CSV, and a local output directory. It is intended for command construction and verification planning. End-to-end execution still depends on the installed package, model availability/cache, and the current version's GPU validation behavior.

## Preflight before a real training run

1. Validate the YAML's dataset columns and problem type with the configuration/data sub-skill.
2. Run the environment checker:

   ```bash
   python sub-skills/training-and-experiments/scripts/check_training_environment.py \
     --config cfg.yaml \
     --check-torch \
     --check-deepspeed
   ```

3. For multi-GPU or DeepSpeed, dry-run the bundled distributed wrapper.
4. Start with a small backbone, low `tokenizer.max_length`, small `training.batch_size`, and `training.epochs: 0` or `1` for a smoke before expensive training.
5. After launch, inspect `flags.json`, `logs.log`, `charts_cache`, `checkpoint.pth`, and prediction files as described in [experiment-artifacts.md](experiment-artifacts.md).
