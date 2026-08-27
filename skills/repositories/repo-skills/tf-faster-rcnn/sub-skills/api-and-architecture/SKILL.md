---
name: api-and-architecture
description: "Inspect and modify tf-faster-rcnn model, backbone, RPN/proposal,
  bbox/blob, and roidb APIs from source without running training or inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# tf-faster-rcnn API and architecture

Use this sub-skill when a Researcher needs to inspect or modify the repository internals around `Network.create_architecture`, VGG/ResNet/MobileNet backbones, RPN/proposal layers, bbox transforms, image blob preprocessing, roidb/minibatch structure, or safe extension points for anchors and new backbones.

Do **not** use this sub-skill as proof that a TensorFlow graph, demo, training job, or evaluation job runs on the current host. Full graph execution depends on the legacy TensorFlow 1.x, Cython/CUDA/NMS, checkpoint, and dataset setup; route that work to `installation-and-configuration`, `inference-and-demo`, or `training-and-evaluation`.

## Verified source facts to preserve

The production inspection environment verified these source-level facts with CPU/static checks and a TensorFlow 1.15 CPU inspection substitute:

- Backbone constructors: `vgg16()`, `resnetv1(num_layers=50)`, and `mobilenetv1()`.
- All three backbones inherit `Network.create_architecture(mode, num_classes, tag=None, anchor_scales=(8,16,32), anchor_ratios=(0.5,1,2))`.
- `cfg.USE_GPU_NMS` defaults to `True`, `cfg.TEST.MODE` defaults to `nms`, and default anchor scales/ratios are `[8,16,32]` and `[0.5,1,2]`.
- Default scale/ratio anchor generation yields `(9, 4)` anchors.
- Source-level utility/dataset checks passed, but full CUDA native build, demo, train, test, and benchmark AP were **not** verified.

## Operating procedure

1. Start from a source checkout and run the bundled source inspector without importing repo modules:

   ```bash
   python scripts/inspect_source_api.py --repo-root <repo-root> --format text
   ```

   Use `--strict` when you need the script to fail on missing required files or signature drift.

2. Read [API reference](references/api-reference.md) for signatures, shapes, and utility contracts.
3. Read [architecture notes](references/architecture-notes.md) before changing graph flow, anchors, RPN/proposal behavior, or a backbone.
4. Read [troubleshooting](references/troubleshooting.md) when signatures match but graph construction, roidb minibatches, NMS imports, or bbox shapes fail.
5. If the task requires installation, native extension build, TensorFlow session execution, demo commands, training commands, datasets, or checkpoints, stop and route to the appropriate sibling sub-skill.

## Common modification patterns

### Change anchor scales or ratios

- Prefer passing `anchor_scales` and `anchor_ratios` to `create_architecture` instead of hard-coding values in lower layers.
- The values are stored on the `Network` instance, consumed by `_anchor_component`, passed to `generate_anchors_pre`, and determine `self._num_anchors`.
- `self._num_anchors` controls RPN classification channels (`A * 2`), bbox channels (`A * 4`), anchor target shapes, proposal layer slicing, and proposal target contracts.
- After changing anchors, run the source inspector and check every RPN/proposal shape path in [architecture notes](references/architecture-notes.md).

### Add or adapt a backbone

A compatible backbone subclass should:

- Inherit `Network` and call `Network.__init__(self)`.
- Set `_feat_stride`, `_feat_compress`, and `_scope` in `__init__`.
- Implement `_image_to_head(self, is_training, reuse=None)` and store `self._layers['head']`.
- Implement `_head_to_tail(self, pool5, is_training, reuse=None)` and return the feature vector used by region classification.
- Implement `get_variables_to_restore(self, variables, var_keep_dic)` and `fix_variables(self, sess, pretrained_model)` if ImageNet/pretrained weights need RGB/BGR or FC/conv conversion.
- Wire the new class into CLI/model-selection code only after architecture inspection; command workflows belong to `inference-and-demo` or `training-and-evaluation`.

### Inspect roidb and minibatch inputs

- `RoIDataLayer.forward()` returns blobs from `get_minibatch`: `data`, `gt_boxes`, and `im_info`.
- `data` is an NHWC float32 blob with pixel means subtracted; the repo assumes a single-image minibatch for core train/test paths.
- `gt_boxes` is shaped `(N, 5)` with `(x1, y1, x2, y2, class)` after image scaling.
- `im_info` is `[height, width, scale]` for the prepared blob.

## Boundaries and omissions

- This sub-skill intentionally performs AST/source inspection only. It does not import `tensorflow`, build Cython/CUDA extensions, download checkpoints, open datasets, or run demo/train/test code.
- Full backend setup and `gpu_nms`/`cpu_nms` build issues belong to `installation-and-configuration`.
- User-facing demo/inference command construction belongs to `inference-and-demo`.
- Train/test/reval command construction and benchmark caveats belong to `training-and-evaluation`.
