---
name: modeling-inference
description: "Choose and wire MONAI networks, losses, metrics, inferers,
  postprocessing, visualization, and export-oriented model utilities for
  inference and evaluation primitives."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MONAI Modeling and Inference

Use this sub-skill when a task needs MONAI model primitives: network selection, tensor shape conventions, segmentation losses, validation metrics, sliding-window inference, postprocessing, visualization, or model export caveats.

## Route Here For

- Building channel-first MONAI networks from `monai.networks`, especially segmentation architectures such as `UNet` and transformer-style variants such as `SwinUNETR`.
- Choosing loss functions from `monai.losses`, including activation and one-hot handling for binary, multi-class, and multi-label segmentation.
- Computing metrics from `monai.metrics`, especially Dice and surface-distance style metrics that expect postprocessed predictions and reset/aggregate discipline.
- Running inference with `monai.inferers.sliding_window_inference` or `SlidingWindowInferer` for volumes too large for one forward pass.
- Adding prediction postprocessing with dictionary transforms such as `Activationsd` and `AsDiscreted`.
- Understanding visualization helpers and export-oriented caveats without relying on optional export packages being installed.

## Route Elsewhere

- Use `../data-transforms/SKILL.md` for data loading, preprocessing, metadata, `MetaTensor`, caching, decollation, and inverse transforms.
- Use `../training-evaluation/SKILL.md` for Ignite trainer/evaluator loops, handlers, checkpointing, AMP, and experiment logging.
- Use `../bundle-config/SKILL.md` for MONAI Bundle configuration, Bundle CLI run/verify/export commands, and packaged bundle workflows.
- Use `../apps-auto3dseg/SKILL.md` for Auto3DSeg and high-level application orchestration.

## Required References

- Read `references/workflows.md` when choosing a network/loss/metric/inferer recipe or wiring postprocessing, visualization, and export-aware inference flow.
- Read `references/api-reference.md` when you need concise signatures, tensor shape contracts, or API-specific usage notes for core modeling primitives.
- Read `references/troubleshooting.md` when debugging channel/shape mismatches, activation or one-hot mistakes, metric lifecycle issues, sliding-window OOM/artifacts, optional export dependencies, or CPU/CUDA limitations.
- Run `scripts/modeling_smoke.py --help` to inspect the bundled validation script; run `scripts/modeling_smoke.py` to perform a tiny CPU-only smoke check of MONAI network, loss/metric, and sliding-window primitives.

## Quick Defaults

- Assume tensors are channel-first: image/logits shape is usually `(batch, channels, spatial...)`; 3D segmentation commonly uses `(B, C, H, W, D)`.
- For multi-class segmentation logits, start with `DiceCELoss(to_onehot_y=True, softmax=True)` during training and postprocess validation logits with `Activationsd(softmax=True)` followed by `AsDiscreted(argmax=True, to_onehot=num_classes)`.
- For binary segmentation logits, start with `DiceLoss(sigmoid=True)` or `DiceCELoss(sigmoid=True)` and postprocess with sigmoid plus thresholding.
- For sliding-window inference, keep the predictor in eval mode, choose `roi_size` in spatial dimensions only, reduce `sw_batch_size` before reducing ROI, and use `device="cpu"`/`sw_device="cuda"` only when you intentionally want stitched output on CPU.
- For metrics, pass postprocessed predictions and labels with compatible one-hot/channel layout, call the metric per batch, then `aggregate()` and `reset()` for each validation epoch.
