# Configuration Reference

This repository uses a config-first training pattern. YAML files define model graphs, data modules, loggers, callbacks, trainer settings, and nested diffusion components through dotted `target` paths plus `params` mappings.

## Top-Level Shape

A training YAML normally has these top-level sections:

```yaml
model:
  base_learning_rate: 1.0e-4
  target: sgm.models.diffusion.DiffusionEngine
  params: {}

data:
  target: sgm.data.mnist.MNISTLoader
  params: {}

lightning:
  trainer: {}
  callbacks: {}
  modelcheckpoint: {}
  logger: {}
```

`model` and `data` are required for `main.py` training. `lightning` is optional but common. The launcher pops `lightning` out before model creation, so model constructors do not receive Lightning callback or trainer options.

## Target/Params Pattern

Any config object that will be passed to `instantiate_from_config` must include `target`:

```yaml
some_component:
  target: package.module.ClassName
  params:
    constructor_arg: value
```

`instantiate_from_config(config)` resolves `config["target"]` and calls the object with `**config.get("params", {})`. Special sentinels `__is_first_stage__` and `__is_unconditional__` return `None`; other missing targets raise `KeyError: Expected key `target` to instantiate.`

Common target examples:

- `sgm.models.diffusion.DiffusionEngine`
- `sgm.models.autoencoder.AutoencodingEngine`
- `sgm.models.autoencoder.AutoencoderKL`
- `sgm.models.autoencoder.IdentityFirstStage`
- `sgm.modules.GeneralConditioner`
- `sgm.modules.encoders.modules.ClassEmbedder`
- `sgm.modules.encoders.modules.FrozenCLIPEmbedder`
- `sgm.modules.encoders.modules.ConcatTimestepEmbedderND`
- `sgm.modules.diffusionmodules.openaimodel.UNetModel`
- `sgm.modules.diffusionmodules.denoiser.Denoiser`
- `sgm.modules.diffusionmodules.denoiser.DiscreteDenoiser`
- `sgm.modules.diffusionmodules.denoiser_scaling.EDMScaling`
- `sgm.modules.diffusionmodules.denoiser_scaling.EpsScaling`
- `sgm.modules.diffusionmodules.discretizer.EDMDiscretization`
- `sgm.modules.diffusionmodules.discretizer.LegacyDDPMDiscretization`
- `sgm.modules.diffusionmodules.loss.StandardDiffusionLoss`
- `sgm.modules.diffusionmodules.loss_weighting.EDMWeighting`
- `sgm.modules.diffusionmodules.loss_weighting.EpsWeighting`
- `sgm.modules.diffusionmodules.sigma_sampling.EDMSampling`
- `sgm.modules.diffusionmodules.sigma_sampling.DiscreteSampling`
- `sgm.modules.diffusionmodules.sampling.EulerEDMSampler`
- `sgm.modules.diffusionmodules.guiders.VanillaCFG`
- `sgm.data.mnist.MNISTLoader`
- `sgm.data.cifar10.CIFAR10Loader`
- `sgm.data.dataset.StableDataModuleFromConfig`
- `main.ImageLogger`
- `main.SetupCallback`
- `pytorch_lightning.callbacks.ModelCheckpoint`
- `pytorch_lightning.callbacks.LearningRateMonitor`
- `pytorch_lightning.loggers.CSVLogger`
- `pytorch_lightning.loggers.WandbLogger`
- `pytorch_lightning.strategies.DDPStrategy`

## DiffusionEngine Model Section

A minimal diffusion training section uses `DiffusionEngine` with nested configs:

```yaml
model:
  base_learning_rate: 1.0e-4
  target: sgm.models.diffusion.DiffusionEngine
  params:
    network_config:
      target: sgm.modules.diffusionmodules.openaimodel.UNetModel
      params: {}
    denoiser_config:
      target: sgm.modules.diffusionmodules.denoiser.Denoiser
      params:
        scaling_config:
          target: sgm.modules.diffusionmodules.denoiser_scaling.EDMScaling
    first_stage_config:
      target: sgm.models.autoencoder.IdentityFirstStage
    conditioner_config:
      target: sgm.modules.GeneralConditioner
      params:
        emb_models: []
    loss_fn_config:
      target: sgm.modules.diffusionmodules.loss.StandardDiffusionLoss
      params:
        sigma_sampler_config:
          target: sgm.modules.diffusionmodules.sigma_sampling.EDMSampling
        loss_weighting_config:
          target: sgm.modules.diffusionmodules.loss_weighting.EDMWeighting
    sampler_config:
      target: sgm.modules.diffusionmodules.sampling.EulerEDMSampler
      params:
        discretization_config:
          target: sgm.modules.diffusionmodules.discretizer.EDMDiscretization
```

Training requires both `sampler_config` and `loss_fn_config`; `DiffusionEngine.on_train_start` raises if either is missing. `first_stage_config` is instantiated and frozen. For toy pixel-space configs it is usually `IdentityFirstStage`; latent configs often use `AutoencoderKL` and a checkpoint path.

## GeneralConditioner Section

`GeneralConditioner` receives `emb_models`, instantiates every embedder, and requires each embedder config to include `input_key` or `input_keys`:

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

