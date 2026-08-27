# InternImage Semantic Segmentation Workflows

This reference distills the segmentation workflow evidence from source labels `segmentation/README.md`, `segmentation/train.py`, `segmentation/test.py`, `segmentation/image_demo.py`, `segmentation/dist_train.sh`, `segmentation/dist_test.sh`, `segmentation/slurm_train.sh`, `segmentation/slurm_test.sh`, `segmentation/mmcv_custom`, `segmentation/mmseg_custom`, and `segmentation/ops_dcnv3`.

## Environment assumptions

- The segmentation code is built for MMSegmentation v0.27.0 with `mmcv-full==1.5.0`, `mmdet==2.28.1`, `timm==0.6.11`, PyTorch with CUDA, `numpy<2.0`, and `pydantic==1.10.13` according to repository evidence.
- Real model execution usually requires the DCNv3 operator package available as `ops_dcnv3` and the compiled `DCNv3` extension or a compatible prebuilt wheel. Command construction and parser help do not prove this runtime is ready.
- The generated command helper emits commands that change into `<repo-root>/segmentation` and set `PYTHONPATH` to `<repo-root>` so the repo-specific `mmcv_custom`, `mmseg_custom`, and local `ops_dcnv3` modules can register.
- Keep configs and checkpoints paired. Loading an ADE20K checkpoint with a Cityscapes or COCO-Stuff config commonly produces class-count, palette, or head-shape mismatches.

## Command-builder pattern

Use the bundled helper from this sub-skill tree. It prints a command only; it does not execute it.

```bash
python sub-skills/segmentation/scripts/build_segmentation_command.py --list-configs
python sub-skills/segmentation/scripts/build_segmentation_command.py train --help
python sub-skills/segmentation/scripts/build_segmentation_command.py test --help
python sub-skills/segmentation/scripts/build_segmentation_command.py image-demo --help
```

Pass either `--config configs/<dataset>/<file>.py` or `--config-key <catalog-key>`. If `--repo-root` is omitted, the emitted shell command uses `REPO_ROOT=${REPO_ROOT:-.}` so it can be run from an InternImage checkout or with `REPO_ROOT` set explicitly.

## Training

Single-process training target: source label `segmentation/train.py`.

Key arguments distilled from the parser:

- positional `config`
- `--work-dir` for logs/checkpoints; default is `./work_dirs/<config-stem>`
- `--load-from` to initialize from a checkpoint
- `--resume-from` or `--auto-resume` for interrupted runs
- `--no-validate` to skip validation during training
- `--gpu-id` for non-distributed mode; deprecated `--gpus` and `--gpu-ids` only keep the first GPU
- `--seed`, `--diff_seed`, and `--deterministic`
- `--cfg-options KEY=VALUE ...` for MMSeg config overrides

Example command construction:

```bash
python sub-skills/segmentation/scripts/build_segmentation_command.py train \
  --repo-root /path/to/InternImage \
  --config-key ade20k/upernet_internimage_t_512_160k_ade20k \
  --work-dir work_dirs/ade20k_t
```

Distributed training target: source labels `segmentation/dist_train.sh` and `segmentation/train.py`. The repo launcher uses `python -m torch.distributed.launch`, passes `--launcher pytorch`, and defaults to port `29300`.

```bash
python sub-skills/segmentation/scripts/build_segmentation_command.py dist-train \
  --repo-root /path/to/InternImage \
  --config configs/ade20k/upernet_internimage_b_512_160k_ade20k.py \
  --gpus 8 --port 29300 \
  --work-dir work_dirs/ade20k_b_8gpu
```

Operational notes:

- Non-distributed training converts SyncBN to BN and warns that SyncBN is supported by DDP. Prefer distributed training for configs intended for multi-GPU training.
- InternImage-G and many H/Mask2Former configs are memory-heavy. Config evidence includes `with_cp=True` for InternImage-G and comments that setting `with_cp=True` in H/Mask2Former blocks saves memory.
- `--cfg-options` can override nested config fields, but changing crop size, batch size, class count, or backbone widths can invalidate checkpoint compatibility.

## Evaluation and result output

Evaluation target: source label `segmentation/test.py`.

The test command requires at least one operation: `--out`, `--eval`, `--format-only`, `--show`, or `--show-dir`. The builder defaults to `--eval mIoU` when no operation is supplied.

Important arguments:

- positional `config checkpoint`
- `--eval mIoU` for generic segmentation metrics; `--eval cityscapes` triggers Cityscapes format-result evaluation behavior
- `--work-dir` writes an evaluation JSON; otherwise JSON is written below `./work_dirs/<config-stem>`
- `--out results.pkl` dumps pickled model outputs; the suffix must be `.pkl` or `.pickle`
- `--show-dir <dir>` saves painted images; `--show` attempts interactive display
- `--opacity` controls visualization opacity in `(0, 1]`
- `--aug-test` enables fixed multi-scale + flip testing
- `--format-only` formats results for a test server and cannot be combined with `--eval`
- distributed collection can use `--gpu-collect` or CPU tmpdir collection via `--tmpdir`

Single-GPU evaluation command construction:

