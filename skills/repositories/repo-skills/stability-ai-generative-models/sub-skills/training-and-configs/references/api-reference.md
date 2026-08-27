# API Reference for Config-Facing Training Objects

The package version verified for this skill is `sgm` `0.1.0`. The signatures below are the config-facing constructor contracts most often needed when authoring or troubleshooting training YAML.

## Launcher Helpers

### `sgm.util.instantiate_from_config(config)`

Behavior:

- Requires `config["target"]` unless the config is the sentinel string `__is_first_stage__` or `__is_unconditional__`.
- Resolves the target with `get_obj_from_str(config["target"])`.
- Calls the resolved object with `**config.get("params", {})`.
- Raises `KeyError("Expected key `target` to instantiate.")` when a normal config lacks `target`.

### `sgm.util.get_obj_from_str(string, reload=False, invalidate_cache=True)`

Splits the dotted target at the final dot, imports the module, optionally reloads it, and returns the class/function attribute. Import typos usually surface here as `ModuleNotFoundError`, `ImportError`, or `AttributeError`.

### `sgm.util.load_model_from_config(config, ckpt, verbose=True, freeze=True)`

Loads `.ckpt` or `.safetensors`, instantiates `config.model`, applies the state dict with `strict=False`, optionally freezes parameters, and switches the model to eval mode. This is a model-loading helper, not a static config validator.

## `main.py` Training CLI

Important launcher options:

- `--base` / `-b`: one or more base YAML files loaded left to right.
- Unknown CLI tokens such as `model.base_learning_rate=5e-5` become OmegaConf dotlist overrides and merge last.
- `--resume` / `-r`: path to an existing log directory or checkpoint. Cannot be combined with `--name`.
- `--resume_from_checkpoint`: direct checkpoint path supported for newer Torch/Lightning stacks; useful with `--name` for a new log folder.
- `--name` / `-n`: postfix for log directory naming.
- `--logdir`: base log directory, default `logs`.
- `--train`: defaults true.
- `--no-test`: disables test after training.
- `--scale_lr`: when true, uses `accumulate_grad_batches * ngpu * batch_size * base_learning_rate`.
- `--wandb`: switches default logger from CSV to WandB; debug mode sets WandB offline.
- `--debug`: enables post-mortem debugging and moves new logdirs under `debug_runs`.
- `--enable_tf32`: enables TF32 matmul and cuDNN settings.

Runtime behavior:

- Appends current working directory to `sys.path` so targets like `main.ImageLogger` resolve when launched as `python main.py`.
- Merges configs and dotlist overrides before instantiating `config.model` and `config.data`.
- Defaults `lightning.trainer.accelerator` to `gpu`.
- Instantiates default logger, strategy, setup callback, image logger, learning rate logger, and checkpoint callback unless overridden.
- Calls `data.prepare_data()` before `trainer.fit`; this can trigger side effects in data modules.
- Saves merged project and Lightning configs into the run logdir via `SetupCallback` when training starts.

## `sgm.models.diffusion.DiffusionEngine`

Verified constructor signature:

```text
DiffusionEngine(
  network_config,
  denoiser_config,
  first_stage_config,
  conditioner_config=None,
  sampler_config=None,
  optimizer_config=None,
  scheduler_config=None,
  loss_fn_config=None,
  network_wrapper=None,
  ckpt_path=None,
  use_ema=False,
  ema_decay_rate=0.9999,
  scale_factor=1.0,
  disable_first_stage_autocast=False,
  input_key="jpg",
  log_keys=None,
  no_cond_log=False,
  compile_model=False,
  en_and_decode_n_samples_a_time=None,
)
```

Config implications:

- `network_config`, `denoiser_config`, and `first_stage_config` are required.
- `network_config` is instantiated, then wrapped by `network_wrapper` or the default OpenAI UNet wrapper.
- `denoiser_config`, `sampler_config`, `conditioner_config`, `scheduler_config`, and `loss_fn_config` are nested target configs.
- `conditioner_config` defaults to an unconditional config when absent.
- `first_stage_config` is instantiated, switched to eval, frozen, and used for encode/decode.
- `ckpt_path` may point to `.ckpt` or `.safetensors` and loads with `strict=False`.
- Training requires `sampler_config` and `loss_fn_config`; missing either raises at train start.
- `input_key` must match the image tensor key emitted by the data module, commonly `jpg`.

Config-facing methods:

- `configure_optimizers()` uses `optimizer_config.target`, defaults to `torch.optim.AdamW`, and includes trainable conditioner embedders.
- `sample(cond, uc=None, batch_size=16, shape=None, **kwargs)` uses the configured sampler and denoiser.
- `log_conditionings(batch, n)` logs conditioning inputs listed in `log_keys`.

## `sgm.models.autoencoder.AutoencodingEngine`

Verified constructor signature:

```text
AutoencodingEngine(
  *args,
  encoder_config,
  decoder_config,
  loss_config,
  regularizer_config,
  optimizer_config=None,
  lr_g_factor=1.0,
  trainable_ae_params=None,
  ae_optimizer_args=None,
  trainable_disc_params=None,
  disc_optimizer_args=None,
  disc_start_iter=0,
  diff_boost_factor=3.0,
  ckpt_engine=None,
  ckpt_path=None,
  additional_decode_keys=None,
  **kwargs,
)
```

Additional `AbstractAutoencoder` kwargs include `ema_decay=None`, `monitor=None`, and `input_key="jpg"`.

Config implications:

