# DINO inference and evaluation API reference

This reference is derived from the DINO argument parser, `build_dino`,
`PostProcess`, COCO conversion/transforms, and the two checked-in DINO configs.
Paths below are project-relative names, not hard-coded locations.

## Main evaluation CLI

`main.py` uses a parser with a required config and these relevant options:

| Option | Default / type | Use and output |
|---|---|---|
| `-c`, `--config_file` | required string | Python config; use the same scale/backbone family as the checkpoint. |
| `--coco_path` | a machine-specific default; string | COCO root. Always pass an explicit root rather than relying on the default. |
| `--dataset_file` | `coco` | Selects the COCO builder; panoptic evaluation is a separate setup. |
| `--output_dir` | empty string | Evaluation artifacts such as `log.txt`, `eval.pth`, and optional saved results. Pass a writable directory. |
| `--device` | `cuda` | Torch device. The normal DINO evaluation path expects CUDA and the compiled deformable operator. |
| `--resume` | empty | Loads `checkpoint['model']` for evaluation/resume. A local file or an HTTPS state-dict URL is accepted by the source entry point; prefer a local, already-approved checkpoint. |
| `--pretrain_model_path` | unset | Partial pretraining load for fine-tuning; not the normal COCO evaluation switch. |
| `--eval` | false | Runs `engine.evaluate` and returns after the validation split. |
| `--test` | false | Selects the source test/export path; do not interpret it as COCO val AP without checking its artifact format. |
| `--num_workers` | `10` | Validation dataloader workers. Lower it when diagnosing process/file-descriptor pressure. |
| `--save_results` | false | Saves per-rank result debug data under `output_dir` (including normalized raw boxes in the source debug path). |
| `--save_log` | false | Passes a logger to the evaluation loop. |
| `--amp` | false | Enables CUDA autocast in evaluation. Compare with a non-AMP run before attributing small numeric changes to the model. |
| `--fix_size` | false | Changes dataset resize behavior. Keep the config/default behavior for pretrained-result comparisons. |
| `--remove_difficult` | false | Dataset option; confirm the selected loader actually uses it before comparing AP. |
| `--options key=value ...` | unset | Merges config overrides such as the options in the official eval shell scripts. Quote values containing shell metacharacters. |

`--world_size`, `--rank`, `--local_rank`, `--dist_url`, and
`--find_unused_params` are distributed-launch plumbing. Use the dedicated
training/data routes for launch orchestration; the checked-in
`DINO_eval_dist.sh` uses eight processes and is not a safe default smoke test.

The official evaluation scripts set `dn_scalar=100`, `embed_init_tgt=TRUE`,
`dn_label_coef=1.0`, `dn_bbox_coef=1.0`, `use_ema=False`, and
`dn_box_noise_scale=1.0` as config overrides. Preserve these when reproducing
the README's pretrained-model result unless a deliberate ablation is being
recorded.

## Config and checkpoint contract

`build_dino(args)` requires the config to provide the model construction fields,
including `modelname='dino'`, `num_classes`, `num_queries`, backbone and
transformer settings, `num_feature_levels`, loss settings, `num_select`, and
`nms_iou_threshold`. The checked-in reference configs differ in the important
structural fields below:

| Config | Backbone | Feature levels | Batch-size hint | `num_classes` | `num_select` |
|---|---|---:|---:|---:|---:|
| `config/DINO/DINO_4scale.py` | ResNet-50 | 4 (`return_interm_indices=[1,2,3]`) | 2 | 91 | 300 |
| `config/DINO/DINO_5scale.py` | ResNet-50 | 5 (`return_interm_indices=[0,1,2,3]`) | 1 | 91 | 300 |

Backbone-specific configs (for example Swin or ConvNeXt) are separate model
contracts. A checkpoint trained with a different number of feature levels,
backbone, class count, or query structure can fail at `load_state_dict` or,
worse, be an invalid comparison if loaded non-strictly. The normal evaluation
path loads `checkpoint['model']` strictly. Training checkpoints can also carry
`optimizer`, `lr_scheduler`, `epoch`, `args`, and optionally `ema_model`; these
are not model outputs.

`util.coco_id2name.json` maps COCO category IDs to names. COCO IDs are not a
compact zero-based class list: IDs such as 12, 26, 30, 43, and 82 are absent.
DINO's COCO config uses `num_classes=91` so the logits/class indices can retain
COCO category IDs 1–90; class `0` is not a normal COCO category. For a custom
vocabulary, keep the label IDs and `num_classes >= max_obj_id + 1` consistent
with training; do not silently remap output labels while evaluating.

