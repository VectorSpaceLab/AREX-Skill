# InternImage Detection Workflows

This reference distills detection workflow evidence from source labels `detection/README.md`, `detection/train.py`, `detection/test.py`, `detection/image_demo.py`, `detection/deploy.py`, `detection/dist_train.sh`, `detection/dist_test.sh`, `detection/slurm_train.sh`, `detection/slurm_test.sh`, `detection/mmcv_custom`, `detection/mmdet_custom`, `detection/ops_dcnv3`, `sam/main_zero_shot_instance_seg.py`, and `sam/engine.py`. It is self-contained operating guidance; do not reopen source documentation for routine commands.

## Environment assumptions

- The detection code targets MMDetection v2.28-era APIs with `mmdet==2.28.1`, `mmcv-full==1.5.0`, `timm==0.6.11`, PyTorch with CUDA, `numpy<2.0`, `pydantic==1.10.13`, and `yapf==0.40.1` according to inspected repository evidence.
- Real training, testing, demo inference, and SAM prompting usually require a GPU and the local DCNv3 operator path. The generated helper checks do not prove that the OpenMMLab runtime, checkpoint files, datasets, CUDA toolkit, or compiled extension are ready.
- Commands emitted by the bundled helper change into `<repo-root>/detection` and set `PYTHONPATH` to include both `<repo-root>` and `<repo-root>/detection`. This preserves top-level imports such as `mmcv_custom`, `mmdet_custom`, and `ops_dcnv3`, while still letting SAM import `detection.*` and `sam.*` modules.
- Keep configs and checkpoints paired. A classification pretraining checkpoint belongs in config initialization or training initialization, not as the evaluation checkpoint for `test.py`.

## Command-builder pattern

Use the bundled helper from this sub-skill tree. It prints a shell command only; it does not execute it.

```bash
python scripts/build_detection_command.py --help
python scripts/build_detection_command.py --list-configs
python scripts/build_detection_command.py train --help
python scripts/build_detection_command.py test --help
python scripts/build_detection_command.py image-demo --help
python scripts/build_detection_command.py sam --help
```

Pass either `--config configs/<dataset>/<file>.py` or `--config-key <catalog-key>`. If `--repo-root` is omitted, the emitted command uses `REPO_ROOT=${REPO_ROOT:-$(pwd)}` and should be run from the checkout root or with `REPO_ROOT` already set.

## Training

Single-process training target: source label `detection/train.py`.

Key arguments distilled from the parser:

- positional `config`
- `--work-dir` for logs/checkpoints; if absent, the source derives `./work_dirs/<config-stem>` from the detection working directory
- `--resume-from` or `--auto-resume` for interrupted runs
- `--no-validate` to skip validation during training
- `--gpu-id` for non-distributed mode; deprecated `--gpus` and `--gpu-ids` only keep one GPU in non-distributed mode
- `--seed`, `--diff-seed`, and `--deterministic`
- `--cfg-options KEY=VALUE ...` for MMDetection config overrides
- `--auto-scale-lr` only works when the config defines compatible `auto_scale_lr` fields

Example command construction:

```bash
python scripts/build_detection_command.py train \
  --repo-root <INTERNIMAGE_REPO> \
  --config-key coco/mask_rcnn_internimage_t_fpn_1x_coco \
  --work-dir work_dirs/mask_rcnn_t_1x \
  --gpu-id 0
```

Distributed training target: source labels `detection/dist_train.sh` and `detection/train.py`. The source launcher uses `python -m torch.distributed.launch`, passes `--launcher pytorch`, and uses a fixed train port value `63667` in the inspected script even though a `PORT` variable is declared.

```bash
python scripts/build_detection_command.py dist-train \
  --repo-root <INTERNIMAGE_REPO> \
  --config-key coco/mask_rcnn_internimage_b_fpn_1x_coco \
  --gpus 8 --port 63667 \
  --work-dir work_dirs/mask_rcnn_b_8gpu
```

Operational notes:

