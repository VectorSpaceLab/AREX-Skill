# Sampling workflow and contracts

This reference records the behavior of the source sampler and its supporting
modules. It is an operating contract, not a request to run the source files as
CPU tests. Use the bundled inspector to validate parsing and effective defaults;
reserve actual sampling for a prepared application runtime.

## 1. Flag surface and safe preflight

The source sampling parser combines these sampler defaults with the model and
diffusion defaults from `script_util.py`:

| Flag | Default | Meaning and cautions |
|---|---:|---|
| `--data_name` | `BRATS` | Exact branch labels are `ISIC`, `BRATS`, and the fallback custom branch. |
| `--data_dir` | `../dataset/brats2020/testing` | Branch-specific data root. |
| `--out_dir` | `./results/` | Directory for debug images and ensemble images. |
| `--model_path` | empty | Required for real inference; it is loaded with `map_location="cpu"`. |
| `--image_size` | `64` | Must be compatible with the checkpoint/model construction; published examples use `256`. |
| `--batch_size` | `1` | The implementation assumes one path/ID in several places; keep it at 1 unless the sampler is patched. |
| `--num_ensemble` | `5` | Number of stochastic masks aggregated per input. Must be positive. |
| `--use_ddim` | `False` | Selects the DDIM-known loop in the source, but see the DDIM incompatibility below. |
| `--dpm_solver` | `False` | Passed into diffusion construction; effective only through the non-DDIM known loop. |
| `--diffusion_steps` | `1000` | Progressive steps, or DPM-Solver steps when that path is active. The published speed suggestion is `50` with DPM-Solver; the source comments that roughly `20`–`30` DPM-Solver steps can work well. |
| `--version` | `new` | Selects the new versus legacy UNet and changes which returned mask is ensembled. |
| `--clip_denoised` | `True` | Clipping option passed to the sampler. |
| `--debug` | `False` | Writes per-ensemble diagnostic JPEGs and contains extra CUDA-specific debug paths. |
| `--gpu_dev` | `0` | Device selector used by distributed setup when `--multi_gpu` is absent. |
| `--multi_gpu` | `None` | Parser surface for multi-GPU setup; the sampling loop still has single-batch/path assumptions. |
| `--num_samples` | `1` | Parsed but not used by the sampling loop. |

Other model/diffusion flags are accepted exactly as exposed by
`model_and_diffusion_defaults()`: `num_channels=128`, `num_res_blocks=2`,
`num_heads=4`, `in_ch=5`, `class_cond=False`, `learn_sigma=False`,
`use_scale_shift_norm=True`, `attention_resolutions="16,8"`, `noise_schedule="linear"`,
`rescale_timesteps=False`, `rescale_learned_sigmas=False`, and the remaining
UNet/diffusion construction flags. Published ISIC/BRATS examples override
important model values, notably `image_size=256`, `num_channels=128`,
`num_res_blocks=2`, `num_heads=1`, `learn_sigma=True`,
`use_scale_shift_norm=False`, and `attention_resolutions=16`.

Use `scripts/inspect_sample_cli.py --help` and a proposed flag set before any
checkpoint or data access. The inspector reports the effective branch plan and
makes clear that the branch overwrites `in_ch`:

- **ISIC:** RGB image (3 channels) plus one random noise channel, effective
  `in_ch=4`; transform is resize then tensor conversion.
- **BRATS:** four MRI channels plus one random noise channel, effective
  `in_ch=5`; the 3-D loader exposes virtual slice names and binarizes tumor
  labels. The source constructs `BRATSDataset3D` without `test_flag=True`, so
  its input tree is expected to contain the five sequence files, including the
  segmentation channel, unless the loader call is corrected.
- **Custom:** the 2-D loader pairs sorted `images/*.png` and `masks/*.png`,
  converts image/mask to RGB/L, and the effective model input is again `4`.
  The source's custom branch does not assign `slice_ID` before writing output;
  a custom run therefore needs a naming patch or an adapter rather than blind
  execution.

## 2. Checkpoint and model compatibility

The sampler constructs a model before loading the checkpoint. The source model
has `out_channels=2` regardless of `learn_sigma`; checkpoint compatibility is
therefore determined by the whole construction, not only by the input image:

- Match `version` (`new` uses `UNetModel_newpreview`; any other string selects
the legacy preview model), `in_ch`, image size, channel/resolution settings,
attention settings, and other architecture flags used during training.
- Match the model's expected state-dict key names and tensor shapes. Loading is
strict; shape/key mismatches fail rather than being partially ignored.
- `dist_util.load_state_dict` deserializes the file directly. A checkpoint
  wrapper such as `{"state_dict": ...}` is not unwrapped by the sampler.
