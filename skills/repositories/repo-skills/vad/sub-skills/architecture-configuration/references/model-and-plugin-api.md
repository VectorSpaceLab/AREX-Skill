# VAD model and plugin API

## Registry entry points

The plugin package imports custom assigners/coders/costs, datasets and pipelines, the VoVNet utility backbone, optimizer, model utilities, and the VAD package. The VAD package registers or exposes:

- `VAD`, a detector built on the MMDetection3D two-stage detector base.
- `VADHead`, the multi-branch head for object detection, map vectors, motion/future trajectories, and ego planning.
- `VADPerceptionTransformer`, plus custom decoder/layer sequences and attention modules.
- Custom dataset `VADCustomNuScenesDataset`.
- Custom coders including `CustomNMSFreeCoder`, `MapNMSFreeCoder`, and future-trajectory coding support.
- Custom Hungarian assigners, map/trajectory/planning losses, hooks, runner, and dataset pipeline transforms.

The decorators in the source register classes into MMDetection/MMCV registries. Config strings are resolved only after the module containing the registration has been imported.

## Data flow

1. Multi-view camera images are loaded and normalized by custom pipeline components.
2. The backbone/FPN produces image features.
3. `VADPerceptionTransformer` constructs a BEV representation using temporal self-attention, spatial cross-attention, CAN-bus shift/rotation information, and deformable attention.
4. `VADHead` decodes object queries, vectorized map queries, agent motion/future trajectories, and ego planning outputs.
5. Custom coders and dataset evaluation convert predictions to nuScenes/VAD result structures.

The model uses a temporal queue and `video_test_mode=True` in the supplied configs. Missing or malformed history/ego fields can therefore fail after a config has parsed successfully.

## Constructor and method facts

Source inspection confirms the following public class surfaces:

- `VAD.__init__(...)`, `VAD.forward(return_loss=True, **kwargs)`, `forward_train(...)`, `forward_test(...)`, and `forward_dummy(img)`.
- `VADHead.__init__(...)`, `forward(...)`, and `get_bboxes(preds_dicts, img_metas, rescale=False)`.
- `VADPerceptionTransformer.__init__(...)` and `forward(...)`; it is configured through nested `encoder`, `decoder`, and `map_decoder` dictionaries.
- `VADCustomNuScenesDataset` provides data preparation, vectorized map generation, formatting, and evaluation; its `format_results` accepts list-style outputs and can unwrap a `bbox_results` mapping.

Treat exact tensor shapes as config- and branch-dependent. Use the source/config contract rather than guessing when extending a head or pipeline.

## Import/build distinction

A safe `mmcv.Config.fromfile` check can parse VAD configs without building the model. Importing `mmdet3d.models`/`datasets` and building VAD also requires the version-matched native MMDetection3D operators and compatible CUDA compiler/runtime. If an import fails with a missing `*_ext` module such as `ball_query_ext`, repair the environment before debugging registry names or tensor shapes.