- The released Mask R-CNN configs state a default training shape of 8 GPUs with 2 images per GPU. Changing samples per GPU, image scale, or LR schedule changes comparability.
- Large Cascade XL and DINO/CB-DINO H/G configs are memory-heavy. COCO README evidence explicitly recommends enabling `with_cp=True` when out-of-memory occurs, but changing it is a deliberate config edit.
- DINO/CB-DINO configs use custom DINO heads/transformers and may use very large query counts or Objects365-initialized checkpoints. Validate a smaller config before launching expensive training.

## Evaluation and result output

Evaluation target: source label `detection/test.py`.

The source parser requires at least one action: `--out`, `--eval`, `--format-only`, `--show`, or `--show-dir`. The helper supplies a conservative default only when no action is supplied: `bbox segm` for COCO Mask R-CNN/Cascade instance segmentation configs and `bbox` for detection-only configs.

Important arguments:

- positional `config checkpoint`
- `--eval bbox` for detection metrics; `--eval bbox segm` for COCO instance segmentation configs with masks; `--eval mAP` for VOC/OpenImages-style configs when their dataset evaluator expects mAP
- `--work-dir` writes a metric JSON if evaluation runs
- `--out results.pkl` dumps pickled model outputs and must end in `.pkl` or `.pickle`
- `--format-only` formats results for submission and cannot be combined with `--eval`
- `--show-dir <dir>` saves painted results; `--show` attempts interactive display
- `--show-score-thr` controls visualization threshold, default `0.3`
- distributed collection can use `--gpu-collect` or CPU collection with `--tmpdir`
- `--cfg-options KEY=VALUE ...` and `--eval-options KEY=VALUE ...` are forwarded to the source parser

Single-GPU evaluation command construction:

```bash
python scripts/build_detection_command.py test \
  --repo-root <INTERNIMAGE_REPO> \
  --config-key coco/mask_rcnn_internimage_t_fpn_1x_coco \
  --checkpoint checkpoints/mask_rcnn_internimage_t_fpn_1x_coco.pth \
  --eval bbox segm --work-dir work_dirs/eval_mask_rcnn_t
```

Distributed evaluation target: source labels `detection/dist_test.sh` and `detection/test.py`. The source launcher uses `python -m torch.distributed.launch`, passes `--launcher pytorch`, and defaults the test port to `29511`.

```bash
python scripts/build_detection_command.py dist-test \
  --repo-root <INTERNIMAGE_REPO> \
  --config-key coco/dino_4scale_internimage_t_1x_coco_layer_wise_lr \
  --checkpoint checkpoints/dino_4scale_internimage_t_1x_coco.pth \
  --gpus 8 --port 29511 --eval bbox
```

Output behavior to remember:

- If checkpoint metadata contains `CLASSES`, the model uses it; otherwise the source falls back to dataset classes from the config.
- `--work-dir` controls the metric JSON location; `--out` controls raw pickled outputs and is independent of visualization output.
- Dataset-specific evaluator behavior comes from MMDetection 2.x. Do not mix COCO `bbox/segm` expectations with VOC/OpenImages `mAP` expectations without checking the selected config family.

## Image demo

Image demo target: source label `detection/image_demo.py`.

The demo accepts one image file, a config, and a checkpoint. Supported parser options are:

- `--out <dir>` output directory; default `demo`
- `--device <device>` inference device; default `cuda:0`
- `--palette` choices are exactly `coco`, `voc`, `citys`, and `random`
- `--score-thr <float>` box score threshold; default `0.3`
- `--async-test` is parsed, but the inspected main path uses synchronous inference

Example:

```bash
python scripts/build_detection_command.py image-demo \
  --repo-root <INTERNIMAGE_REPO> \
  --image images/example.jpg \
  --config-key coco/mask_rcnn_internimage_t_fpn_1x_coco \
  --checkpoint checkpoints/mask_rcnn_internimage_t_fpn_1x_coco.pth \
  --out demo --device cuda:0 --palette coco --score-thr 0.3
```

Demo output behavior:

