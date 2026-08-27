# Training workflows

These are command-construction patterns, not commands to run unchanged. Replace
every placeholder with a user-selected local path and confirm the data contract,
checkpoint type, CUDA device, and output destination first. The examples contain
no download or network step. The shell variables (`SAM_CKPT`, `ISIC_ROOT`,
`REFUGE_ROOT`, `EFFICIENTSAM_CKPT`, `MOBILE_SAM_CKPT`, `DECATHLON_ROOT`, and
`TRAINING_WRAPPER`) are deliberate user inputs; set them to validated local
paths before running.

## Preflight order

```bash
python scripts/inspect_model_registry.py --net sam --encoder vit_b --mod sam_adpt
python train.py --help
```

Then verify, without launching a long job:

1. the case-sensitive dataset key and sample shape with
   [data preparation](../../data-preparation/SKILL.md);
2. a readable base checkpoint for `-sam_ckpt` and, if applicable, a training
   wrapper for `-weights`;
3. `torch.cuda.is_available()`, the intended `CUDA_VISIBLE_DEVICES` mapping,
   free memory, and a small CUDA allocation; and
4. a new experiment name, writable output root, positive `-vis`, and memory
   values appropriate to the image or volume.

## 2D original SAM Adapter (ISIC pattern)

```bash
CUDA_VISIBLE_DEVICES=0 python train.py \
  -net sam -encoder vit_b -mod sam_adpt \
  -exp_name isic-sam-adapter \
  -sam_ckpt "$SAM_CKPT" \
  -dataset isic -data_path "$ISIC_ROOT" \
  -image_size 1024 -out_size 1024 -b 32 -vis 50 -val_freq 5
```

This follows the README's ISIC recipe while making the encoder, output size,
and positive visualization interval explicit. Lower `-b` first and then
`-image_size` on a constrained GPU; keep target and label semantics unchanged.

## 2D REFUGE multi-class pattern

```bash
CUDA_VISIBLE_DEVICES=0 python train.py \
  -net sam -encoder vit_b -mod sam_adpt \
  -exp_name refuge-sam-adapter \
  -sam_ckpt "$SAM_CKPT" \
  -dataset REFUGE -data_path "$REFUGE_ROOT" \
  -image_size 1024 -out_size 1024 -multimask_output 2 \
  -b 32 -vis 50 -val_freq 5
```

The training dispatcher requires uppercase `REFUGE`; the README's two-class
cup/disc update requires a compatible two-channel contract. The original SAM
branch requests multiple masks when `-multimask_output > 1`. EfficientSAM and
MobileSAM ignore that request in `train_sam` and pass `False`.

There is a source-level uncertainty to resolve before relying on automatic best
checkpoint selection for this route: the REFUGE validation branch unpacks
`edice_cup` and `edice_disc`, but the later save condition compares `edice`,
which is not assigned in that branch. Treat a REFUGE run as requiring a source
fix or an explicit verification of this block; do not hide a resulting
`UnboundLocalError` as a data problem.

## EfficientSAM Adapter pattern

```bash
CUDA_VISIBLE_DEVICES=0 python train.py \
  -net efficient_sam -encoder vit_t -mod sam_adpt \
  -sam_ckpt "$EFFICIENTSAM_CKPT" \
  -exp_name efficient-tiny-adapter -dataset isic -data_path "$ISIC_ROOT" \
  -image_size 256 -out_size 256 -b 2 -vis 20 -val_freq 5
```

Use an EfficientSAM checkpoint with its expected top-level `model` mapping.
Do not infer compatibility from the shared `-sam_ckpt` flag or from a filename.
The EfficientSAM decoder path always requests one mask in this training loop.

## MobileSAM TinyViT LoRA pattern

```bash
CUDA_VISIBLE_DEVICES=0 python train.py \
  -net mobile_sam -encoder tiny_vit -mod sam_lora \
  -sam_ckpt "$MOBILE_SAM_CKPT" \
  -exp_name mobile-tiny-lora -dataset isic -data_path "$ISIC_ROOT" \
  -image_size 1024 -out_size 1024 -mid_dim 4 \
  -b 2 -vis 20 -val_freq 5
```

