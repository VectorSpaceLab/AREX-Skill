# Training troubleshooting

## Unsupported image size

**Symptom:** `ValueError: unsupported image size: ...` while constructing the model.

**Cause:** With an empty `--channel_mult`, `create_model` only maps 64, 128, 256, and 512. `attention_resolutions` is also interpreted by integer division (`image_size // int(resolution)`).

**Action:** Use one of the supported sizes or provide an explicit comma-separated `--channel_mult` after checking that the resulting downsampling and attention layout are valid. Do not treat an arbitrary image size as a harmless resize change. Use the tiny factory recipe with `image_size=64` for wiring checks.

## Invalid boolean values

**Symptom:** `argument --...: boolean value expected`, or a flag appears not to turn on.

**Cause:** The parser uses `str2bool`, not `action="store_true"`.

**Action:** Supply exactly one value from `yes true t y 1 no false f n 0` (case-insensitive), for example `--learn_sigma True` and `--class_cond False`. `--dpm_solver` and `--use_fp16` also require values.

## Missing Visdom or a Visdom connection warning

**Symptom:** The real launcher fails with `ModuleNotFoundError: visdom` before showing help, or reports it cannot connect to port 8850.

**Cause:** `segmentation_train.py` imports `Visdom` and constructs `Visdom(port=8850)` at module import time. This happens before `main()` parses arguments. The object is not needed by the safe inspector, and the current training path does not actively call it for loss logging.

**Action:** Install the declared `visdom` dependency in the training environment. If a dashboard is desired, run a compatible Visdom server on port 8850. If no dashboard is needed, a local source fork can lazy-import or remove that top-level client, but that is a source change—not something the safe inspector should emulate. Use `inspect_train_cli.py` for help/default inspection when the package is unavailable.

## CUDA unavailable or VRAM exhaustion

**Symptom:** NCCL/device errors, `Expected all tensors to be on the same device`, CUDA OOM, or a run that is implausibly slow on CPU.

**Cause:** The launcher is designed around CUDA. `setup_dist` chooses NCCL when CUDA is available; fp16, the intended throughput, and the multi-GPU path are CUDA-specific. `TrainLoop` warns that distributed gradients are not synchronized correctly for a multi-process CPU setup.

**Action:** Verify the selected GPU and free memory before launching. Reduce `batch_size`, then use a positive `microbatch` to bound activation memory; consider `--use_checkpoint True` and only then `--use_fp16 True` on supported CUDA hardware. Keep architecture changes explicit. A CPU parser/factory run can validate imports or construction, but CPU is not a truthful substitute for full training and should not be used to claim convergence.

## Input-channel mismatch

**Symptom:** The first convolution or highway network reports an input-channel mismatch, or checkpoint tensors have incompatible shapes.

**Cause:** The launcher concatenates the loader's image batch and condition/mask tensor. The branch then sets `in_ch`: ISIC → 4, BRATS → 5, custom 2-D → 4, and the current custom 3-D fallback also → 4. The diffusion loss takes the last channel as the mask and the model's highway path uses the preceding channels.

**Action:** Inspect one loader batch before training and verify `batch.shape[1] + cond.shape[1] == args.in_ch`. Use exact `--data_name ISIC` or `BRATS` when appropriate. Do not rely on the initial factory default `in_ch=5`; the launcher overwrites it after branch selection. For custom 3-D, treat the source's four-channel assignment as an implementation detail to verify, not as a general medical-data rule.

## Wrong data branch or no custom 3-D detection

**Symptom:** A custom directory uses the 2-D loader, or a dedicated loader is used unexpectedly.

**Cause:** Exact case-sensitive `data_name` checks run first. Any non-`ISIC`/`BRATS` value reaches the source test `any(Path(args.data_dir).glob("*\\*.nii.gz"))`. On POSIX, the backslash in that pattern is normally a literal character rather than a portable directory separator, so ordinary `.nii.gz` files may not match.

**Action:** Confirm `data_name` is not accidentally `ISIC` or `BRATS`, then run the safe inspector's `--show-branch` against the actual directory. If the source's glob does not match, do not assume the 3-D custom path is active; fix the source pattern or provide an explicit local branch implementation after checking the loader contract. This sub-skill intentionally does not prescribe a full dataset tree.

## Resume appears to work but state is incomplete