- `--out` is a directory, not an image file. The painted image keeps the input basename inside that directory.
- CPU demo commands can be printed, but the runtime still needs compatible MMDetection, checkpoint, and DCNv3 behavior on CPU or GPU. Treat CPU demo as runtime-dependent, not guaranteed.
- Use `coco` palette for COCO/LVIS/OpenImages by default, `voc` for VOC, and `random` only when class coloring is not semantically important.

## Slurm and schedulers

The source Slurm launchers were inspected but not copied as runtime scripts because partition names, quota flags, and cluster policies are site-specific. Generate the Python command first, then wrap it in the user's scheduler.

Source Slurm train semantics:

```bash
GPUS=<total-tasks> GPUS_PER_NODE=<gpus-per-node> CPUS_PER_TASK=<cpus> \
srun -p <partition> --job-name=<job> --gres=gpu:<gpus-per-node> \
  --ntasks=<total-tasks> --ntasks-per-node=<gpus-per-node> \
  --cpus-per-task=<cpus> --kill-on-bad-exit=1 \
  python -u train.py <config> --work-dir=<work-dir> --launcher=slurm <train-options>
```

Source Slurm test semantics add the checkpoint after the config and pass `--launcher=slurm` to `test.py`. Preserve `--eval`, `--out`, `--show-dir`, and collection options from the helper-generated test command.

## Custom plugin registration

The detection entrypoints import `mmcv_custom` and `mmdet_custom` before building configs. This is required because the repository registers components outside vanilla MMDetection:

- `mmcv_custom` registers `CustomLayerDecayOptimizerConstructor`, `EfficientFFN`, and, for the inspected Torch 1.11 branch, `ZeroAdamW` plus `ZeroHook`.
- `mmdet_custom.models` registers the `InternImage` and `CBInternImage` backbones, DINO/CBDINO detector/head components, custom transformer layers, and `CBChannelMapper`.
- `mmdet_custom.datasets` registers `CrowdHumanDataset`.
- The InternImage backbone imports `ops_dcnv3`, whose CUDA extension module is named `DCNv3` when built.

If a future workflow uses generic MMDetection tools directly, it must preserve equivalent imports or `custom_imports`; otherwise configs containing `type='InternImage'`, `type='CBInternImage'`, `type='DINO'`, `type='CBDINO'`, `type='CBChannelMapper'`, or `type='CrowdHumanDataset'` can fail registry lookup.

## Export routing

Detection export evidence comes from source label `detection/deploy.py`. It accepts `deploy_cfg model_cfg checkpoint img` plus options such as `--test-img`, `--work-dir`, `--calib-dataset-cfg`, `--device`, `--log-level`, `--show`, `--dump-info`, `--quant-image-dir`, `--quant`, and `--uri`. The detected TensorRT example uses the instance-seg dynamic deploy config under the detection deploy config tree, a detection model config, a checkpoint, a demo image, `--work-dir`, `--device cuda`, and `--dump-info`.

Do not treat export as an ordinary detection run. Route TensorRT/mmdeploy/DCNv3 custom-op build planning to the sibling deployment sub-skill, carrying over only the selected detection model config and checkpoint.

## Source-script decisions

- `detection/train.py`, `detection/test.py`, `detection/image_demo.py`, `detection/dist_train.sh`, and `detection/dist_test.sh` were adapted into `scripts/build_detection_command.py` because safe command construction is useful and does not require datasets/checkpoints.
- `detection/slurm_train.sh` and `detection/slurm_test.sh` were reference-only because they are cluster-specific.
- `sam/main_zero_shot_instance_seg.py` and `sam/engine.py` were adapted into the helper's `sam` mode plus `references/sam-integration.md`; real execution remains checkpoint/GPU/SAM-dependent.
- `detection/deploy.py` was distilled for argument semantics and routed to deployment because TensorRT/mmdeploy export has separate backend prerequisites.
- `detection/ops_dcnv3` was distilled for prerequisites and troubleshooting; CUDA/C++ sources were not bundled as standalone runtime helpers.
