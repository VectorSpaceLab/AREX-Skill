# Checkpoint Conversion, Publishing, FLOPs, and Deployment Caveats

Read this when a task involves adapting pretrained weights, validating model-complexity numbers, publishing checkpoints, or deciding whether a customized model can be deployed.

## Conversion Decision Process

Checkpoint conversion is safe only when the source checkpoint schema and target MMSegmentation module names are known.

Use this process:

1. Identify the source family: BEiT, CLIP/SAN, MiT/SegFormer, STDC, Swin, Twins, ViT, JAX ViT, or another model.
2. Confirm the source checkpoint container: plain state dict, `state_dict`, `model`, a remote URL handled by MMEngine, or a custom nested object.
3. Build the target config and inspect `model.state_dict().keys()`.
4. Compare tensor shapes for patch embeddings, classifier/decode heads, positional embeddings, normalization layers, and QKV projections.
5. Convert into a new destination file and load it with strict diagnostics. Never overwrite the source checkpoint.
6. If class count, head shape, patch size, image resolution, or architecture differs, expect partial loading or manual adaptation.

Treat converter logic as model-family-specific evidence, not as a generic guarantee. This skill does not bundle full converter scripts because each converter is checkpoint-specific, can require large source weights, and must be validated against the target config.

## Converter Family Map

Use these family-specific expectations when planning a converter or reviewing an existing conversion utility:

- **BEiT**: maps patch embedding, transformer blocks, layer norms, and FFN names to MMSegmentation style.
- **CLIP/SAN**: maps CLIP visual/text transformer names and side-adapter network keys for open-vocabulary segmentation models.
- **MiT/SegFormer**: maps patch embeddings, transformer layers, Q/K/V concatenation, FFN conv reshaping, and norms.
- **STDC**: maps official STDC1/STDC2 feature and stage names.
- **Swin**: maps stages, attention, FFN, patch embedding, and downsample unfold ordering.
- **Twins**: maps PCPVT/SVT patch embeddings, blocks, attention Q/K/V, FFN, and positional blocks.
- **ViT and JAX ViT**: maps patch embeddings, transformer blocks, QKV, attention output, FFN, norms, and in JAX cases converts numpy tensors into PyTorch-style keys.

Before using or writing any converter, inspect its argument parser or function contract in the current project where it lives. Do not assume all converters use the same positional arguments; some require family-specific choices such as model kind or STDC variant.

## Conversion Risk Checklist

Before telling a user conversion should work, check:

- The target config uses the same backbone/head family the converter expects.
- The source checkpoint contains the fields the converter reads.
- Source image patch size, embedding width, layer count, and attention heads match the target config.
- Target decode-head class count and output channels match the downstream dataset; otherwise head weights may be intentionally skipped or randomly initialized.
- Positional embeddings may need interpolation when resolution or patch grid differs; not every converter handles this.
- Optional dependencies for the target model are installed, such as detection or open-vocabulary components for some heads/projects.
- CPU/GPU availability does not affect key conversion, but it can affect later loading or operator checks.

When in doubt, convert only the backbone, load non-strictly, and report missing/unexpected keys explicitly.

## Publishing a Checkpoint

Publishing is a separate validation step after training and conversion. A safe publish process should:

1. Load the checkpoint on CPU.
2. Remove optimizer/training-state entries only after confirming they are not needed for resume.
3. Save a new checkpoint file rather than editing the source artifact.
4. Compute a content hash and include a short hash in the filename.
5. Keep the matching config, dataset/classes, and validation metrics alongside the checkpoint.

Publishing does not verify model accuracy and does not automatically sanitize arbitrary metadata. Inspect metadata before public release when checkpoints may contain private paths, dataset names, or experiment notes.

## FLOPs and Parameter Checks

A model-complexity check normally builds `cfg.model`, creates a random input tensor from a requested shape, applies the data preprocessor, removes auxiliary heads if the comparison requires it, reverts SyncBN for analysis, and calls MMEngine complexity utilities.

Important caveats:

- MaskFormer and Mask2Former style heads are commonly unsupported by simple FLOPs helpers.
- Unsupported ops or custom operators may be omitted or miscounted by the complexity backend.
- Random-input model complexity is not end-to-end inference throughput.
- Input shape may be interpreted as square for one integer and `(height, width)` for two integers.
- `size_divisor` or preprocessing can change padded shape; report the padded shape as well as the requested shape.
- Optional project modules must be importable and registered before model build.

Use FLOPs as a comparative smoke check, not as a definitive deployment benchmark or paper claim.

## Deployment Caveats

Model customization can break deployment even when training works:

- Custom Python modules must be importable in the deployment environment.
- MMCV custom ops must be installed for operators used by the selected model/head.
- MaskFormer/Mask2Former and open-vocabulary models may need optional dependencies and export support beyond base MMSegmentation.
- Dynamic control flow, custom tensor shapes, text encoders, or unsupported interpolation/attention operators can block export.
- Sliding-window inference and post-processing can dominate runtime but may not appear in model-only complexity checks.
- `align_corners`, crop size, and whole/slide inference mode must match the trained config to avoid quality regressions.

For deployment runtime commands, route to the inference sub-skill instead of treating deployment as only a model-customization concern.