## Raw model output

The detector forward returns a dictionary:

```text
pred_logits: [B, Q, C]       classification logits
pred_boxes:  [B, Q, 4]       normalized (cx, cy, w, h)
aux_outputs: optional list of dictionaries with the same two keys
```

`Q` is the query count (900 in the reference configs), and `C` is the configured
class-logit width (91 for COCO). `pred_logits` are logits, not probabilities;
`PostProcess` applies `sigmoid()` independently per query/class because DINO
uses focal classification. In the criterion, no-object targets are represented
by an all-zero focal target (the source cardinality helper also treats its final
logit as no-object); `PostProcess` does not remove a no-object class or run a
softmax. It is deliberately a flat query/class selection.

`pred_boxes` are relative to the individual unpadded image, in center format:

```text
cx = center x / image width
cy = center y / image height
w  = box width / image width
h  = box height / image height
```

They are not pixel `xywh`, not `xyxy`, and not `(x_min, y_min, x_max,
y_max)`. Converting to corners is:

```text
x1 = cx - w/2    y1 = cy - h/2
x2 = cx + w/2    y2 = cy + h/2
```

The center/width/height components are produced through normalized model
regression, but converted corner coordinates can legitimately extend outside
`[0, 1]` for a box crossing an image edge. Preserve raw values for diagnosis;
clamp only when drawing or when a consumer explicitly requires image bounds.

## `PostProcess` contract

`postprocessors['bbox'](outputs, target_sizes, not_to_xyxy=False, test=False)`
performs the following operations:

1. `sigmoid(pred_logits)` and flatten `[Q, C]` into `Q*C` scores per image.
2. Select `num_select` highest score entries (300 in both reference configs).
3. Recover `query_index = flat_index // C` and `label = flat_index % C`.
4. Convert `pred_boxes` from normalized `cxcywh` to normalized `xyxy`, unless
   `not_to_xyxy=True` is requested.
5. Multiply by `[image_width, image_height, image_width, image_height]`, where
   `target_sizes` is shaped `[B, 2]` and ordered `[height, width]`.
6. If `nms_iou_threshold > 0`, apply class-agnostic torchvision NMS to the
   selected boxes; the reference configs use `-1`, so no NMS is applied.

For each batch item it returns a dictionary:

```text
{
  "scores": Tensor[K],  # sigmoid scores, descending top-k order before NMS
  "labels": Tensor[K],  # class/category IDs from the logits
  "boxes":  Tensor[K,4] # absolute xyxy by default; absolute cxcywh with not_to_xyxy
}
```

`K` is normally `num_select` and can be smaller after NMS. `test=True` is a
special source path that requires `not_to_xyxy=False` and changes the final two
corner coordinates into widths/heights after conversion; do not use it to
interpret ordinary visualization output.

`target_sizes` is the most common source of wrong boxes:

- **COCO evaluation:** stack `target['orig_size']` (`[original_H, original_W]`)
  before calling `PostProcess`. `engine.evaluate` does this so predictions are
  in original-image pixels for COCO API conversion.
- **Visualization after the dataset transform:** use the transformed,
  unpadded `[H, W]` (`target['size']`), not the padded batch tensor shape.
- **Normalized notebook-style visualization:** the notebook passes
  `[[1.0, 1.0]]`, obtains normalized `xyxy`, converts those boxes back to
  normalized `cxcywh`, and gives the visualizer the transformed image size.
  The bundled smoke script follows this deliberate pattern and emits both
  normalized and transformed-pixel representations.

A score threshold is a consumer-side filter after top-k selection. It does not
change model logits, COCO AP, or the `num_select` work done by `PostProcess`.
The bundled smoke script defaults to `0.30` for readable visualization; choose a
threshold explicitly for a different precision/recall trade-off.

## Dataset/transform facts

`ConvertCocoPolysToMask` starts with COCO `[x, y, width, height]` annotations,
converts them to clipped absolute `xyxy`, removes zero-area/crowd entries, and
stores `orig_size=[H,W]` and the current `size=[H,W]`. The validation transform
uses `RandomResize([800], max_size=1333)` followed by `ToTensor` and
`Normalize([0.485,0.456,0.406], [0.229,0.224,0.225])`; although named
`RandomResize`, the single-element validation scale is deterministic.
`Normalize` converts target boxes to normalized `cxcywh` using the transformed
image dimensions.
