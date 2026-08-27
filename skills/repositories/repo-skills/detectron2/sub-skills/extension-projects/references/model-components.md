# Model Components

This reference summarizes the Detectron2 model-extension surfaces most often needed by coding agents. It focuses on extension seams; use the training, data, inference, and deployment sub-skills for full workflow execution.

## Builders

- `build_model(cfg)` reads `cfg.MODEL.META_ARCHITECTURE`, resolves the class in `META_ARCH_REGISTRY`, calls it with `cfg`, moves the result to `cfg.MODEL.DEVICE`, and returns a `torch.nn.Module` with random parameters unless weights are loaded separately.
- `build_backbone(cfg, input_shape=None)` reads `cfg.MODEL.BACKBONE.NAME`; when `input_shape` is omitted it creates a `ShapeSpec` whose channel count matches `cfg.MODEL.PIXEL_MEAN`.
- `build_roi_heads(cfg, input_shape)` reads `cfg.MODEL.ROI_HEADS.NAME` and calls the registered ROI heads implementation with `(cfg, input_shape)`.
- `build_proposal_generator(cfg, input_shape)`, `build_box_head`, `build_mask_head`, `build_keypoint_head`, and semantic-head builders follow the same pattern: config name to registry lookup to callable construction.

Builders only construct modules. They do not register custom classes, load project config keys, register datasets, load checkpoints, or train.

## Backbone Contract

A custom backbone registered in `BACKBONE_REGISTRY` should normally subclass `detectron2.modeling.Backbone` and implement:

- `forward(images)`: returns a dictionary from feature name to feature tensor.
- `output_shape()`: returns a dictionary from feature name to `ShapeSpec`.

The feature names in `output_shape()` must match downstream config keys such as `MODEL.ROI_HEADS.IN_FEATURES`, `MODEL.RPN.IN_FEATURES`, `MODEL.ROI_MASK_HEAD.IN_FEATURES`, or project-specific feature lists. Shape mismatches often surface later in ROI pooling, RPN, FPN, mask heads, or semantic heads rather than at registration time.

A useful custom-backbone debugging sequence:

1. Import the module that registers the backbone.
2. Confirm `BACKBONE_REGISTRY.get("YourBackboneName")` resolves.
3. Check `cfg.MODEL.BACKBONE.NAME` exactly matches the registered name.
4. Build only the backbone with `build_backbone(cfg)` before building the full model.
5. Inspect `backbone.output_shape()` and align every consumer's `IN_FEATURES` with the returned keys.

## ROI Heads Contract

A custom ROI heads class registered in `ROI_HEADS_REGISTRY` is called as `YourROIHeads(cfg, input_shape)`. Built-in `ROIHeads` variants typically use `@configurable` and `from_config` so they can be called either from config or with explicit arguments.

Use a custom ROI heads class when you change per-proposal logic, add a new task head, replace predictors, or need a config-selectable ROI behavior. If you only need a custom box/mask/keypoint head, registering a lower-level head may be simpler than replacing all ROI heads.

Keep these aligned:

- `cfg.MODEL.ROI_HEADS.NAME` for the ROI heads class.
- `cfg.MODEL.ROI_HEADS.IN_FEATURES` for feature maps consumed by the ROI heads.
- `cfg.MODEL.ROI_BOX_HEAD.NAME`, `cfg.MODEL.ROI_MASK_HEAD.NAME`, and related lower-level names when replacing individual heads.
- Dataset annotations and mapper outputs required by any new task fields.

## Meta-Architecture Contract

A meta-architecture registered in `META_ARCH_REGISTRY` receives `cfg` and returns a full `torch.nn.Module`. Use this for a full model family or when the input/output contract differs substantially from the built-in generalized R-CNN, semantic segmentor, panoptic FPN, RetinaNet, or project models.

A meta-architecture must handle the standard model mode contract if it should interoperate with existing trainers and evaluators:

- In training mode, return a dictionary of scalar losses.
- In evaluation mode, return a list of per-image dictionaries, or the task-specific structure expected by evaluators.
- If it consumes standard data loaders, accept `list[dict]` with image tensors and optional `instances`, `sem_seg`, `proposals`, `height`, and `width` keys.

## Explicit Construction

Use explicit construction when the config system is too restrictive. For example, a Faster R-CNN variant with a custom box predictor can instantiate `StandardROIHeads` with an explicit `box_predictor` argument while reusing config-derived defaults for other arguments.

Pattern:

```python
roi_heads = StandardROIHeads(
    cfg,
    backbone.output_shape(),
    box_predictor=MyRCNNOutputLayers(...),
)
```

If the customized component should later be selectable from a config, wrap that explicit construction in a registered class or configurable class.

## Partial Execution

When a task asks for intermediate features or custom instrumentation, it is often better to partially execute a built model than to rewrite the full model. Typical sequence:

1. Build the model.
2. Put it in eval mode if doing inference-style probing.
3. Convert input tensors to the same shape/normalization assumptions expected by the model.
4. Call `model.backbone`, `model.proposal_generator`, or `model.roi_heads` directly with the intermediate structures those components expect.

Partial execution requires matching feature names, `ImageList` padding/size conventions, proposal `Instances`, and mode-specific behavior. It is an extension/debugging tactic, not a stable public API for all internals.

## Trainer Integration

A new model component often requires trainer changes:

- Override `build_train_loader` when mapper outputs must include new fields.
- Override `build_evaluator` when the task produces non-standard outputs.
- Override `build_optimizer` or scheduler creation when project code uses custom learning-rate policies.
- Override hooks when the extension needs extra periodic evaluation, checkpointing, or test-time augmentation.

Do not diagnose a model-build failure in isolation if the extension also changed dataset fields, metadata, evaluator tasks, or post-processing expectations.