- The sampler attempts to remove `module.` from DataParallel keys by assigning
  `new_state_dict[k[7:]]` whenever the substring `module.` appears. This works
  for the usual all-prefixed state dict, but it is not a robust prefix-normalizer:
  a mixed dict can be overwritten by the `else` branch, and a non-prefix
  occurrence is also sliced at position 7. Validate key sets before sampling.

The branch assignment of `args.in_ch` occurs after parsing and before model
creation, so a user-supplied `--in_ch` does not override ISIC/BRATS/custom
branch behavior. A checkpoint trained for another channel count cannot be made
compatible by changing only the flag.

## 3. Sampling choices and version behavior

For each input batch the sampler forms `img = concat(input, random_noise)` and
repeats the known-image diffusion loop `num_ensemble` times. With
`--use_ddim False`, it selects `p_sample_loop_known`; with `--use_ddim True`, it
selects `ddim_sample_loop_known`.

- The DDPM path progressively keeps the original image channels and resamples
  the last segmentation/noise channel. It returns `(sample, x_noisy, org,
  cal, cal_out)`.
- The DDIM-known function in the source has no `step` parameter, while the
  caller always passes `step=args.diffusion_steps`. Consequently the literal
  DDIM path raises an unexpected-keyword `TypeError` until the caller/function
  contract is patched. Its internal starting timestep is also hard-coded near
  500 rather than using the requested diffusion step.
- DPM-Solver is selected inside the non-DDIM known loop when `--dpm_solver
  True`. It uses a discrete beta schedule, `dpmsolver++`, dynamic thresholding,
  order 2, multistep, and `steps=args.diffusion_steps`. If both `--use_ddim`
  and `--dpm_solver` are true, the caller chooses DDIM first, so the DPM-Solver
  branch is not reached (and the DDIM keyword bug still applies).
- For `version == "new"`, each ensemble member is `sample[:, -1, :, :]`.
  For every other version string, it is `cal_out`. Do not compare new and
  legacy output values as if they came from the same post-processing path.

The source records CUDA-event timing for every ensemble member and calls
`cuda.synchronize()` even though distributed setup can choose CPU/Gloo. This
makes a real CPU sampling run unsafe; use the parser/evaluator checks for CPU
validation and require a compatible CUDA runtime for sampling.

## 4. Ensemble and output contract

The source stacks the `num_ensemble` members and calls the repository's
`staple` helper. That helper is a mean-vote operation followed by one optional
reweighting pass; it is not a general external STAPLE implementation. The
result is squeezed and written with `torchvision.utils.save_image` as a JPEG.

With `batch_size=1` and the standard names, output is:

- debug member: `<slice_ID>_output0.jpg`, `<slice_ID>_output1.jpg`, ...;
- aggregate: `<slice_ID>_output_ens.jpg`.

Only names containing the literal substring `ens` are selected by the original
ISIC evaluator. The aggregate is an intensity image, not a guaranteed binary
mask; the evaluator normalizes it by its maximum before thresholding.

ID derivation is brittle:

- ISIC uses the final underscore-delimited token before the extension. An input
  `ISIC_0000003.jpg` produces ID `0000003`, and the aggregate is
  `0000003_output_ens.jpg`.
- BRATS uses a virtual loader path and combines underscore token `-3` with the
  text after `slice`; this is intended to yield a case/slice ID such as
  `123_0`, but depends on the loader's filename convention.
- Custom data has no source assignment for `slice_ID` and fails at output
  construction unless patched.

`shuffle=True` is used in the source DataLoader. With `batch_size>1`, only
`path[0]` is used to derive one ID while tensors can contain multiple examples,
so output collisions or mislabeled batches are possible. Keep `batch_size=1`
for the unpatched implementation. `num_samples` has no effect.

## 5. Safe boundaries

A successful parser inspection proves only argument parsing and branch planning.
A successful bundled evaluator proves only image pairing and metric arithmetic.
Neither proves model import, checkpoint loading, CUDA kernel support, dataset
loading, or diffusion quality. Real inference requires all of:

1. a trained checkpoint whose unwrapped keys and architecture match the exact
   effective configuration;
2. the correct ISIC/BRATS/custom loader data contract and expected dimensions;
3. a compatible CUDA/PyTorch/torchvision environment, with CUDA events working;
4. an output directory with enough space for JPEGs and ensemble members; and
5. an explicit decision about whether the DDIM caller bug and custom naming bug
   have been patched.

Do not add training-loop instructions or treat a source-script import as a
substitute for these gates.
