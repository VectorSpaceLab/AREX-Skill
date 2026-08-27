# Safe Training and Config Workflows

These workflows help future agents author, adapt, and inspect training configs without starting long training jobs or relying on source checkout paths.

## Workflow: Inspect an Existing Config Safely

1. Run the bundled static helper with every base config in the same order the launcher would receive them.

   ```bash
   python sub-skills/training-and-configs/scripts/inspect_training_config.py \
     --config base.yaml --config override.yaml
   ```

2. Check the report for:
   - Missing top-level `model` or `data` sections.
   - `lightning` omissions that may trigger GPU defaults.
   - Every nested `target` path and any mapping that looks instantiable but lacks `target`.
   - `CKPT_PATH`, `DATA_PATH`, `USER`, `<path>`, or similar placeholders.
   - Data module assumptions, especially `StableDataModuleFromConfig` `datapipeline` and `loader` blocks.

3. Add dotlist overrides to verify intended merge results without touching the YAML:

   ```bash
   python sub-skills/training-and-configs/scripts/inspect_training_config.py \
     --config toy.yaml \
     --dotlist data.params.batch_size=8 lightning.trainer.max_epochs=1
   ```

4. Only after static inspection passes should a human decide whether to run `main.py`.

## Workflow: Author a New Toy Diffusion Config

Use a toy config when the goal is structural validation, not model quality.

1. Start from a small `DiffusionEngine` structure with:
   - `first_stage_config.target: sgm.models.autoencoder.IdentityFirstStage`.
   - `data.target: sgm.data.mnist.MNISTLoader` or `sgm.data.cifar10.CIFAR10Loader`.
   - `network_config.target: sgm.modules.diffusionmodules.openaimodel.UNetModel`.
   - `denoiser_config`, `loss_fn_config`, `sigma_sampler_config`, `loss_weighting_config`, `sampler_config`, and `discretization_config` targets.

2. If class conditioning is needed, add:

   ```yaml
   conditioner_config:
     target: sgm.modules.GeneralConditioner
     params:
       emb_models:
         - target: sgm.modules.encoders.modules.ClassEmbedder
           input_key: cls
           is_trainable: True
           ucg_rate: 0.2
           params:
             embed_dim: 128
             n_classes: 10
   ```

3. Ensure `UNetModel` conditioning dimensions align with the embedder output. For a class embedder with `embed_dim: 128`, configs often use `num_classes: sequential` and `adm_in_channels: 128`.

4. Keep trainer values small for real smoke runs, but do not use training as the first validator. Inspect statically first:

   ```bash
   python sub-skills/training-and-configs/scripts/inspect_training_config.py --config toy-mnist.yaml
   ```

5. If a human asks for a minimal real run, explicitly warn that MNIST/CIFAR loaders can download data and that `main.py` will instantiate the model/data and may use GPU defaults unless overridden.

## Workflow: Adapt ImageNet or Text-to-Image Training Configs

Large configs include placeholders and data-pipeline assumptions. Adapt them without launching training:

1. Replace checkpoint placeholders.
   - `model.params.first_stage_config.params.ckpt_path: CKPT_PATH` must become a valid local `.ckpt` or `.safetensors` path before model instantiation.
   - Avoid downloading checkpoints as validation. Ask the user to provide paths if they want a run.

2. Replace dataset placeholders.
   - `DATA_PATH` entries under `data.params.train.datapipeline.urls` must point to the intended local/webdataset shards.
   - Confirm shard expansion syntax, permissions, and expected keys before running.

3. Align data keys to conditioning keys.
   - Text configs expect `txt` for `FrozenCLIPEmbedder` and image tensors under `jpg`.
   - Class configs expect `cls` for `ClassEmbedder`.
   - Aspect/crop conditioning expects keys such as `original_size_as_tuple` and `crop_coords_top_left`, usually created by `sdata` mappers.

4. Tune local resource knobs.
   - Lower `data.params.train.loader.batch_size`.
   - Lower `num_workers` for constrained hosts.
   - Reduce `pipeline_config.shardshuffle` and `sample_shuffle` for small datasets.
   - Consider disabling or reducing image logging frequency.
   - Set `lightning.trainer.accumulate_grad_batches` deliberately.

5. Inspect the adapted config:

   ```bash
   python sub-skills/training-and-configs/scripts/inspect_training_config.py \
     --config adapted.yaml \
     --dotlist lightning.trainer.devices=0,
   ```

6. Produce a final command template but do not execute it unless the user confirms a real training run.