**Symptom:** A model checkpoint loads, yet optimizer momentum or EMA behavior resets; an incompatible checkpoint does not fail loudly.

**Cause:** The source uses partial parameter loading. Its normal save names (`optsavedmodelNNNNNN.pt` and `emasavedmodel_RATE_NNNNNN.pt`) do not match the filenames searched during resume (`optNNNNNN.pt` and `ema_RATE_NNNNNN.pt`).

**Action:** Resume with the matching `savedmodelNNNNNN.pt`, preserve every architecture/diffusion/version flag, and verify the output logs and optimizer state explicitly. If full optimizer/EMA continuation is required, reconcile the filename convention or load those states manually in a controlled source change. Never treat a partial-load message as proof of architecture compatibility.

## Multi-GPU selection errors

**Symptom:** Invalid device ordinal, NCCL errors, or unexpected single-device behavior with `--multi_gpu`.

**Cause:** The flag is a string parsed as comma-separated integer IDs, e.g. `--multi_gpu 0,1,2`. In that branch `CUDA_VISIBLE_DEVICES` is not restricted by `setup_dist`; `gpu_dev` is used as the `DataParallel` placement device. The process group is still initialized with hard-coded one-process environment values, and `TrainLoop` adds a DDP wrapper when CUDA is available.

**Action:** Start with a single GPU and a small positive microbatch. If using multiple GPUs, ensure all IDs are visible and use physical IDs consistently; set `--gpu_dev` to a valid primary ID. Do not launch this script as if it were a standard multi-process `torchrun` program without first adapting and testing its distributed setup. Validate collective/device behavior on a short, disposable run before a long job.

## Microbatch behavior is unexpected

**Symptom:** OOM persists, or changing `--microbatch` changes optimization behavior more than expected.

**Cause:** `microbatch <= 0` becomes the full batch. A positive value slices the batch and accumulates gradients, but the source does not divide the accumulated gradient by the number of microbatches. DataParallel/DDP synchronization also differs on non-final slices.

**Action:** Choose a positive microbatch no larger than `batch_size`, keep the effective batch and learning-rate interpretation recorded, and compare a short run before committing. Do not set `--microbatch 0` expecting a zero-size batch; it means full-batch mode.

## Schedule sampler failure

**Symptom:** `NotImplementedError: unknown schedule sampler: ...`, or a resampler fails during construction under a newer NumPy.

**Cause:** Only `uniform` and `loss-second-moment` are implemented. The adaptive implementation uses the deprecated `np.int` alias for its loss-count array in this source, which can fail with newer NumPy versions.

**Action:** Use `--schedule_sampler uniform` for the compatibility baseline. If testing `loss-second-moment`, pin or adapt the environment deliberately and record the change; do not silently attribute an environment failure to the training algorithm.

## DPM-solver or version mismatch

**Symptom:** Sampling fails after changing `--dpm_solver`, or a checkpoint behaves differently with `--version 1`.

**Cause:** `dpm_solver` is a sampling configuration stored on the diffusion object. The bundled sampling path uses a specific DPM-Solver API, `dpmsolver++`, order 2, and a custom segmentation input arrangement. `--version` changes the UNet implementation. Neither option supplies training data or makes a checkpoint architecture-agnostic.

**Action:** Keep `--dpm_solver False` and the documented 1000-step training configuration while validating training. Use `--diffusion_steps 50 --dpm_solver True` only as the README's sampling acceleration configuration. Keep `version`, channel settings, learned-sigma settings, and diffusion schedule consistent between checkpoint creation and use. Check the bundled solver interface before upgrading torch or solver dependencies.

## Logging/output confusion

**Symptom:** No Visdom chart is visible, or expected checkpoints are absent.

**Cause:** Visdom client construction and the repository logger are separate. Logger output defaults to stdout, `log.txt`, and `progress.csv`; checkpoint creation is controlled by `save_interval`, with a save at step zero after the first update. An invalid `save_interval` such as zero causes modulo errors.

**Action:** Check `out_dir`, write permissions, logger environment overrides, and process rank. Use a positive `save_interval`. Expect `savedmodelNNNNNN.pt`, `emasavedmodel_RATE_NNNNNN.pt`, and `optsavedmodelNNNNNN.pt`, and remember the resume filename mismatches documented above.