Embedder outputs are routed by tensor rank: rank 2 to `vector`, rank 3 to `crossattn`, and rank 4 to `concat`. `cond_view` and `cond_motion` are special input keys routed to their own output keys. Non-trainable embedders are frozen and switched to eval mode. `legacy_ucg_value` applies legacy classifier-free dropout by replacing batch values before embedding.

## Autoencoding Configs

Autoencoding configs use `AutoencodingEngine` directly or legacy wrappers such as `AutoencoderKL`. The modern engine expects nested encoder, decoder, loss, regularizer, and optimizer-related configs:

```yaml
model:
  target: sgm.models.autoencoder.AutoencodingEngine
  params:
    encoder_config:
      target: some.encoder.Class
    decoder_config:
      target: some.decoder.Class
    loss_config:
      target: some.loss.Class
    regularizer_config:
      target: some.regularizer.Class
    optimizer_config:
      target: torch.optim.Adam
```

Legacy `AutoencoderKL` configs in diffusion examples use `ckpt_path`, `embed_dim`, `monitor`, `ddconfig`, and `lossconfig`; they route through compatibility wrappers before reaching the engine.

## Data Sections

Toy configs use simple Lightning data modules:

```yaml
data:
  target: sgm.data.mnist.MNISTLoader
  params:
    batch_size: 512
    num_workers: 1
```

`MNISTLoader` and `CIFAR10Loader` download datasets if actually instantiated and used, so do not run them as static validation.

Large image/text configs use `StableDataModuleFromConfig`:

```yaml
data:
  target: sgm.data.dataset.StableDataModuleFromConfig
  params:
    train:
      datapipeline:
        urls:
          - DATA_PATH
        pipeline_config:
          shardshuffle: 10000
          sample_shuffle: 10000
        decoders:
          - pil
        postprocessors:
          - target: sdata.mappers.TorchVisionImageTransforms
            params:
              key: jpg
              transforms: []
      loader:
        batch_size: 64
        num_workers: 6
```

`StableDataModuleFromConfig` requires `train.datapipeline` and `train.loader`. Validation/test configs require the same pair when present. If no validation config is provided and `skip_val_loader` is false, training config is reused as validation.

## Lightning Section

`lightning.trainer` is merged with defaults from `pytorch_lightning.Trainer.__init__`. CLI trainer args override config values only when they differ from Trainer defaults. The launcher sets `lightning.trainer.accelerator` to `gpu` by default before handling devices.

Typical fields:

```yaml
lightning:
  trainer:
    devices: 0,
    benchmark: True
    num_sanity_val_steps: 0
    accumulate_grad_batches: 1
    max_epochs: 20
  modelcheckpoint:
    params:
      every_n_train_steps: 5000
  callbacks:
    image_logger:
      target: main.ImageLogger
      params:
        disabled: False
        batch_frequency: 1000
        max_images: 16
```

The example `devices: 0,` value is a string-like GPU list in YAML. If you need CPU-only validation or dry-run planning, avoid relying on launcher defaults; set accelerator/devices explicitly in the final command or inspect only with the bundled helper.

## Merge and Override Rules

Launcher merge order is:

1. Load every config passed to `--base` from left to right.
2. Convert unknown CLI tokens to an OmegaConf dotlist.
3. Merge base configs first and CLI dotlist last.
4. Pop `lightning` from the project config for separate trainer/logger/callback handling.

Later base configs override earlier base configs at the same keys. Dotlist overrides override all base files.

Examples:

```bash
python main.py --base base.yaml override.yaml model.base_learning_rate=5e-5
python main.py --base toy.yaml lightning.trainer.max_epochs=1 data.params.batch_size=8
python main.py --base txt2img.yaml model.params.first_stage_config.params.ckpt_path=checkpoints/model.ckpt
```

Use dotlist keys without a leading `--` for config values. Options with leading dashes are parsed by argparse as launcher or trainer CLI arguments; unknown non-option tokens become OmegaConf dotlist values.

## Placeholders and USER Comments

Example training configs include placeholders such as `CKPT_PATH`, `DATA_PATH`, and comments starting with `USER`. Treat them as required adaptation points:

- Replace `CKPT_PATH` before model instantiation because `AutoencoderKL` will try to apply the checkpoint.
- Replace `DATA_PATH` before dataset construction because `StableDataModuleFromConfig` passes URLs to `sdata` pipelines.
- Review mapper keys such as `jpg`, `height`, `width`, `txt`, `cls`, `original_size_as_tuple`, and `crop_coords_top_left` so conditioner inputs match data outputs.
- Reduce `batch_size`, `num_workers`, shuffle buffers, and checkpoint frequency for local debugging.

## Safe Command Templates

Static inspection:

```bash
python sub-skills/training-and-configs/scripts/inspect_training_config.py --config config.yaml
```

Training command only after validation and human confirmation:

```bash
python main.py --base config.yaml -n run_name lightning.trainer.devices=0,
```

Resume same log folder:

```bash
python main.py --resume logs/existing-run
```

Resume from checkpoint into a new log folder:

```bash
python main.py --base config.yaml -n new_run --resume_from_checkpoint logs/existing-run/checkpoints/last.ckpt
```