## Workflow: Reason About CLI Dotlist Overrides

Use dotlist overrides for small edits and experiment-specific settings. The launcher merges them after all YAML bases.

Examples:

```bash
python main.py --base config.yaml model.base_learning_rate=5e-5
python main.py --base config.yaml data.params.train.loader.batch_size=4
python main.py --base config.yaml lightning.trainer.max_epochs=1 lightning.trainer.num_sanity_val_steps=0
python main.py --base config.yaml model.params.sampler_config.params.num_steps=10
```

Rules of thumb:

- Use `key=value` tokens, not `--key value`, for config overrides.
- Use full nested paths from the merged YAML.
- Later dotlist values override earlier values for the same key.
- Shell quoting may be needed for lists, commas, brackets, or strings containing spaces.
- If overriding `lightning.trainer.devices`, preserve the intended Lightning format. Existing examples use values like `0,`.
- Use the helper with `--dotlist` to inspect merged results before building a command for `main.py`.

## Workflow: Resume Training Safely

Same-logdir resume:

```bash
python main.py --resume logs/run-name
```

Behavior:

- The launcher rejects `--name` combined with `--resume`.
- If `--resume` points to a logdir, it finds `checkpoints/last**.ckpt`, chooses the most recent if multiple exist, and prepends stored `configs/*.yaml` from the logdir to `--base`.
- If `--resume` points to a checkpoint file, the logdir is inferred from the checkpoint path.
- The resolved checkpoint becomes `opt.resume_from_checkpoint` and is passed to `trainer.fit(..., ckpt_path=...)`.

New-logdir resume from a checkpoint:

```bash
python main.py --base config.yaml -n finetune-run --resume_from_checkpoint logs/old/checkpoints/last.ckpt
```

Use this pattern when a new log folder is desired. Confirm the checkpoint file exists and that the base config matches the checkpoint architecture.

Static resume inspection:

```bash
python sub-skills/training-and-configs/scripts/inspect_training_config.py \
  --config config.yaml \
  --resume logs/old/checkpoints/last.ckpt \
  --name finetune-run
```

The helper warns about `--resume`/`--name` conflicts and invalid paths but does not inspect checkpoint contents.

## Workflow: Prepare Lightning Logging and Callbacks

1. Decide logger mode.
   - Default is CSV logging under the run logdir.
   - `--wandb true` switches to WandB.
   - `--debug true` sets WandB offline and moves new debug logdirs under `debug_runs` after completion/failure.

2. Review checkpoint frequency.
   - Default `ModelCheckpoint` saves under `checkpoints/` and keeps `last.ckpt`.
   - `metrics_over_trainsteps_checkpoint` can save every N steps without deleting old files; warn about disk usage.

3. Review image logger settings.
   - `main.ImageLogger` can call model image logging and write grids.
   - For resource-constrained debugging, set `disabled: True`, reduce `max_images`, or increase `batch_frequency`.

4. Review strategy.
   - Default strategy target is `pytorch_lightning.strategies.DDPStrategy`.
   - If no custom strategy is supplied, default params include `find_unused_parameters: False`.

5. Use static inspection first; callback instantiation can import optional packages and create directories only once `main.py` runs.

## Workflow: Safe Validation Without Starting Training

Recommended validation ladder:

1. Parse and merge config files using `inspect_training_config.py`.
2. Inspect all target paths in the report and compare them against the API reference.
3. Resolve placeholders with the user, but do not download or create them as part of validation.
4. Check data/conditioning key alignment manually.
5. Check trainer defaults and device settings.
6. Present a command template for the user to run when they are ready.

Avoid these as validation unless explicitly requested:

- `python main.py --base ...` because it instantiates model/data and may prepare data.
- Importing `sgm.data.dataset` without `sdata` installed because missing `sdata` exits immediately.
- Instantiating text embedders because they can load/download large model weights.
- Running train/test loops, even for toy configs, unless the user asks for execution.

## Difficult Usability Cases

Use these as high-value verification scenarios for future review artifacts, not as runtime skill content:

- Validate a new toy class-conditioned MNIST diffusion config where one nested denoiser or sampler object is missing `target`; explain the failure before any training starts and show the corrected dotlist/base YAML merge.
- Adapt a text-to-image or ImageNet config by replacing `CKPT_PATH`, `DATA_PATH`, mapper keys, shuffle buffers, batch size, and trainer devices while preserving `GeneralConditioner` input-key compatibility and avoiding a real webdataset read.
