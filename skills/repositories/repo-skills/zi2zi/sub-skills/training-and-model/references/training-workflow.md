# Training workflow

## Preflight checklist

Before launching `train.py`, verify:

- `experiment/data/train.obj` exists and contains records.
- `experiment/data/val.obj` exists and contains records.
- `--embedding_num` is at least the highest style label plus one.
- The chosen `--batch_size` fits the GPU memory budget.
- The experiment directory is writable and empty enough that old checkpoints will
  not be mistaken for the new run.
- If using `--fine_tune`, the label IDs exist in the packaged data.

Use the data-preparation helper to check the object files before training:

```sh
python sub-skills/data-preparation/scripts/inspect_zi2zi_obj.py \
  experiment/data/train.obj experiment/data/val.obj --expect-min=1 --image-check
```

## Standard training command

```sh
python train.py \
  --experiment_dir=experiment \
  --experiment_id=0 \
  --image_size=256 \
  --embedding_num=40 \
  --embedding_dim=128 \
  --batch_size=16 \
  --lr=0.001 \
  --epoch=40 \
  --sample_steps=50 \
  --checkpoint_steps=500 \
  --schedule=20 \
  --L1_penalty=100 \
  --Lconst_penalty=15
```

`train.py` also accepts:

- `--resume=1|0`
- `--freeze_encoder=1|0`
- `--fine_tune=0,1,2`
- `--inst_norm=1|0`
- `--flip_labels=1|0`
- `--Ltv_penalty` and `--Lcategory_penalty`

## Label shuffling and fine-tuning

The `flip_labels` mode uses the same source batch with shuffled style labels for
parts of the discriminator/generator loss. It is intended for situations where
`d_loss` becomes too small and later fine-tuning needs a stronger training
signal.

Recommended sequence:

1. Train normally until losses and samples plateau.
2. Start a fine-tuning run for the desired labels with `--fine_tune`.
3. If the discriminator saturates, enable `--flip_labels=1` and continue
   carefully.

## Checkpoint and sample monitoring

- `checkpoint/experiment_<id>_batch_<batch>/unet.model-*` holds TensorFlow
  checkpoints.
- `logs/` contains TensorBoard event files.
- `sample/experiment_<id>_batch_<batch>/sample_<epoch>_<step>.png` contains
  validation samples paired as real and fake images.

If samples do not improve, inspect whether label IDs, embedding count, or input
object files are mismatched.

## Model implementation notes

`model/unet.py` builds a generator with:

- an 8-layer encoder;
- a decoder with skip connections and optional dropout;
- an embedding lookup for style labels;
- a discriminator that outputs real/fake and category logits;
- losses for adversarial fooling, L1 distance, category prediction,
  encoding/constant alignment, and optional TV regularization.

The data provider pads batches to fixed sizes because transpose convolution and
the graph expect deterministic batch dimensions.

Use the bundled [plan_zi2zi_training.py](../scripts/plan_zi2zi_training.py) to
print a validated command line when you want to check arguments without running
TensorFlow.
