# Training workflows and safe boundaries

## 1. Inspect before running

Use the bundled inspector from any working directory:

```bash
python <training-skill>/scripts/inspect_train_cli.py --help
python <training-skill>/scripts/inspect_train_cli.py --show-defaults
python <training-skill>/scripts/inspect_train_cli.py --show-branch --data_name BRATS --data_dir <training-data>
```

The inspector is a standard-library program. It reproduces the parser defaults and strict boolean conversion without importing `segmentation_train.py`; therefore it does not start a Visdom client, initialize `torch.distributed`, create a DataLoader, allocate a model, or train. Its custom-branch report mirrors the source's exact `Path.glob("*\\*.nii.gz")` test and warns about the POSIX backslash caveat described in troubleshooting.

The actual launcher is not a dry-run tool. Even asking the real launcher for help can fail before argument parsing if the `visdom` package is missing, because the module constructs `Visdom(port=8850)` at import time.

## 2. Branch selection and channel contract

The branch order in `segmentation_train.py` is fixed:

1. `--data_name ISIC` (exact case) uses `ISICDataset`, a resize-to-square plus tensor transform, and sets `args.in_ch = 4`.
2. `--data_name BRATS` (exact case, also the default) uses `BRATSDataset3D`, a resize transform, and sets `args.in_ch = 5`.
3. Any other `data_name` falls through to an automatic test: if `any(Path(args.data_dir).glob("*\\*.nii.gz"))` is true, it uses `CustomDataset3D` and sets `args.in_ch = 4` in the current source; otherwise it uses `CustomDataset` and sets `args.in_ch = 4`.

The custom 3-D branch therefore has a source-level inconsistency: it is detected as 3-D but still assigns four input channels. Do not infer a five-channel custom contract; inspect the loader's emitted tensors before building a model. The dedicated BRATS branch is the only branch that assigns five.

Branch selection happens before the model factory and overwrites the parser's initial `--in_ch 5` default. `TrainLoop.run_step` concatenates the loader's `batch` and `cond` on the channel dimension. The final channel is treated as the segmentation mask by `training_losses_segmentation`; the preceding channels are image/input channels. A mismatch reaches the first convolution or the highway subnetwork as a shape error.

Detailed dataset tree contracts are intentionally outside this sub-skill. This guide only tells you how the launcher selects the branch and what channel invariant to verify.

## 3. Documented baseline commands

The published ISIC and BRATS recipes pass the following flags to the
prepared MedSegDiff training launcher. The launcher is intentionally not copied
into this skill: it is a full training program with GPU, data, logging, and
checkpoint side effects. Use the versioned source package that you have
separately prepared, and use the bundled inspector here before invoking it.

For ISIC, pass:

```text
--data_name ISIC --data_dir <input-data-directory> --out_dir <output-directory>
--image_size 256 --num_channels 128 --class_cond False --num_res_blocks 2
--num_heads 1 --learn_sigma True --use_scale_shift_norm False
--attention_resolutions 16 --diffusion_steps 1000 --noise_schedule linear
--rescale_learned_sigmas False --rescale_timesteps False --lr 1e-4 --batch_size 8
```

For BRATS, use the same configuration with `--data_dir
<brats-training-directory>` and the default `--data_name BRATS`.

These commands document a starting point, not a lightweight smoke run. The README separately suggests `--lr 5e-5 --batch_size 8` for its fine-model hyperparameter discussion. Preserve the distinction: the example command uses `1e-4`; the later suggestion uses `5e-5`.

The README's larger MedSegDiff++ setting is:

```text
--image_size 256 --num_channels 512 --class_cond False --num_res_blocks 12
--num_heads 8 --learn_sigma True --use_scale_shift_norm True
--attention_resolutions 24 --batch_size 64
```

This is substantially more resource-intensive. The README says about 100,000 training steps commonly converge, while noting that later loss values may flatten while sample quality continues to improve. Do not use that claim as a fixed early-stop criterion.

## 4. Recommended configuration discipline

For a reproducible run, record at least:

- branch (`ISIC`, `BRATS`, or custom fallback), data directory, output directory, and actual emitted channel count;
- every architecture flag (`image_size`, `num_channels`, `num_res_blocks`, `num_heads`, `num_head_channels`, `num_heads_upsample`, `attention_resolutions`, `channel_mult`, `dropout`, `version`, and normalization/checkpoint switches);
- diffusion flags (`learn_sigma`, `diffusion_steps`, `noise_schedule`, `timestep_respacing`, `use_kl`, `predict_xstart`, both rescale flags, and `dpm_solver`);
- optimizer/loop flags (`lr`, `weight_decay`, `lr_anneal_steps`, `batch_size`, `microbatch`, `ema_rate`, logging/checkpoint intervals, and precision settings);
- GPU selection and the exact checkpoint file used for a resume.

