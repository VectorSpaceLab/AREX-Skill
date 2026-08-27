# AdelaiDet API and CLI reference

This is a compact reference for the verified public surfaces. Use source/package introspection for implementation details after choosing a route.

## Package and configuration

| Surface | Purpose | Notes |
| --- | --- | --- |
| `import adet` | Imports package and registers modeling modules through `adet/__init__.py`. | Verified with `adet.__version__ == 0.1.1`. |
| `adet.config.get_cfg()` | Returns a Detectron2 `CfgNode` with AdelaiDet defaults installed. | Use this instead of raw Detectron2 `get_cfg` for AdelaiDet configs. |
| `adet.config.add_adet_config(cfg)` | Adds AdelaiDet model/data/input defaults to an existing Detectron2 config. | Useful for custom launchers. |
| `adet.checkpoint.AdetCheckpointer` | Detectron2 checkpointer integration for AdelaiDet models. | Use through the repository train/demo/export flows unless writing a custom loader. |

Verified config sections include `MODEL.FCOS`, `MODEL.BATEXT`, `MODEL.BLENDMASK`, `MODEL.CONDINST`, `MODEL.SOLOV2`, `MODEL.FCPOSE`, `MODEL.MEInst`, `MODEL.BASIS_MODULE`, `MODEL.TOP_MODULE`, `MODEL.BiFPN`, and related input/data defaults.

## Detectron2 registry effects

After `import adet.modeling`, verified registrations include:

- Meta-architectures: `OneStageDetector`, `BlendMask`, `SOLOv2`.
- Backbones/builders: `build_fcos_resnet_fpn_backbone`, `build_vovnet_fpn_backbone`.
- ROI/Text head: `TextHead`.

Registry names are used by YAML config values such as `MODEL.META_ARCHITECTURE`, `MODEL.BACKBONE.NAME`, or ROI head options. If a config says a registry object is missing, confirm that imports go through `adet.config.get_cfg()` and that `import adet` succeeds before config merge.

## Custom operators

| Python surface | Native extension symbol | Backend status | Notes |
| --- | --- | --- | --- |
| `adet.layers.BezierAlign` | `adet._C.bezier_align_forward/backward` | CPU and CUDA source paths exist; CUDA smoke verified. | Used by text-recognition pooling. Input ROIs are `Bx17`: batch id plus 8 Bezier control points. |
| `adet.layers.DefROIAlign` | `adet._C.def_roi_align_forward/backward` | CUDA required for real use. | Source CPU branch raises not-supported. Input ROIs are `Bx5`; offsets are `B x 2 x pooled_h x pooled_w`. |
| `adet._C.ml_nms` | `adet._C.ml_nms` | CUDA required for native op. | Source CPU branch raises not-implemented. The high-level `adet.layers.ml_nms` wrapper uses Detectron2 `batched_nms` for normal boxlist flows. |

A successful CUDA build exposes these extension symbols:

```python
import adet._C as C
assert {'bezier_align_forward', 'def_roi_align_forward', 'ml_nms'} <= set(dir(C))
```

## Data and evaluation surfaces

| Surface | Route | Purpose |
| --- | --- | --- |
| `adet.data.builtin` | `data-prep`, `train-eval` | Registers built-in dataset names and metadata. |
| `adet.data.dataset_mapper.DatasetMapperWithBasis` | `data-prep`, `train-eval` | Mapping for basis-mask/semantic-supervision workflows. |
| `adet.data.fcpose_dataset_mapper.FCPoseDatasetMapper` | `data-prep`, `train-eval` | Mapper for FCPose/keypoint data. |
| `adet.data.datasets.text` | `text-spotting`, `data-prep` | Text dataset parsing and Bezier annotations. |
| `adet.evaluation.TextEvaluator` | `text-spotting` | Text spotting evaluation, lexicon/dictionary-sensitive. Requires `rapidfuzz<3`. |
| `adet.structures.Bezier` / `adet.structures.beziers` | `text-spotting` | Bezier geometry support for text annotations. |
| `adet.utils.visualizer.TextVisualizer` | `demo-visualize`, `text-spotting` | Visualization support for text predictions. |

## Public CLIs and wrappers

The source repository exposes script files rather than installed console entry points. This skill bundles wrappers/adaptations to make usage safer:

| Workflow | Source CLI behavior | Skill-owned entry point |
| --- | --- | --- |
| Training/evaluation | `tools/train_net.py` parses Detectron2 launch args, config, resume/eval-only, and `opts`. | `sub-skills/train-eval/scripts/run_train_eval.py` |
| Demo inference | `demo/demo.py` supports input images, webcam, video, output path, confidence threshold, and config overrides. | `sub-skills/demo-visualize/scripts/run_demo.py` |
| Dataset visualization | `tools/visualize_data.py` previews dataset/source records. | `sub-skills/demo-visualize/scripts/visualize_dataset.py` |
| COCO/PIC/LVIS/text data prep | Dataset scripts create semantic masks or converted annotations. | `sub-skills/data-prep/scripts/*` |
| Checkpoint conversion | `tools/convert_fcos_weight.py`, `rename_blendmask.py`, `remove_optim_from_ckpt.py`. | `sub-skills/export-convert/scripts/*` |
| ONNX export | `onnx/export_model_to_onnx.py` builds the model and exports ONNX. | `sub-skills/export-convert/scripts/export_onnx.py` |

All wrappers have `--help` and most have `--dry-run`; run dry-run before launching expensive or data-dependent work.
