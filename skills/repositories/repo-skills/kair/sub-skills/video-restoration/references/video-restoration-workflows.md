# KAIR VRT/RVRT video restoration workflows

This reference covers KAIR's VRT and RVRT video testing and training workflows.
Commands are meant to be run from a KAIR checkout by a user or future agent;
the bundled command builder prints commands only and never imports KAIR or
starts downloads.

## Quick testing workflow

1. Choose the model family and task ID from `vrt-rvrt-task-reference.md`.
   VRT IDs are `001`-`009`; RVRT IDs are `001`-`006`. The namespaces are not
   interchangeable even when the numeric ID describes a similar restoration
   task.
2. Prepare an LQ input folder. For ordinary recurrent video tests, use a nested
   video layout:

   ```text
   testsets/or_custom_lq/
     clip_or_video_001/
       00000000.png
       00000001.png
       ...
     clip_or_video_002/
       00000000.png
       ...
   ```

   If you have ground truth, prepare the same subfolder names and the same frame
   counts under `--folder_gt`. If frames are flat in one directory, move or copy
   them under a single sequence subfolder before using KAIR's VRT/RVRT tests.
   For layout checking, dataset regrouping, LMDB conversion, and meta-info
   generation, use the sibling `data-preparation` sub-skill.
3. Make the pretrained checkpoint available as
   `model_zoo/vrt/<task>.pth` or `model_zoo/rvrt/<task>.pth`, where `<task>` is
   the full task string such as `001_RVRT_videosr_bi_REDS_30frames`. If the file
   is missing, KAIR's native test scripts attempt network downloads before
   inference.
4. Use the command builder to construct a command safely:

   ```bash
   python skills/disco/kair/sub-skills/video-restoration/scripts/build_video_restoration_command.py \
     --family rvrt \
     --task-id 006 \
     --folder-lq testsets/Set8 \
     --folder-gt testsets/Set8 \
     --sigma 50 \
     --tile 0 256 256 \
     --save-result
   ```

   The builder prints a KAIR command like:

   ```bash
   python main_test_rvrt.py --task 006_RVRT_videodenoising_DAVIS_16frames --folder_lq testsets/Set8 --folder_gt testsets/Set8 --sigma 50 --tile 0 256 256 --tile_overlap 2 20 20 --save_result
   ```

5. Review the printed command, then run it from the KAIR checkout only if the
   user accepts the compute, CUDA, network, and storage implications.

### Common custom-folder examples

RVRT video denoising on a custom noisy folder with no GT:

```bash
python skills/disco/kair/sub-skills/video-restoration/scripts/build_video_restoration_command.py \
  --family rvrt --task-id 006 \
  --folder-lq testsets/custom_noisy_video \
  --sigma 25 \
  --tile 0 256 256 \
  --num-workers 4 \
  --save-result
```

The printed command omits `--folder_gt`. In this mode KAIR reports progress and
saves images when `--save_result` is present, but it cannot print PSNR/SSIM.
If a KAIR revision fails on no-GT non-blind denoising because the noise-level
channel is not appended for `SingleVideoRecurrentTestDataset`, either provide a
matched clean `--folder_gt` for evaluation, use a wrapper that appends the sigma
map expected by the model, or switch to a revision that handles no-GT denoising.

VRT REDS4 video SR with GT metrics:

```bash
python skills/disco/kair/sub-skills/video-restoration/scripts/build_video_restoration_command.py \
  --family vrt --task-id 001 \
  --folder-lq testsets/REDS4/sharp_bicubic \
  --folder-gt testsets/REDS4/GT \
  --tile 40 128 128 \
  --save-result
```

VRT video frame interpolation on UCF101-style folders:

```bash
python skills/disco/kair/sub-skills/video-restoration/scripts/build_video_restoration_command.py \
  --family vrt --task-id 009 \
  --folder-lq testsets/UCF101 \
  --folder-gt testsets/UCF101 \
  --tile 0 0 0 \
  --tile-overlap 0 0 0 \
  --save-result
```

## Dataset expectations by mode

- Recurrent video SR and deblurring tests use `folder_lq/<video>/<frame>` and,
  when metrics are requested, `folder_gt/<same_video>/<same_frame>`. LQ and GT
  frame counts must match per video.
- Video denoising with GT commonly uses the same clean folder for both LQ and GT
  and passes `--sigma`; KAIR injects Gaussian noise internally in the GT-backed
  dataset path and evaluates against the clean frames.
- No-GT tests use only `folder_lq/<video>/<frame>` and can save outputs but do
  not compute metrics.
- Vimeo90K tests use `sequences/<clip>/<sequence>/im1.png` through `im7.png`
  and the bundled KAIR meta-info file for the test split. The native VRT/RVRT
  scripts do not automatically fetch the Vimeo90K test set.
- VRT frame interpolation has special readers for Vimeo90K, UCF101, DAVIS, and
  Vid4-style data. Use task `009` and match the folder pattern in
  `vrt-rvrt-task-reference.md`.
- Space-time video SR in the VRT documentation is not a separate test task in
  `main_test_vrt.py`; it combines the VRT Vimeo SR task (`003`) and frame
  interpolation task (`009`) depending on the desired space-time pipeline.

