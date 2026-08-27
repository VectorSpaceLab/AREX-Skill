---
name: inference-evaluation
description: "Routes DINO checkpoint evaluation on COCO, single-image inference,
  normalized box postprocessing, notebook-independent visualization, and bounded
  GFLOPS inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DINO inference and evaluation

Use this route when a Researcher needs to inspect a pretrained DINO detector,
measure COCO box AP, run one custom image, understand the raw and postprocessed
box tensors, or obtain a bounded architecture/FPS/GFLOPS smoke measurement.
The route assumes a prepared DINO project root, a compatible config/checkpoint,
and the verified runtime (`torch 2.5.1+cu121`, `torchvision 0.20.1+cu121`, and an
importable `MultiScaleDeformableAttention` extension). Ordinary COCO detection
also needs `pycocotools`; `panopticapi` is only needed for a panoptic path. It
does not download weights/data or start a long evaluation by default.

## Route boundaries

- **Include here:** pretrained checkpoint evaluation, one-image inference,
  COCO AP interpretation, `pred_boxes`/`PostProcess` semantics, thresholding,
  output inspection, notebook-derived visualization, and safe benchmark
  interpretation.
- **Route training away:** training, fine-tuning, resume orchestration,
  distributed launch, Slurm/Submitit scheduling, and optimizer changes →
  `../training/`.
- **Route setup away:** installing the package, compiling or repairing the
  deformable-attention extension, COCO directory preparation, and config/data
  mutation → `../data-model-setup/`.

Treat checkpoints as trusted local pickle-like artifacts; do not load an
untrusted file. Do not claim a model is evaluated merely because it loads. A
COCO result needs an evaluation log and the COCO evaluator's reported AP; a
custom-image result needs the image/config/checkpoint identity and the
postprocessing coordinate space.

## Fast route

1. **Preflight the triplet.** Pair a 4-scale checkpoint with
   `config/DINO/DINO_4scale.py` and a 5-scale checkpoint with
   `config/DINO/DINO_5scale.py`; also match the backbone and class vocabulary.
   Check that the extension and optional Python imports listed above work.
   Confirm the COCO root has `train2017/`, `val2017/`, and
   `annotations/instances_{train,val}2017.json`. See
   [troubleshooting](references/troubleshooting.md) before changing anything.
2. **Run COCO evaluation only when requested.** Use the bundled evaluator
   planner to replace the source shell wrappers. It prints a command and does
   not launch unless `--launch` is supplied:

   ```bash
   python skills/disco/dino/scripts/run_dino_eval.py \
     --project-root /path/to/DINO \
     --config config/DINO/DINO_4scale.py \
     --coco-path /path/to/COCODIR \
     --checkpoint /path/to/checkpoint \
     --output-dir /path/to/eval-output
   ```

   Add `--launch` only after reviewing the command and setup gate. For a direct,
   explicit run use:

   ```bash
   python main.py \
     --output_dir /path/to/eval-output \
     -c config/DINO/DINO_4scale.py \
     --coco_path /path/to/COCODIR \
     --eval --resume /path/to/checkpoint \
     --options dn_scalar=100 embed_init_tgt=TRUE \
       dn_label_coef=1.0 dn_bbox_coef=1.0 use_ema=False \
       dn_box_noise_scale=1.0
   ```

   This constructs the validation loader and evaluates the full requested
   split. Do not substitute `--pretrain_model_path` for `--resume` when the
   goal is evaluation: the former is the partial-load/fine-tuning path.
3. **Run one custom image with the bundled smoke tool.** It reimplements the
   notebook's RGB → resize → tensor → ImageNet normalization → model → bbox
   postprocess flow and does not import the notebook or source visualizer:

   ```bash
   python skills/disco/dino/sub-skills/inference-evaluation/scripts/inference_smoke.py \
     --project-root /path/to/DINO \
     --config config/DINO/DINO_4scale.py \
     --checkpoint /path/to/checkpoint \
     --image /path/to/image.jpg \
     --device cuda \
     --score-threshold 0.30 \
     --output-json /tmp/dino-predictions.json \
     --visualize /tmp/dino-predictions.png
   ```

   The project root is intentionally explicit; no checkout or environment
   path is embedded in the script. A CPU invocation is useful for parser,
   transform, or dependency diagnostics but may fail at the CUDA deformable
   attention operator and is not an equivalent inference result. The command
   has one image and one forward pass as its default scope.
4. **Interpret the result.** Raw `pred_boxes` are normalized
   `(center_x, center_y, width, height)` values. The bbox postprocessor selects
   the top-scoring query/class pairs, converts boxes to `xyxy`, and scales them
   by `(image_width, image_height, image_width, image_height)`. For COCO AP it
   receives each target's original `[height, width]`; for visualization the
   transformed, unpadded size is the correct pixel target size. The bundled
   script intentionally passes `[[1.0, 1.0]]` to `PostProcess`, then derives
   normalized boxes and resized-image pixel boxes for its visualization output.
5. **Benchmark narrowly.** Use `tools/benchmark.py` only for an explicitly
   requested architecture/FPS/GFLOPS check. It is CUDA-only, uses 20 validation
   images and repeated warmups, does not load a checkpoint, and can warn about
   unsupported traced operations. See [benchmarking](references/benchmarking.md).

## Read next

- [API reference](references/api-reference.md) for parser flags, config
  families, tensor shapes, class IDs, and exact `PostProcess` output.
- [Workflows](references/workflows.md) for checkpoint/COCO evaluation and
  custom-image inference with expected artifacts.
- [Benchmarking](references/benchmarking.md) for the bounded GFLOPS/FPS command,
  output schema, and limitations.
- [Troubleshooting](references/troubleshooting.md) for useful failure recovery,
  normalization mistakes, and optional visualization dependencies.
- [Bundled smoke script](scripts/inference_smoke.py) for a safe, parser-checked,
  notebook-independent one-image run.
- [Root evaluation planner](../../scripts/run_dino_eval.py) for a print-only
  replacement of the source shell launchers.

## Completion and evidence

Record the config path, checkpoint path/key, device, COCO root or image, command,
score threshold, transformed/original image sizes, output files, and any
warnings. A successful load is a smoke result, not an AP claim. Keep long
benchmark/evaluation logs outside this skill directory.
