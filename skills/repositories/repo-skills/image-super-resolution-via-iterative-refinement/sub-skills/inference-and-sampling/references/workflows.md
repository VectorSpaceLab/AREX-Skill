# Inference and Sampling Workflows

This reference covers the repository's two non-`sr.py` image-production scripts:

- `infer.py` performs conditional super-resolution inference over a validation dataloader.
- `sample.py` performs unconditional DDPM/SR3 training or unconditional generation.

The stock scripts create timestamped experiment folders through the repo logger. They also parse JSON configs after stripping `//` comments, set `CUDA_VISIBLE_DEVICES` from `-gpu` or `gpu_ids`, and rewrite `path.log`, `path.tb_logger`, `path.results`, and `path.checkpoint` under `experiments/<name>_<timestamp>/...` for each run.

## Pretrained super-resolution inference with `infer.py`

Use this route for pretrained SR3 inference such as 64×64 to 512×512 upscaling. The README's inference path is:

```bash
python infer.py -c config/sr_sr3_64_512.json
```

Prefer building it through the bundled helper first. The example below assumes the current directory is this sub-skill directory; otherwise, call the same bundled script by its resolved skill path and pass `--repo-root <checkout-root>`.

```bash
python scripts/build_inference_command.py \
  --repo-root <checkout-root> \
  -c config/sr_sr3_64_512.json \
  --require-resume-state \
  --gpu-ids 0
```

### Required config properties

For the stock 64→512 config, the important fields are:

- `path.resume_state`: checkpoint prefix for a pretrained model. The code appends `_gen.pth` internally. Set this to a stem such as `experiments/.../checkpoint/I830000_E32`, not to `I830000_E32_gen.pth`.
- `model.which_model_G`: `sr3` for the SR3 network variant.
- `model.diffusion.conditional`: `true`; conditional inference feeds `visuals['SR']` into `super_resolution`.
- `model.diffusion.image_size`: target/high resolution (`512` in the stock high-SR config).
- `model.unet.in_channel`: `6` for conditional SR because the model receives RGB conditioning plus RGB noisy target channels.
- `datasets.val.mode`: normally `LRHR` for the prepared validation layout.
- `datasets.val.dataroot`: root containing prepared images or LMDB entries.
- `datasets.val.data_len`: number of validation items to process.

For `datatype: img`, the validation root should contain at least `sr_<low>_<high>` and `hr_<high>` directories; with `mode: LRHR`, `lr_<low>` is also loaded by the dataset class even though `infer.py` saves only the interpolated input (`_inf`), final/process SR images, and HR images. If no true HR images exist, the README allows using the same images for the HR and SR-ready directories so that the dataset can still be constructed.

### `infer.py` CLI surface

`infer.py` accepts:

- `-c/--config`: JSON-with-comments config file; default is `config/sr_sr3_64_512.json`.
- `-p/--phase`: only `val` is accepted and defaulted.
- `-gpu/--gpu_ids`: comma-separated GPU ids overriding the config.
- `-debug/-d`: rewrites the experiment name to `debug_<name>` and shrinks frequencies/timesteps/data lengths in the shared logger parser.
- `-enable_wandb`: initializes W&B logging.
- `-log_infer`: with W&B enabled, logs inference rows to an evaluation table.

### Inference outputs

For each validation item, `infer.py` writes under the timestamped `path.results` directory:

- `<step>_<idx>_sr_process.png`: grid/sequence of reverse-diffusion states;
- `<step>_<idx>_sr.png`: final super-resolved output;
- `<step>_<idx>_hr.png`: high-resolution target from the dataset;
- `<step>_<idx>_inf.png`: the prepared/interpolated super-resolution input.

`current_step` is initialized to `0` in standalone inference, so the default filenames start with `0_`.

## Unconditional generation or training with `sample.py`

Use this route for the README's 128×128 face generation configs. The two stock sample configs are:

- `config/sample_sr3_128.json`: SR3-style timestep/gamma embedding, `conditional: false`, `image_size: 128`, `datasets.val.data_len: 50`.
- `config/sample_ddpm_128.json`: DDPM network variant, `conditional: false`, `image_size: 128`, `datasets.val.data_len: 10`.

For pretrained unconditional generation, use validation mode and require a checkpoint stem:

```bash
python scripts/build_sample_command.py \
  --repo-root <checkout-root> \
  -c config/sample_sr3_128.json \
  --phase val \
  --require-resume-state \
  --gpu-ids 0
```

For unconditional training or resume training, choose `--phase train` and ensure the training dataset layout exists:

```bash
python scripts/build_sample_command.py \
  --repo-root <checkout-root> \
  -c config/sample_sr3_128.json \
  --phase train \
  --gpu-ids 0
```

### Required config properties

For unconditional sampling:

- `model.diffusion.conditional` should be `false`.
- `model.unet.in_channel` should normally be `3` for RGB generation.
- `model.which_model_G` selects `sr3` or `ddpm` modules.
- `model.beta_schedule.<phase>.n_timestep` controls reverse-diffusion length; stock sample configs use `2000` steps.
- `path.resume_state` is required for meaningful `-p val` generation from a pretrained model. Without it, the model is randomly initialized and outputs are not a pretrained result.
- For `-p train`, `path.resume_state` is optional for fresh training. If it is set, the code loads both the generator and optimizer states.

### `sample.py` phase behavior

- `-p val`: does not construct a validation dataset. It uses `datasets.val.data_len` as the sample count, sets the validation noise schedule, calls `diffusion.sample(continous=True)`, and saves process/final sample images. A pretrained generator checkpoint is normally expected.
- `-p train`: constructs `datasets.train`, optimizes until `train.n_iter`, periodically samples `datasets.val.data_len` images during validation, and saves checkpoints.

The training dataset class still expects the repo's paired image layout (`sr_<low>_<high>` plus `hr_<high>`) even for unconditional training because the shared dataset implementation returns both `SR` and `HR` tensors.

### `sample.py` CLI surface

`sample.py` accepts:

- `-c/--config`: JSON-with-comments config file; default is `config/sample_sr3_128.json`.
- `-p/--phase`: `train` or `val`; the script default is `train`, so generation commands should pass `-p val` explicitly.
- `-gpu/--gpu_ids`: comma-separated GPU ids overriding the config.
- `-debug/-d`: enables the shared debug config edits.
- `-enable_wandb`: logs train metrics/checkpoint metadata or validation sample images.
- `-log_wandb_ckpt`: with W&B enabled, logs training checkpoints as W&B artifacts.

### Sampling outputs

In `-p val`, `sample.py` writes under the timestamped `path.results` directory:

- `<step>_<idx>_sample_process.png`: grid/sequence of reverse-diffusion states;
- `<step>_<idx>_sample.png`: final generated image.

During training, validation samples are nested under a per-epoch subdirectory inside `path.results` and use names such as `<step>_<idx>_sr.png` despite being unconditional samples.

## Command-builder usage notes

Both bundled builders only inspect configs and print shell commands. They do not import PyTorch, create datasets, load checkpoints, or run model code.

Useful flags:

- `--require-resume-state`: fail unless `path.resume_state` is set and the expected checkpoint files exist.
- `--skip-checkpoint-files`: still require a syntactically valid checkpoint stem but do not check the filesystem.
- `--check-data`: check expected image-layout directories for the selected workflow when `datatype: img`.
- `--command-only`: print just the shell command for scripting.

Use the builders as a preflight step; running the printed command is a separate, user-approved action because the stock workflows can require CUDA memory, external datasets/checkpoints, W&B credentials, and substantial reverse-diffusion time.
