# VRT/RVRT troubleshooting

Use this reference when KAIR video restoration fails during VRT/RVRT command
construction, parser import, CUDA extension build, dataset loading, checkpoint
loading, inference tiling, or distributed training.

## CUDA, `nvcc`, `ninja`, and custom extension failures

RVRT imports guided deformable attention from KAIR's `models.op.deform_attn`
module. That module uses PyTorch's C++/CUDA extension loader to compile C++ and
CUDA sources at import time. A realistic RVRT workflow therefore needs:

- CUDA-enabled PyTorch built for a CUDA version compatible with the host driver.
- `nvcc` from a matching CUDA toolkit on `PATH` or discoverable through
  `CUDA_HOME`.
- A host C++ compiler supported by the installed CUDA toolkit.
- `ninja` installed in the Python environment.
- Sufficient writable cache space for PyTorch's extension build cache.

Suggested checks from the user's KAIR environment:

```bash
python - <<'PY'
import torch
print('torch', torch.__version__)
print('torch cuda', torch.version.cuda)
print('cuda available', torch.cuda.is_available())
if torch.cuda.is_available():
    print('device', torch.cuda.get_device_name(0))
PY
nvcc --version
ninja --version
```

Common fixes:

- `No CUDA runtime is found` or `CUDA_HOME environment variable is not set`:
  install/activate a CUDA toolkit compatible with the PyTorch build and export
  `CUDA_HOME` before importing RVRT.
- `ninja: command not found`: install `ninja` in the active environment.
- `invalid device function` or unsupported architecture errors: rebuild for the
  actual GPU architecture, for example
  `export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9"` with values matched to the user's
  GPU. Remove stale PyTorch extension build cache entries before retrying.
- Compiler/CUDA ABI errors: use a compiler version supported by the installed
  CUDA toolkit, or install a PyTorch wheel matching the available CUDA stack.
- CPU-only PyTorch: parser help for some VRT paths may work, but RVRT custom-op
  and realistic VRT/RVRT inference/training are not verified as CPU workflows.

## Missing pretrained models

VRT/RVRT test scripts load checkpoints from:

```text
model_zoo/vrt/<full-task>.pth
model_zoo/rvrt/<full-task>.pth
```

If the file is absent, the native script attempts a network download. If the
host is offline, behind a proxy, or rate-limited, manually place the checkpoint
with exactly the full task filename shown in `vrt-rvrt-task-reference.md`.
Delete partial `.pth` files left by interrupted downloads before retrying.

If `torch.load` fails with an archive or pickle error, suspect a partial or
wrong checkpoint. Re-download the matching task checkpoint and verify the file
path family (`vrt` vs `rvrt`) and task namespace.

## Missing data, empty folders, and Vimeo manual setup

`AssertionError: No dataset found at ...` means the `--folder_lq` root produced
zero video subfolders for the selected dataset reader.

Checklist:

- For ordinary recurrent tests, use `folder_lq/video_name/frame.png`, not a flat
  folder of images. For a single custom video, create one subfolder and put all
  frames there.
- If `--folder_gt` is supplied, use the same subfolder names and frame counts as
  `--folder_lq`.
- Keep frame filenames sortable in temporal order, for example `00000000.png`,
  `00000001.png`, and so on.
- For denoising with GT, it is normal to pass the same clean folder for both
  `--folder_lq` and `--folder_gt`; KAIR injects Gaussian noise internally based
  on `--sigma`.
- For Vimeo90K tests, prepare `sequences/<clip>/<sequence>/im1.png` through
  `im7.png` and keep the KAIR meta-info file naming. The native scripts do not
  automatically download Vimeo90K.
- Route LMDB creation, video regrouping, REDS/DAVIS/DVD/GoPro/UDM10 preparation,
  and meta-info validation to the `data-preparation` sub-skill.

If a native script auto-downloads a non-Vimeo testset and then fails, remove any
partial archive or partial extracted folder under `testsets/` before retrying.

## No-GT custom denoising edge case

For prompts such as "test RVRT denoising on a custom noisy frame folder with no
GT", the intended command is:

```bash
python main_test_rvrt.py --task 006_RVRT_videodenoising_DAVIS_16frames \
  --folder_lq testsets/custom_noisy_video --sigma 25 \
  --tile 0 256 256 --tile_overlap 2 20 20 --save_result
```

Because `--folder_gt` is omitted, KAIR should save outputs under
`results/006_RVRT_videodenoising_DAVIS_16frames/` but cannot compute metrics.
If the local KAIR revision raises a channel mismatch for no-GT non-blind
denoising, the cause is that the no-GT dataset path does not append the sigma
noise-level channel expected by the non-blind denoising model. Workarounds are:

1. Provide a clean matched `--folder_gt` when available, so the GT-backed dataset
   path appends the noise-level channel and computes metrics.
2. Use or write a thin inference wrapper that appends the constant sigma channel
   to each LQ frame before calling the model.
3. Use a KAIR revision that explicitly supports no-GT non-blind denoising.

## OOM, slow inference, and tile problems

Symptoms include `CUDA out of memory`, process kills, or very slow patch-by-patch
inference.

- Reduce temporal tile length: e.g. `--tile 40 128 128` to `--tile 20 128 128`,
  or RVRT `--tile 100 128 128` to `--tile 50 128 128`.
- Reduce spatial tile: e.g. `256` to `192` or `128`. Keep it a multiple of `8`.
- Lower `--num_workers` to `0`-`4` for small datasets or low-memory hosts.
- Avoid `--tile 0 0 0` unless the whole clip and full-resolution frames fit in
  memory.
- Keep tile values larger than overlap values. If overlap is too large, stride
  becomes small and inference gets much slower.
- Use RVRT instead of VRT for comparable SR/deblur/denoise tasks when memory is
  the limiting factor and the RVRT CUDA extension builds successfully.
- For training OOM, lower config keys such as `datasets.train.dataloader_batch_size`,
  `datasets.train.dataloader_num_workers`, `datasets.train.gt_size`, and, where
  appropriate, the number of frames. Re-check dataset and task consistency after
  changing those keys.

If the error says `testing patch size should be a multiple of window_size`, use
spatial tile values divisible by `8` for KAIR's VRT/RVRT tasks.

## DDP, `use_checkpoint`, static graph, and the 20000-iteration resume bug

The VRT/RVRT training docs and `main_train_vrt.py` warn that distributed
training can terminate around `fix_iter` (commonly `20000`) because PyTorch DDP
and `torch.utils.checkpoint` interact poorly when the computation graph changes.
The KAIR configs set `find_unused_parameters: false` and `use_static_graph: true`
for the affected workflows, and the training script saves a checkpoint just
before the graph change.

When this happens:

1. Treat it as an expected resume point, not as failed training.
2. Resume with the same JSON config and the same experiment directory. The
   training script searches the experiment's model directory for the latest
   `G`, `E`, and `optimizerG` checkpoints and starts from the maximum iteration.
3. Do not delete partial checkpoints unless they are corrupt.
4. If the failure repeats immediately, verify that `use_checkpoint_*`,
   `find_unused_parameters`, `use_static_graph`, and `train.fix_iter` are still
   consistent with the original config.

For distributed launches, use the KAIR command pattern:

```bash
python -m torch.distributed.launch --nproc_per_node=8 --master_port=1234 \
  main_train_vrt.py --opt options/vrt/001_train_vrt_videosr_bi_reds_6frames.json --dist True
```

For non-distributed runs, omit `--dist` entirely:

```bash
python main_train_vrt.py --opt options/vrt/001_train_vrt_videosr_bi_reds_6frames.json
```

Do not pass `--dist False`; the script's parser may treat the string `False` as
truthy and initialize distributed mode.

## `num_workers`, dataloader, and multiprocessing issues

- CLI tests default to `--num_workers 16`; training configs commonly use
  `dataloader_num_workers: 32`. These values are high for small local machines.
- If workers hang, crash, or exhaust shared memory, lower CLI `--num_workers` or
  config `dataloader_num_workers`.
- If LMDB data loads fail, verify that the LMDB folder has `data.mdb`,
  `lock.mdb`, and `meta_info.txt`, and route detailed conversion checks to
  `data-preparation`.
- If LQ and GT counts differ, fix the video subfolders or meta-info; do not
  suppress the assertion, because metrics and temporal alignment would be wrong.

## Task namespace and argument mismatches

- VRT task IDs (`001`-`009`) must be used with `main_test_vrt.py` and
  checkpoints under `model_zoo/vrt/`.
- RVRT task IDs (`001`-`006`) must be used with `main_test_rvrt.py` and
  checkpoints under `model_zoo/rvrt/`.
- VRT frame interpolation is task `009`; RVRT has no KAIR task `009`.
- The training config task name is lower-case and prefixed with `train_`; it is
  not the same string as the test script's `--task` value.
- Keep `--sigma` for denoising tasks and omit it for SR/deblur/FI unless a local
  wrapper explicitly supports another behavior.
