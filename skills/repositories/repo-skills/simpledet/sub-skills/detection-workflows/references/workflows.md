# Detection workflow recipes

## Safe progression

1. Run the setup diagnostic and config inspector.
2. Validate every roidb and checkpoint prefix.
3. Use `run_workflow.py --dry-run` to inspect the exact command and checkout
   root.
4. Run a short single-GPU configuration with known data/weights.
5. Add FP16, multi-GPU, NCCL, or distributed execution one axis at a time.

The wrapper is at `../../scripts/run_workflow.py` relative to this reference's
skill root. It invokes the checkout's public entry point only after printing
its command and working directory.

## Training

```bash
python <skill-root>/scripts/run_workflow.py --repo-root /path/to/simpledet \
  --entrypoint train --config config/faster_r50v1_fpn_1x.py --dry-run
```

Confirm the config points at the right dataset split and pretrain prefix, then
remove `--dry-run`. `begin_epoch=0` starts from the pretrain checkpoint;
nonzero values resume from the experiment checkpoint. Training writes logs,
symbol JSON, parameters, and optional profiler output under the configured
experiment name.

## Bbox evaluation

```bash
python <skill-root>/scripts/run_workflow.py --repo-root /path/to/simpledet \
  --entrypoint test --config config/faster_r50v1_fpn_1x.py --epoch 6 --dry-run
```

The test path loads `pTest.model.prefix` and the selected epoch, reads all
configured cache splits, applies NMS and COCO bbox evaluation, and writes a
split result JSON under the experiment directory.

## Mask evaluation

```bash
python <skill-root>/scripts/run_workflow.py --repo-root /path/to/simpledet \
  --entrypoint mask-test --config config/mask_r50v1_fpn_1x.py --epoch 6 --dry-run
```

Before running, validate polygon records, mask resolution, foreground ROI count,
static padded polygon length, and mask checkpoint compatibility.

## Speed benchmark

```bash
python <skill-root>/scripts/run_workflow.py --repo-root /path/to/simpledet \
  --entrypoint speed --config config/faster_r50v1_fpn_1x.py \
  --shape 800 1333 --gpu 0 --count 100 --dry-run
```

The public benchmark creates a dummy batch, warms up once, times the requested
count, and prints average milliseconds. It still requires a CUDA-capable MXNet
context and may write an inference graph snapshot.

## Fine-tuning and FP16

Use the fine-tune family config after validating VOC/cache names, class counts,
pretrain head compatibility, and a new output prefix. For FP16, change only a
compatible config and verify finite losses on one GPU before enabling multiple
GPUs/NCCL. Keep `batch_image` per GPU.