```bash
python sub-skills/segmentation/scripts/build_segmentation_command.py test \
  --repo-root /path/to/InternImage \
  --config-key ade20k/upernet_internimage_t_512_160k_ade20k \
  --checkpoint checkpoints/upernet_internimage_t_512_160k_ade20k.pth \
  --eval mIoU --work-dir work_dirs/eval_ade20k_t
```

Distributed evaluation command construction, matching the repo launch pattern with default port `29510`:

```bash
python sub-skills/segmentation/scripts/build_segmentation_command.py dist-test \
  --repo-root /path/to/InternImage \
  --config configs/cityscapes/upernet_internimage_l_512x1024_160k_cityscapes.py \
  --checkpoint checkpoints/upernet_internimage_l_512x1024_160k_cityscapes.pth \
  --gpus 8 --eval mIoU --show-dir work_dirs/cityscapes_l_vis
```

Output behavior to remember:

- If checkpoint metadata contains `CLASSES` and `PALETTE`, evaluation uses it. Otherwise it falls back to the dataset classes and palette from the config.
- Cityscapes format/eval creates formatted output under `imgfile_prefix` from `--eval-options`, or `.format_cityscapes` by default, and removes the temp directory after Cityscapes eval.
- Pickled outputs can be segmentation arrays, pre-eval results, or file paths from `dataset.format_results()` depending on MMSeg behavior.

## Image demo

Image demo target: source label `segmentation/image_demo.py`.

The demo accepts one image file or a directory. Directory mode processes sorted entries and skips files whose extension is not one of `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp`, or `.gif`.

Supported palette choices in the source parser are exactly:

- `ade20k`
- `cityscapes`
- `cocostuff`

Demo command construction:

```bash
python sub-skills/segmentation/scripts/build_segmentation_command.py image-demo \
  --repo-root /path/to/InternImage \
  --image images/example.jpg \
  --config configs/ade20k/upernet_internimage_t_512_160k_ade20k.py \
  --checkpoint checkpoints/upernet_internimage_t_512_160k_ade20k.pth \
  --palette ade20k --out demo --opacity 0.5 --device cuda:0
```

Demo output behavior:

- The `--out` value is an output directory, not a file path; default is `demo`.
- The painted output image keeps the input basename inside the output directory.
- If checkpoint metadata lacks `CLASSES`, demo classes fall back to `get_classes(--palette)`.
- Colors are always taken from `get_palette(--palette)`. For Mapillary, NYU-Depth-V2, or Pascal-Context demos, the native parser cannot select those custom palettes; prefer ADE20K, Cityscapes, or COCO-Stuff demo cases unless the runtime has been intentionally adapted.

## Slurm and schedulers

Source Slurm launchers were inspected but not copied as runtime scripts because partition names, `srun` flags, quota types, and cluster policies are site-specific. If a user needs Slurm, generate the Python command with the helper first, then wrap the same `train.py` or `test.py` invocation in the site scheduler.

The source Slurm train pattern uses these semantics:

```bash
GPUS=<total-tasks> GPUS_PER_NODE=<gpus-per-node> CPUS_PER_TASK=<cpus> \
srun -p <partition> --job-name=<job> --gres=gpu:<gpus-per-node> \
  --ntasks=<total-tasks> --ntasks-per-node=<gpus-per-node> \
  --cpus-per-task=<cpus> --kill-on-bad-exit=1 \
  python -u train.py <config> --launcher slurm <train-options>
```

The source Slurm test pattern adds the checkpoint after the config and passes `--launcher slurm` to `test.py`. Preserve the same config/checkpoint/output flags that the helper emitted.

## Custom plugin registration

The segmentation entrypoints import `mmcv_custom` and `mmseg_custom` before building models/datasets. This is required because the repo registers:

- `CustomLayerDecayOptimizerConstructor` in `mmcv_custom`
- `InternImage` backbone in `mmseg_custom.models.backbones`
- `EncoderDecoderMask2Former`, Mask2Former/MaskFormer heads, pixel decoders, losses, assigners, and samplers in `mmseg_custom.models`
- `MapillaryDataset`, `NYUDepthV2Dataset`, and custom dataset wrappers/pipelines in `mmseg_custom.datasets`

If a future workflow uses generic MMSeg tools directly, it must preserve these imports or equivalent `custom_imports`; otherwise configs containing `type='InternImage'`, `type='EncoderDecoderMask2Former'`, custom heads, or custom datasets will fail to build.

## Source-script decisions

- `segmentation/train.py`, `segmentation/test.py`, `segmentation/image_demo.py`, `segmentation/dist_train.sh`, and `segmentation/dist_test.sh` were adapted into `scripts/build_segmentation_command.py` because safe command construction is useful and does not require datasets/checkpoints.
- `segmentation/slurm_train.sh` and `segmentation/slurm_test.sh` were reference-only because they are cluster-specific.
- `segmentation/deploy.py` was routed to the deployment sub-skill because TensorRT/mmdeploy export is cross-workflow deployment, not ordinary segmentation training/evaluation.
- `segmentation/ops_dcnv3` was distilled for runtime prerequisites and troubleshooting; the CUDA/C++ extension sources were not bundled because they are build-tree-specific and not a safe standalone helper.
