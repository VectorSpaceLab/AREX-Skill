# EfficientViT Workflows

## Classification

### Evaluate a pretrained model

```bash
python main.py --eval --model EfficientViT_M4 --resume <checkpoint> --data-path <imagenet-root>
```

### Train classification

```bash
python -m torch.distributed.launch --nproc_per_node=8 --master_port 12345 --use_env main.py \
  --model EfficientViT_M4 --data-path <imagenet-root> --dist-eval
```

### Quick throughput benchmark

Use `../scripts/benchmark_efficientvit.py` for a shorter, configurable benchmark instead of the original long-running `speed_test.py` loop.

```bash
python ../scripts/benchmark_efficientvit.py --model EfficientViT_M4 --device cuda --batch-size 512
```

## Downstream detection / segmentation

### Evaluate COCO checkpoints

```bash
bash ./dist_test.sh configs/retinanet_efficientvit_m4_fpn_1x_coco.py <checkpoint> 8 --eval bbox
bash ./dist_test.sh configs/mask_rcnn_efficientvit_m4_fpn_1x_coco.py <checkpoint> 8 --eval bbox segm
```

### Train COCO checkpoints

```bash
bash ./dist_train.sh configs/retinanet_efficientvit_m4_fpn_1x_coco.py 8 --cfg-options model.backbone.pretrained=<imagenet-pretrain-checkpoint>
bash ./dist_train.sh configs/mask_rcnn_efficientvit_m4_fpn_1x_coco.py 8 --cfg-options model.backbone.pretrained=<imagenet-pretrain-checkpoint>
```

## Input expectations

- Classification expects ImageNet-1k in a folder or tar layout described in the repo README.
- Downstream expects COCO 2017 with `annotations/`, `train2017/`, and `val2017/`.
- Downstream commands assume the ImageNet-pretrained backbone checkpoint already exists.