## Tile and overlap semantics

KAIR VRT/RVRT test scripts accept three integers for `--tile` and
`--tile_overlap`.

- `--tile T H W` is documented as temporal clip length plus spatial patch size.
  In the current KAIR VRT/RVRT scripts, `tile[0]` controls temporal tiling and
  `tile[1]` is used as a square spatial patch size. Keep `H` and `W` equal in
  commands for clarity and compatibility with the README examples.
- `0` disables tiling for that dimension. `--tile 0 0 0` tests the full clip and
  full frame after the script pads to the model window; it is fastest but has
  the largest memory demand.
- Temporal stride is `tile[0] - tile_overlap[0]`. Spatial stride is
  `tile[1] - tile_overlap[1]`. Keep each tile value larger than its overlap.
- The spatial patch size must be a multiple of the model spatial window. The
  VRT/RVRT task configs and test scripts use spatial window size `8`, so use
  spatial tiles such as `128`, `192`, or `256`.
- Reducing `T` or the spatial tile lowers GPU memory at the cost of more passes
  and sometimes slightly different metrics or seams. Increase overlap only when
  seam artifacts matter and memory allows it.
- `--num_workers` defaults to `16` in the native scripts. Lower it to `0`-`4`
  for debugging, small custom datasets, low-memory systems, or dataloader
  hangs.

## Auto-download and side-effect caveats

`main_test_vrt.py` and `main_test_rvrt.py` are not bundled as skill scripts
because they instantiate full networks, may compile CUDA extensions, and attempt
network downloads when checkpoints or non-Vimeo testsets are absent. Their
useful command surface is distilled here and in the command builder.

Native test behavior to account for:

- Missing model files are downloaded into `model_zoo/vrt/` or
  `model_zoo/rvrt/` using the full task name as the checkpoint filename.
- Missing non-Vimeo public testsets are downloaded and extracted under
  `testsets/`. A failed network request can leave partial archives or partial
  folders.
- Vimeo90K test data is not auto-downloaded; prepare it manually and verify the
  `sequences/<clip>/<sequence>/im*.png` layout.
- Full inference can be slow and GPU-heavy even when parser help is safe.

## Output and metrics behavior

- With `--save_result`, output PNGs are written under `results/<task>/<video>/`.
  Without `--save_result`, the scripts still run inference and metrics but do
  not save restored frames.
- With `--folder_gt`, the scripts print per-video PSNR, SSIM, PSNR_Y, SSIM_Y and
  then averages.
- Without `--folder_gt`, the scripts print progress only; PSNR/SSIM are not
  meaningful because no GT frames are loaded.
- For Vimeo video SR, the scripts evaluate only the center frame. RVRT mirrors
  the seven-frame input to fourteen frames and averages the two center outputs.
- For VRT frame interpolation, the script keeps the interpolated center output.

## Training workflow

KAIR trains VRT and RVRT through the shared `main_train_vrt.py` script with JSON
configs under `options/vrt/` and `options/rvrt/`.

Distributed command pattern from the KAIR workflows:

```bash
python -m torch.distributed.launch --nproc_per_node=8 --master_port=1234 \
  main_train_vrt.py --opt options/vrt/001_train_vrt_videosr_bi_reds_6frames.json --dist True
```

Single-process smoke or small-budget command pattern:

```bash
python main_train_vrt.py --opt options/vrt/001_train_vrt_videosr_bi_reds_6frames.json
```

Notes:

- Do not pass `--dist False`; the parser stores command-line values as strings,
  and a non-empty string can still trigger distributed initialization. Omit
  `--dist` for non-distributed runs.
- Match `--nproc_per_node` to the number of GPU IDs in the config or edit the
  config's `gpu_ids`, `datasets.train.dataloader_batch_size`, and
  `datasets.train.dataloader_num_workers` consistently.
- Training configs use JSON-with-`//` comments. KAIR's option parser supports
  that format, but generic JSON tools may not.
- Important dataset keys are `datasets.train.dataset_type`, `dataroot_gt`,
  `dataroot_lq`, `meta_info_file`, `io_backend.type`, `num_frame`, `gt_size`,
  `dataloader_batch_size`, and `dataloader_num_workers`.
- VRT/RVRT training expects LMDBs for the provided configs. Use the
  `data-preparation` sub-skill for converting frame folders to LMDB and for
  verifying meta-info keys before training.
- Full training is expensive. Treat `main_train_vrt.py` as reference-only
  guidance during skill verification unless the user explicitly approves a
  dataset, hardware, time, and checkpoint budget.

## Source script decisions

- `main_test_vrt.py` and `main_test_rvrt.py`: command-builder targets only; not
  copied because they depend on full KAIR networks and can auto-download models
  or datasets.
- `main_train_vrt.py`: reference-only training guidance; not copied because it
  launches long training and imports full KAIR model/dataset stacks.
- MATLAB video evaluation scripts: reference-only because they require MATLAB
  and have environment/path assumptions that are not safe as bundled runtime
  scripts.
