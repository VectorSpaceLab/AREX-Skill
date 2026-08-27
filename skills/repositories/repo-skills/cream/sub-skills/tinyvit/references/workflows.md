# TinyViT Workflows

## Evaluate on ImageNet-1k

```bash
python -m torch.distributed.launch --nproc_per_node 8 main.py \
  --cfg configs/1k/tiny_vit_21m.yaml --data-path <imagenet-root> --batch-size 128 \
  --eval --resume <checkpoint>
```

## Save sparse teacher logits on ImageNet-22k

```bash
python -m torch.distributed.launch --nproc_per_node 8 save_logits.py \
  --cfg configs/teacher/clip_vit_large_patch14_22k.yaml --data-path <imagenet22k-root> \
  --batch-size 128 --eval --resume <teacher-checkpoint> \
  --opts DISTILL.TEACHER_LOGITS_PATH <output-dir>
```

## Check saved logits

```bash
python -m torch.distributed.launch --nproc_per_node 8 save_logits.py \
  --cfg configs/teacher/clip_vit_large_patch14_22k.yaml --data-path <imagenet22k-root> \
  --batch-size 128 --eval --resume <teacher-checkpoint> \
  --check-saved-logits --opts DISTILL.TEACHER_LOGITS_PATH <output-dir>
```

## Finetune 22k to 1k

```bash
python -m torch.distributed.launch --nproc_per_node 8 main.py \
  --cfg configs/22kto1k/tiny_vit_21m_22kto1k.yaml --data-path <imagenet-root> \
  --batch-size 128 --pretrained <checkpoint> --output <output-dir>
```

## Finetune to higher resolution

```bash
python -m torch.distributed.launch --nproc_per_node 8 main.py \
  --cfg configs/higher_resolution/tiny_vit_21m_224to384.yaml --data-path <imagenet-root> \
  --batch-size 32 --pretrained <checkpoint> --output <output-dir> --accumulation-steps 4
```

```bash
python -m torch.distributed.launch --nproc_per_node 8 main.py \
  --cfg configs/higher_resolution/tiny_vit_21m_384to512.yaml --data-path <imagenet-root> \
  --batch-size 32 --pretrained <checkpoint> --output <output-dir> --accumulation-steps 4
```

## Train from scratch on ImageNet-1k

```bash
python -m torch.distributed.launch --nproc_per_node 8 main.py \
  --cfg configs/1k/tiny_vit_21m.yaml --data-path <imagenet-root> --batch-size 128 --output <output-dir>
```

## Input assumptions

- ImageNet-1k uses the standard folder or tar layout described in the repo docs.
- ImageNet-22k uses the class-archive layout and file-list described in the docs.
- `DATA.DEBUG True` is helpful when you only want a fast sparse-logit or layout sanity check.
