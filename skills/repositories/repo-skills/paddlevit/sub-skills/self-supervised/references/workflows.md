# DINO workflows and boundaries

This reference turns the PaddleViT DINO source into bounded operating
procedures. Commands assume the current directory is
`self_supervised_learning/dino`; replace paths explicitly when it is not.

## 1. Read-only preflight

1. Confirm the checkout/commit and inspect the intended YAML. Do not use a
   downloaded model or dataset as an implicit prerequisite.
2. Run the config checker:

   ```bash
   python /path/to/self-supervised/scripts/check_dino_config.py \
     --config ./configs/vit_small_patch16_224.yaml
   ```

3. Run the model smoke without network or a dataset:

   ```bash
   python /path/to/self-supervised/scripts/dino_model_smoke.py \
     --repo-root /path/to/PaddleViT --device cpu
   ```

   On a prepared CUDA machine, repeat with `--device gpu:0`. This proves only
   model/crop plumbing and finite toy outputs; it is not a training result.
4. For an actual run, separately assert `train_list.txt`, image readability,
   free disk, visible CUDA devices, and an output directory that does not
   collide with an existing run.

## 2. Data and crop contract

The ImageNet reader requires this shape:

```text
<root>/train_list.txt
<root>/val_list.txt
<root>/train/<class>/<image>
<root>/val/<class>/<image>
```

List entries may point to any path relative to `<root>`, but the loader joins
that path to the root. Every image is opened as RGB. Training transforms return
a list ordered as two global crops followed by local crops. The default list
has 12 tensors per sample: two 224x224 tensors and ten 96x96 tensors. The
teacher is deliberately called on the first two only.

Do not use a one-tensor CIFAR dataset with the DINO entrypoints without a
separate adapter that produces the same list contract. Labels are loaded but
not used by the DINO loss.

## 3. Intended launch templates

### One GPU

```bash
CUDA_VISIBLE_DEVICES=0 \
python main_dino_single_gpu.py \
  -cfg=./configs/vit_small_patch16_224.yaml \
  -dataset=imagenet2012 \
  -batch_size=32 \
  -data_path=/dataset/imagenet \
  -output=./output \
  -amp
```

`batch_size` is local/per GPU. Remove `-amp` for an FP32 control. AMP is a
CUDA-specific acceleration path in the repository docs, and the source uses
`GradScaler`; test a short job before a long one.

### One-node multi GPU

```bash
CUDA_VISIBLE_DEVICES=0,1 \
python main_dino_multi_gpu.py \
  -ngpus=2 \
  -cfg=./configs/vit_small_patch16_224.yaml \
  -dataset=imagenet2012 \
  -batch_size=16 \
  -data_path=/dataset/imagenet \
  -output=./output \
  -amp
```

The worker initializes `paddle.distributed`, builds a distributed batch
sampler, wraps student and teacher with `paddle.DataParallel`, and all-reduces
loss/center values. Every rank must see the same code, config, visible device
count, and rendezvous environment. `-ngpus` must not exceed the visible usable
CUDA devices. The supplied `run_train_multi.sh` selects eight GPUs and runs a
long ImageNet job; it is documentation, not a smoke command.

Do not claim that a multi-GPU launch is validated by merely parsing the shell
file. A bounded multi-process test must observe worker initialization, a
sampler batch on every rank, one synchronized step, and clean exit.

## 4. Checkpoint lifecycle

The code creates a timestamped train directory below `SAVE`. Intended files
are:

```text
<model-prefix>.pdparams
<model-prefix>.pdopt
<model-prefix>_dino_loss.pdparams   # intended spelling; inspect actual output
```

The multi-GPU saver writes the teacher state, while the single-GPU code intends
to save a model state. Preserve the teacher state for downstream feature use.
For an exact resume, retain model/teacher state, optimizer state, DINO center
buffer, epoch, and effective config. Check all files and their actual suffixes
before invoking `-resume`; the source has inconsistent `.pdparams`/`.pdprams`
and `._dino_loss` spellings and references an ambiguous `model` variable.

A safe resume sequence is:

1. Copy or inspect the existing prefix without modifying it.
2. Verify state-dict keys/shapes and inspect the loss-buffer key (`center`).
3. Set `TRAIN.LAST_EPOCH` to the saved epoch, or use `-last_epoch` only when
   the checkpoint convention is known.
4. Use a new output directory unless overwrite has been explicitly approved.
5. Run one bounded batch and check finite loss before continuing.

A backbone-only `.pdparams` is initialization, not exact resume.

## 5. Backend and duration gates

- CPU: import, YAML, and tiny synthetic forward only. Do not use CPU evidence
  to claim GPU DINO training or AMP support.
- One CUDA GPU: required for the normal training path; first run a tiny CUDA
  model smoke and a bounded batch.
- Multi-CUDA: requires Paddle distributed support, NCCL-compatible setup, and
  one process per visible GPU. A hang is a failed bounded trial until diagnosed.
- AMP: use only after CUDA smoke; repository documentation calls out NVIDIA
  Ampere/Volta/Turing FP16 support. Keep an FP32 control when debugging NaNs.
- Time/data: ImageNet and 400/800 epoch configs are long-running and
  download/storage-heavy. Never start them as an exploratory action; ask for
  an explicit dataset path, GPU allocation, duration, and stop condition.

## 6. Porting boundary

The porting example is not part of the core training workflow. It requires
`torch`, a hub/network access path, and a matching PyTorch DINO model. The
inspected environment intentionally has no torch/timm. A safe port trial uses
local artifacts only, prints both parameter and buffer names/shapes, manually
reviews the mapping, transposes only compatible linear matrices, compares a
batch of outputs, and saves a new Paddle state. Do not port a classifier head
or call it a DINO checkpoint without checking head, teacher, and center state.