- `encoder_config`, `decoder_config`, `loss_config`, and `regularizer_config` are required target configs.
- `optimizer_config` defaults to `torch.optim.Adam`.
- `ckpt_path` is deprecated in favor of `ckpt_engine`; both cannot be set together.
- `additional_decode_keys` lets batch keys pass through to the decoder.
- The engine uses manual optimization and can train autoencoder and discriminator parameter groups separately.

Legacy wrappers:

- `AutoencoderKL` accepts compatibility-style `ddconfig`, `embed_dim`, `lossconfig`, `ckpt_path`, and related kwargs, then routes through legacy engine setup.
- `IdentityFirstStage` acts as a no-op first stage for toy/pixel-space diffusion configs.

## `sgm.modules.encoders.modules.GeneralConditioner`

Constructor:

```text
GeneralConditioner(emb_models)
```

Config implications:

- `emb_models` is a list of target configs.
- Every embedder must inherit `AbstractEmbModel`.
- Each embedder must define `input_key` or `input_keys` in its config.
- `is_trainable` defaults false; non-trainable embedders are frozen and forced to eval mode.
- `ucg_rate` defaults `0.0` and controls unconditional guidance dropout.
- `legacy_ucg_value` replaces batch values before embedding when set.
- Outputs are concatenated by key: rank 2 to `vector`, rank 3 to `crossattn`, rank 4 to `concat`, with special `cond_view` and `cond_motion` handling.

Common embedder targets:

- `sgm.modules.encoders.modules.ClassEmbedder`: class-label conditioning; common params include `embed_dim`, `n_classes`, and `add_sequence_dim`.
- `sgm.modules.encoders.modules.FrozenCLIPEmbedder`: text conditioning; may load Hugging Face tokenizer/model if instantiated.
- `sgm.modules.encoders.modules.FrozenT5Embedder` and `FrozenByT5Embedder`: text conditioning with T5 variants; heavy downloads may occur if not cached.
- `sgm.modules.encoders.modules.ConcatTimestepEmbedderND`: numeric tuple conditioning for image size and crop coordinates.

## Diffusion Module Targets

### Denoisers and scaling

- `Denoiser(scaling_config)`: wraps a scaling object for continuous-time denoising.
- `DiscreteDenoiser(scaling_config, num_idx, discretization_config, do_append_zero=False, quantize_c_noise=True, flip=True)`: combines scaling with a discrete sigma schedule.
- `EDMScaling(sigma_data=0.5)`: EDM preconditioning.
- `EpsScaling()`: epsilon-prediction preconditioning.
- `VScaling()` and `VScalingWithEDMcNoise()`: v-prediction scaling variants.

### Loss and training sigma sampling

- `StandardDiffusionLoss(sigma_sampler_config, loss_weighting_config, loss_type="l2", offset_noise_level=0.0, batch2model_keys=None)`.
- `EDMSampling(p_mean=-1.2, p_std=1.2)`.
- `DiscreteSampling(discretization_config, num_idx, do_append_zero=False, flip=True)`.
- `ZeroSampler()`.
- `EDMWeighting(sigma_data=0.5)`, `EpsWeighting()`, `UnitWeighting()`, and `VWeighting()`.

### Samplers, discretizers, and guiders

- `BaseDiffusionSampler(discretization_config, num_steps=None, guider_config=None, verbose=False, device="cuda")`.
- `EulerEDMSampler`, `HeunEDMSampler`, `EulerAncestralSampler`, and DPM++ variants inherit sampler constructor arguments.
- `EDMDiscretization(sigma_min=0.002, sigma_max=80.0, rho=7.0)`.
- `LegacyDDPMDiscretization(...)` for DDPM-style schedules used in discrete epsilon configs.
- `VanillaCFG(scale)` for classifier-free guidance.
- `IdentityGuider()` when no guidance is wanted.

## Data Modules

### `sgm.data.mnist.MNISTLoader`

```text
MNISTLoader(batch_size, num_workers=0, prefetch_factor=2, shuffle=True)
```

Emits dict batches with `jpg` and `cls`. Instantiating the underlying dataset can download MNIST into `.data/` if missing.

### `sgm.data.cifar10.CIFAR10Loader`

```text
CIFAR10Loader(batch_size, num_workers=0, shuffle=True)
```

Emits dict batches with `jpg` and `cls`. Instantiating the underlying dataset can download CIFAR-10 if missing.

### `sgm.data.dataset.StableDataModuleFromConfig`

```text
StableDataModuleFromConfig(train, validation=None, test=None, skip_val_loader=False, dummy=False)
```

Config implications:

- Requires the external `sdata` package; missing it causes an immediate exit during import.
- `train` must contain `datapipeline` and `loader`.
- `validation` and `test` must also contain `datapipeline` and `loader` when provided.
- With no validation and `skip_val_loader=False`, validation uses train config.
- `setup(stage)` creates datapipelines; loaders are built by `sdata.create_loader`.

## Lightning Callback Targets

### `main.SetupCallback`

Constructor parameters include `resume`, `now`, `logdir`, `ckptdir`, `cfgdir`, `config`, `lightning_config`, `debug`, and optional `ckpt_name`. It creates log directories, saves merged project and Lightning configs, and saves an emergency checkpoint on exception.

### `main.ImageLogger`

Constructor parameters include `batch_frequency`, `max_images`, `clamp=True`, `increase_log_steps=True`, `rescale=True`, `disabled=False`, `log_on_batch_idx=False`, `log_first_step=False`, `log_images_kwargs=None`, `log_before_first_step=False`, and `enable_autocast=True`. It calls model image logging hooks and writes local image grids; keep it disabled or low frequency for minimal debug runs.