Use the helper to inspect defaults, then pass explicit values for any experiment. Boolean values need a token: `--use_fp16 False`, not merely `--use_fp16`.

## 5. Schedule sampler choice

`--schedule_sampler uniform` is the safest default. The only other accepted name is `loss-second-moment`; it adapts timestep weights after its loss history warms up. Unknown names fail with `NotImplementedError`. The launcher passes `maxt=--diffusion_steps` to the uniform sampler, so changing diffusion length and sampler configuration independently is unsafe.

## 6. Checkpoints, resume, and expected outputs

The logger writes to `--out_dir`. With its default formats, expect stdout, `log.txt`, and `progress.csv`. The loop saves at step zero after the first `run_step`, then whenever `step % save_interval == 0`, and saves a final checkpoint if the last step was not already on an interval.

The source names model outputs as:

```text
savedmodel000000.pt
emasavedmodel_0.9999_000000.pt
optsavedmodel000000.pt
```

The six-digit step is `step + resume_step`. The model checkpoint is the file to pass as `--resume_checkpoint`; `parse_resume_step_from_filename` extracts the integer after the last `model` substring.

Resume is only partially self-consistent in this source:

- `_load_and_sync_parameters` loads the supplied model checkpoint with `load_part_state_dict`, which copies matching names and silently skips unmatched names.
- `_load_optimizer_state` searches for `opt{step:06d}.pt`, but `save()` writes `optsavedmodel{step:06d}.pt`. A normal checkpoint set therefore does not automatically restore the saved optimizer state.
- `_load_ema_parameters` searches for `ema_{rate}_{step:06d}.pt`, but `save()` writes `emasavedmodel_{rate}_{step:06d}.pt`. A normal checkpoint set therefore may start EMA parameters from the current model instead of the saved EMA.

Treat a resumed run as model-weight restoration unless you have independently reconciled and checked optimizer/EMA filenames. Keep architecture and `version` flags unchanged; because loading is partial, an incompatible architecture can appear to load while leaving some parameters at initialization.

## 7. Tiny direct factory smoke recipe

This checks factory wiring only; it is not training and does not require a dataset or Visdom. Run it from an environment that can import the repository package:

```bash
python - <<'PY'
from guided_diffusion.script_util import create_model_and_diffusion

model, diffusion = create_model_and_diffusion(
    image_size=64, class_cond=False, learn_sigma=False,
    num_channels=32, num_res_blocks=1, channel_mult="", in_ch=4,
    num_heads=1, num_head_channels=-1, num_heads_upsample=-1,
    attention_resolutions="16", dropout=0.0, diffusion_steps=100,
    noise_schedule="linear", timestep_respacing="", use_kl=False,
    predict_xstart=False, rescale_timesteps=False,
    rescale_learned_sigmas=False, use_checkpoint=False,
    use_scale_shift_norm=False, resblock_updown=False, use_fp16=False,
    use_new_attention_order=False, dpm_solver=False, version="new",
)
assert model.in_channels == 4
assert diffusion.num_timesteps == 100
print(type(model).__name__, diffusion.num_timesteps)
PY
```

Use a width divisible by 32 because the repository's normalization uses 32 groups. This recipe tests construction, not a forward pass, data compatibility, CUDA kernels, checkpoint loading, or convergence. A CPU success here must not be reported as successful full training.

## 8. DPM-solver and version boundaries

The README suggests `--diffusion_steps 50 --dpm_solver True` to speed sampling. In the diffusion implementation, `dpm_solver` is consulted by `p_sample_loop_known`; `training_losses_segmentation` does not use it to train faster. Keep a normal training schedule such as 1000 steps unless deliberately reproducing a different experiment, and do not confuse sampling step count with training data or training updates.

`--version new` selects the newer preview UNet; `--version 1` selects the legacy preview branch. A checkpoint must be sampled or resumed with compatible architecture/version settings. The bundled DPM solver calls a particular `NoiseScheduleVP`/`DPM_Solver` interface and uses a second-order multistep `dpmsolver++` path in this code. Upgrading unrelated solver or torch dependencies without checking that interface can change or break sampling; it does not repair training data or checkpoint mismatches.

## 9. Actual-training boundary

Only launch the real script after the safe checks, dependency check, branch/channel check, and resource check. It imports Visdom before parsing, initializes `torch.distributed`, builds a full model, loads the dataset, and may run indefinitely. CUDA is the intended execution path; CPU parser/factory checks are useful for syntax and wiring only, not as a truthful replacement for the CUDA, VRAM, throughput, fp16, and multi-GPU behavior of training.
