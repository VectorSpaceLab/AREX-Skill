# COCO Zero-shot Evaluation

This reference distills the GroundingDINO COCO zero-shot evaluation workflow into a self-contained procedure. It does not require reading or executing repository demo files; use the bundled helper in `../scripts/grounding_dino_coco_eval.py`.

## Dataset Layout

Use a standard COCO-style validation layout:

```text
datasets/coco/
  annotations/
    instances_val2017.json
  val2017/
    000000000139.jpg
    000000000285.jpg
    ...
```

The annotation JSON must contain `images`, `annotations`, and `categories`. Each `images[*].file_name` is resolved relative to `--image_dir`. For benchmark-comparable COCO zero-shot AP, keep official COCO category names and category IDs; for mini-COCO smoke tests, keep the same category IDs even if the image set is reduced.

## Helper Command

```bash
python sub-skills/evaluation/scripts/grounding_dino_coco_eval.py \
  --config_file configs/GroundingDINO_SwinT_OGC.py \
  --checkpoint_path weights/groundingdino_swint_ogc.pth \
  --anno_path datasets/coco/annotations/instances_val2017.json \
  --image_dir datasets/coco/val2017 \
  --device cuda \
  --num_select 300 \
  --num_workers 4
```

Short flags are available for the model files:

```bash
python sub-skills/evaluation/scripts/grounding_dino_coco_eval.py \
  -c configs/GroundingDINO_SwinT_OGC.py \
  -p weights/groundingdino_swint_ogc.pth \
  --anno_path datasets/coco/annotations/instances_val2017.json \
  --image_dir datasets/coco/val2017
```

The helper preserves the original CLI surface while adding validation before expensive work. It does not download checkpoints or datasets.

## CLI Options

| Option | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--config_file`, `-c` | yes | none | Path to the GroundingDINO Python config that matches the checkpoint. |
| `--checkpoint_path`, `-p` | yes | none | Path to a local checkpoint file containing a `model` state dict, or a raw state dict. |
| `--device` | no | `cuda` | Torch device for model inference, such as `cuda`, `cuda:0`, or `cpu`. |
| `--num_select` | no | `300` | Top-k query/category detections to send to COCO evaluation per image. Changing it affects AP. |
| `--anno_path` | yes | none | COCO annotation JSON, usually `instances_val2017.json`. |
| `--image_dir` | yes | none | Directory containing images referenced by the annotation JSON. |
| `--num_workers` | no | `4` | PyTorch dataloader workers; use `0` for easier debugging or constrained systems. |

## Evaluation Workflow

1. Validate the config file, checkpoint file, COCO annotation JSON, image directory, `num_select`, and `num_workers`.
2. Load the config with `SLConfig.fromfile`, set the requested device, build the model with `groundingdino.models.build_model`, load the checkpoint through `clean_state_dict`, move the model to the device, and call `eval()`.
3. Build a `torchvision.datasets.CocoDetection`-style dataset wrapper that returns transformed images plus `image_id`, filtered ground-truth boxes, and original image size.
4. Use the GroundingDINO transforms `RandomResize([800], max_size=1333)`, `ToTensor()`, and ImageNet normalization, then create a `DataLoader(batch_size=1, shuffle=False, collate_fn=collate_fn)`.
5. Build a category prompt from the annotation categories: `person . bicycle . car . ... .`.
6. Use `build_captions_and_token_span` and `create_positive_map_from_span` to map category text spans into tokenizer positions.
7. Run the model with `captions=[category_prompt]` for each batch.
8. Convert model logits from token probabilities to category probabilities, select the top `--num_select` query/category pairs, convert normalized `cxcywh` boxes to absolute `xyxy`, and emit `scores`, `labels`, and `boxes`.
9. Update `CocoGroundingEvaluator` with `{image_id: prediction}` mappings, then call `synchronize_between_processes()`, `accumulate()`, and `summarize()`.
10. Read the `bbox` AP summary and the final `coco_eval["bbox"].stats` list.

## Expected Signals

- The run prints `Input text prompt:` followed by all category names separated by `.`.
- Progress prints every 30 images in the bundled helper.
- Successful completion prints `IoU metric: bbox`, the standard COCO AP/AR table, and `Final results: [...]`.
- The first value in `Final results` is the primary AP over IoU `0.50:0.95`.
- With the matching Swin-T OGC config/checkpoint and official COCO val2017 data, the README benchmark signal is about `48.5` AP. The model table reports `48.4` zero-shot AP for GroundingDINO-T; small differences can come from dependency versions, hardware kernels, or exact checkpoint/config pairing.

## Benchmark Caveats

- A mini-COCO run on a few images is only a smoke test for wiring and output shape; it cannot validate the reported AP.
- CPU evaluation is useful for parser/data/model-loading checks but is slow and not a realistic benchmark path.
- The benchmark assumes the checkpoint, config, category IDs, and COCO val2017 annotations match. Swapping Swin-T/Swin-B configs or checkpoints invalidates the expected AP.
- Altering `--num_select`, transforms, category prompt construction, text encoder, or dependency versions can change AP.