This is a compatibility-sensitive pattern. `tiny_vit` uses the TinyViT mode
selection and can create LoRA blocks, but the checkpoint must match the full
SAM-like wrapper and image size. Run the static helper and inspect parameter
names in a prepared environment before a long job. MobileSAM's ordinary ViT
entries have different mode behavior; see [model variants](model-variants.md).
For object-aware box inference, use [mobile inference](../../mobile-inference/SKILL.md)
instead of this route.

## 3D MONAI/Decathlon pattern

```bash
CUDA_VISIBLE_DEVICES=0 python train.py \
  -net sam -encoder vit_b -mod sam_adpt \
  -sam_ckpt "$SAM_CKPT" \
  -exp_name btcv-3d-adapter -dataset decathlon \
  -data_path "$DECATHLON_ROOT" -image_size 1024 -out_size 1024 \
  -b 1 -thd True -chunk 48 -roi_size 96 -num_sample 2 \
  -evl_chunk 24 -vis 20 -val_freq 5
```

`-thd True` is truthy under the source parser and enters the 3D path. Never
write `-thd False` to request 2D; omit `-thd`. The MONAI training transform
crops `(roi_size, roi_size, chunk)`, and `num_sample` controls the number of
positive/negative crops. Validation slices complete windows of `evl_chunk`
depth; a trailing remainder can be omitted by the source loop. Lower `-b`,
`-chunk`, `-num_sample`, and `-roi_size` for training OOM, and lower
`-evl_chunk` independently for validation OOM.

## Validation cadence and visualization

The global settings set `EPOCH = 100`; the loop uses zero-based epochs. For
epochs `0` through `4`, validation runs before training. After training, the
condition is:

```text
(epoch and epoch % args.val_freq == 0) or epoch == settings.EPOCH - 1
```

Thus the default `-val_freq 5` validates after epochs 5, 10, ..., 95 and the
final epoch 99 (and before each of the first five epochs). A non-positive
interval is unsafe. `-vis` is a batch interval; the validation path evaluates
`ind % args.vis`, so `None` can fail even when no visualization was intended.

## Checkpoint, output, and warm-start behavior

The source creates a fresh directory with `set_log_dir('logs', args.exp_name)`:

```text
logs/<exp_name>_<timestamp>/
  Model/
  Log/
  Samples/
```

TensorBoard is configured below `runs/<net>/<settings.TIME_NOW>/`. The source
also creates `checkpoint/<net>/<settings.TIME_NOW>/` and a filename template,
but the shown save call writes to the experiment `logs/.../Model` directory,
not that unused template path. For an improving non-REFUGE validation result,
the save helper writes:

```text
logs/<exp_name>_<timestamp>/Model/best_dice_checkpoint.pth
logs/<exp_name>_<timestamp>/Model/checkpoint_best.pth
```

The saved mapping has this source schema:

```python
{
    'epoch': epoch + 1,
    'model': args.net,
    'state_dict': state_dict,
    'optimizer': optimizer.state_dict(),
    'best_tol': best_dice,       # source stores this variable, not best_tol
    'path_helper': args.path_helper,
}
```

`state_dict` is the unwrapped network state unless distributed mode selects
`net.module.state_dict()`. `-weights` expects this wrapper and reads
`epoch`, `best_tol`, `state_dict`, and `path_helper`; it loads only
`state_dict` with `strict=False`. Optimizer restoration is commented out, and
the source immediately creates a new timestamped `logs` directory, so this is
a model warm start rather than an exact optimizer-continuation resume.

A safe warm-start pattern is:

```bash
CUDA_VISIBLE_DEVICES=0 python train.py \
  -net sam -encoder vit_b -mod sam_adpt \
  -sam_ckpt "$SAM_CKPT" \
  -weights "$TRAINING_WRAPPER" \
  -exp_name resumed-isic -dataset isic -data_path "$ISIC_ROOT" \
  -image_size 512 -out_size 512 -b 1 -vis 10 -val_freq 5
```

Keep the same architecture/mode and use a new `-exp_name`. For independent
checkpoint scoring, route to [evaluation](../../evaluation/SKILL.md), whose
loader has stricter/distributed-specific state-dict handling.

## What these patterns do not do

They do not acquire checkpoints, datasets, optional dependencies, or CUDA
extensions. Full training, notebook execution, and real-data validation are
long or side-effecting operations; run them only after the preflight gate and
record any skipped or backend-blocked verification explicitly.
