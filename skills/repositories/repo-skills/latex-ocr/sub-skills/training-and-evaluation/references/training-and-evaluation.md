# Training, Resizer Training, and Evaluation

## Model Training

Training loads `Im2LatexDataset` pickles, constructs the configured encoder and
decoder, optionally checks GPU memory, and writes checkpoints plus a copy of the
config under `model_path/name`.

```bash
python -m pix2tex.train --config path/to/config.yaml
```

If `wandb` is enabled and `--resume` is not set, the script creates a new W&B
run id. Set `debug: true` or disable W&B when offline.

## Resizer Training

The image-resizer trainer uses paired data to learn the preferred width class
for OCR preprocessing. It saves a state dict to `checkpoints/image_resizer.pth`
by default.

```bash
python -m pix2tex.train_resizer \
  --config path/to/config.yaml \
  --out checkpoints/image_resizer.pth \
  --num_epochs 10 \
  --batchsize 10
```

It repeatedly samples resized images, so valid image paths and dimensions are
required.

## Evaluation

Evaluation loads a checkpoint, dataset pickle, and config, then reports:

- BLEU score;
- normalized edit distance;
- token accuracy.

```bash
python -m pix2tex.eval \
  --config path/to/config.yaml \
  --checkpoint path/to/weights.pth \
  --data path/to/val.pkl \
  --batchsize 10 \
  --num-batches 5 \
  --no-cuda
```

Use `--num-batches` for a bounded smoke evaluation before full validation.

## Checkpoint Output

Training writes files named like `<name>_e<epoch>_step<step>.pth` under
`model_path/name/` and writes a `config.yaml` next to them. Keep the tokenizer
and config that produced a checkpoint with the checkpoint when sharing results.
