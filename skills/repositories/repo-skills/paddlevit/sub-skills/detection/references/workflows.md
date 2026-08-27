# Detection workflows

## 1. Preflight and source-root selection

Inputs: one family (`DETR`, `Swin`, or `PVTv2`), a YAML config, a COCO root,
and an optional checkpoint prefix. Outputs: a validated plan and an explicit
final config. No data or checkpoint is downloaded by preflight.

```bash
python <skill-root>/scripts/check_coco_layout.py <coco-root> --split val --check-api --check-images
python <skill-root>/scripts/detection_model_smoke.py --model all --device cpu
cd <source-root>/object_detection/DETR  # or Swin/PVTv2
export PYTHONPATH="$PWD:$PWD/..:${PYTHONPATH:-}"
```

Run the smoke from the skill path, not from a model directory. For a source
run, keep the current working directory at the selected model directory so
local imports resolve consistently. `--check-api` proves `pycocotools` can
import and parse the selected annotation; `--check-images` decodes referenced
files with Pillow and compares metadata dimensions. Without either flag the
layout checker is stdlib-only.

## 2. Config -> build -> one-batch diagnostic

The source config flow is defaults -> recursively merged YAML `BASE` files ->
CLI overrides. Confirm the printed config contains the intended `DATA_PATH`,
`DATASET=coco`, class/head settings, and checkpoint prefix. Use a tiny local
fixture with one valid image/annotation for a first data-loader check when a
real COCO tree is unavailable. The source `build_coco` still requires the
standard split filenames.

The source main modules parse arguments and initialize output/logging at module
import time. Invoke them as scripts rather than importing `main_single_gpu` in
an interactive probe. Before a real run, inspect `run_*.sh` rather than
executing it blindly because launchers may use fixed paths, multiple GPUs, and
long training schedules.

Representative, expensive evaluation:

```bash
cd <source-root>/object_detection/DETR
CUDA_VISIBLE_DEVICES=0 python main_single_gpu.py \
  -cfg=./configs/detr_resnet50.yaml -dataset=coco \
  -batch_size=1 -data_path=<coco-root> -eval \
  -pretrained=<checkpoint-prefix>
```

For Swin use `configs/swin_t_maskrcnn.yaml`; for PVTv2 use
`configs/pvtv2_b0.yaml`. Source loading treats checkpoint arguments as
prefixes and appends `.pdparams`; resume additionally expects `.pdopt`.

A useful first source-level check is to build the model with the shipped YAML
and run one already-collated image batch. Record whether the model returns the
family's expected shape/loss keys. Do not use the standalone smoke as evidence
that the source builder, checkpoint, or COCO evaluator works.

## 3. DETR train/eval reasoning

DETR training uses a nested padded tensor, then returns logits, normalized
center-size boxes, and auxiliary decoder outputs. `SetCriterion` performs
Hungarian assignment and computes class/L1/GIoU losses. Evaluation uses only
the final decoder output and `PostProcess` to make absolute boxes.

Checklist:

- `NUM_CLASSES` includes the COCO category convention expected by the local
  target path; the no-object output is added by the model head.
- `NUM_QUERIES` is consistent with the checkpoint.
- `TRANS.EMBED_DIM % TRANS.NUM_HEADS == 0`.
- `target_sizes` is `[height,width]`; box scaling is width,height order.
- SciPy is installed for Hungarian matching even though no separate `matcher`
  test is required for a safe utility smoke.

The source uses `-eval` to set `config.EVAL`, which disables auxiliary losses
when building DETR. It also changes the batch-size field used for validation.
Do not interpret a successful forward with random weights as meaningful mAP.

## 4. Swin/PVTv2 train/eval reasoning

These models use the same broad workflow:

1. build a family backbone and FPN;
2. load COCO and apply CPU transforms;
3. collate images into a size-divisible padded tensor;
4. pass absolute boxes/classes and image scale metadata to RPN/RoI heads;
5. train by summing returned RPN/RoI losses, or evaluate and convert rows to
   COCO evaluator dictionaries;
6. gather predictions before distributed COCO accumulation.

For a training plan, check `FPN.IN_CHANNELS`, `FPN.OUT_CHANNELS`, `FPN.STRIDES`,
RPN anchor sizes/strides, and `ROI.NUM_ClASSES`. For evaluation, check score
threshold/NMS/top-k and the relationship between `scale_factor_wh` and the
postprocessor's clipping/rescaling. Empty boxes are filtered by the family
collate function; a batch containing only empty targets is not a valid smoke.

## 5. Multi-GPU boundary

Use the family `main_multi_gpu.py` only on one node with visible CUDA devices
and a tested NCCL/Paddle distributed setup. The repository's documented
pattern is process-per-GPU, `DistributedBatchSampler`, `paddle.DataParallel`,
and all-reduce/gather. `-batch_size` is per process. `-ngpus` must match the
number of workers/visible GPUs; verify the actual launcher semantics in the
selected script.

Validation can drop a tail batch in the source distributed sampler, so record
sample-count differences and do not compare such a run to a full single-GPU
mAP without accounting for it. A CPU smoke is not a substitute for this
boundary. Shared AMP/device/process troubleshooting belongs to
`../deployment-and-operations/`.

## 6. Safe stop conditions

Stop before training/evaluation if the layout checker reports missing image
references, annotation JSON failure, non-positive boxes, or category mismatch.
Stop before checkpoint loading on architecture-shape mismatch. Stop and
switch to CPU/parser checks if CUDA is unavailable; do not silently label the
result GPU-verified. Stop before COCO metrics if `pycocotools` is unavailable.
