# Model Zoo and Config Selection

MMDetection's model zoo is organized around `model-index.yml`, per-family `metafile.yml` files, README pages, and config files. A model entry usually provides a canonical model name, optional aliases, collection metadata, a config path, task metrics, training metadata, and a checkpoint URL.

## Navigation Map

| Source | Use It For |
| --- | --- |
| `model-index.yml` | Top-level list of model family metafiles. |
| `configs/<family>/metafile.yml` | Canonical model names, aliases, config paths, metrics, and weights. |
| `configs/<family>/README.md` | Family-specific notes, tables, papers, and caveats. |
| `configs/<family>/*.py` | Actual config files for a family. |
| `mmdet/configs/` | Package-installed config subset usable from installed MMDetection contexts. |

Future agents using this skill may not have the original source checkout. If a task requires an exact source config file that is not present locally, use a MIM model name or ask the user for the config file contents instead of inventing the file.

## Choosing a Config

1. Identify the task: object detection, instance segmentation, panoptic segmentation, tracking, grounding, or open-vocabulary detection.
2. Choose the model family based on speed/accuracy/runtime constraints.
3. Prefer smaller variants for CPU or quick smoke tests: RTMDet tiny/small, Faster R-CNN R50, RetinaNet R50, or Mask R-CNN R50 depending on task.
4. Inspect the model entry for task metrics and checkpoint URL, but do not download weights unless the user asks for inference/testing/training execution.
5. Inspect the config before passing it to another workflow.
6. Reroute actual inference to `inference-visualization`; reroute training/testing to `training-testing`.

## Model Name vs Config Path

Use a MIM/model-zoo name when:

- The package is installed and the user wants a standard model-zoo checkpoint/config pair.
- You want to avoid copying a source config tree with `_base_` dependencies.
- The tool accepts `mim download mmdet --config MODEL_NAME --dest DEST` or an inferencer model alias.

Use a config path when:

- The user has a local custom config or wants to inspect/edit a specific file.
- You need to validate `_base_`, dataloaders, evaluator, or override behavior before execution.
- The config differs from the canonical model-zoo entry.

Avoid mixing a model-zoo checkpoint with a heavily edited architecture config. If only thresholds, paths, dataloaders, batch sizes, or visualization settings change, checkpoint compatibility is usually unaffected. If `model.type`, backbone depth, neck channels, class count, head structure, or preprocessing changes, require a deliberate compatibility check.

## MIM Names and Downloads

MMDetection docs show MIM usage such as:

```bash
mim download mmdet --config rtmdet_tiny_8xb32-300e_coco --dest .
```

The `--config` value is the model entry name from a metafile, not necessarily the literal file basename in every installation layout. For RTMDet, metafiles include names and aliases such as:

| Model Name | Alias | Config Purpose |
| --- | --- | --- |
| `rtmdet_tiny_8xb32-300e_coco` | `rtmdet-t` | Fast object detection baseline. |
| `rtmdet_s_8xb32-300e_coco` | `rtmdet-s` | Small object detection baseline. |
| `rtmdet_m_8xb32-300e_coco` | `rtmdet-m` | Medium object detection baseline. |
| `rtmdet_l_8xb32-300e_coco` | `rtmdet-l` | Larger detection model. |
| `rtmdet-ins_tiny_8xb32-300e_coco` | `rtmdet-ins-t` | Fast instance segmentation baseline. |

If a command might download large checkpoints, ask or reroute to the execution sub-skill. For config-only inspection, use `inspect_config.py` on an existing config file and avoid downloads.

## CPU-Friendly Selection

For CPU inference planning without accidental checkpoint downloads:

- Select small configs first: `rtmdet_tiny_8xb32-300e_coco`, `faster-rcnn_r50_fpn_1x_coco`, or `mask-rcnn_r50_fpn_1x_coco` depending on the task.
- Prefer config inspection over `mim download` until the user confirms weight acquisition.
- Tell the inference sub-skill to pass `device='cpu'` for API execution or equivalent CLI flags.
- Check whether the environment has full `mmcv`; `mmcv-lite` can fail when detection ops import `mmcv._ext`.
- If no checkpoint is available, use the config for architecture inspection only; do not promise useful predictions.

## Reading Metafile Entries

A typical entry contains:

```yaml
Models:
  - Name: mask-rcnn_r50_fpn_1x_coco
    In Collection: Mask R-CNN
    Config: configs/mask_rcnn/mask-rcnn_r50_fpn_1x_coco.py
    Results:
      - Task: Object Detection
        Dataset: COCO
        Metrics:
          box AP: 38.2
      - Task: Instance Segmentation
        Dataset: COCO
        Metrics:
          mask AP: 34.7
    Weights: https://download.openmmlab.com/...
```

Interpretation:

- `Name` is the safest MIM/model-zoo identifier.
- `Alias` is convenient but can be less explicit in scripts or documentation.
- `Config` points to the source-tree config path from the project layout.
- `Results` identifies supported task(s) and expected benchmark dataset/metrics.
- `Weights` is a remote checkpoint URL, not proof that the file exists locally.

## Family Hints

| Need | Start With | Notes |
| --- | --- | --- |
| General detection baseline | Faster R-CNN, RetinaNet, RTMDet | RTMDet is usually a strong modern choice. |
| Instance segmentation | Mask R-CNN, RTMDet-Ins, Mask2Former | Check mask metrics and head classes. |
| Panoptic segmentation | Panoptic FPN, Mask2Former | Ensure panoptic dataset/evaluator settings match. |
| Transformer detector | DETR, Deformable DETR, DINO | More sensitive to schedule and GPU memory. |
| Lightweight smoke check | RTMDet tiny/small | Still needs compatible checkpoint for real predictions. |
| Tracking/video | ByteTrack, SORT, QDTrack, MaskTrack R-CNN | Reroute execution to the relevant tracking/testing workflow. |
| Open-vocabulary/grounding | GLIP, Grounding DINO variants | Check text prompt and optional dependency requirements. |

## Handoff Checklist

When handing a selected config to another sub-skill, include:

- Model entry name or config file path.
- Whether a checkpoint URL/local checkpoint is known.
- Task type and expected output type.
- Device constraint, especially `cpu` vs CUDA.
- Key overrides already applied or proposed.
- Any compatibility risks, such as changed `num_classes` or missing full MMCV.
