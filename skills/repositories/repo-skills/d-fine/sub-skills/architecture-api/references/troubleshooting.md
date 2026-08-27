# Architecture/API Troubleshooting

## `ValueError: The module ... is not registered`

Likely causes:

- YAML `type` or top-level component name is misspelled or has the wrong capitalization.
- The Python module defining the class was not imported for registration side effects.
- A custom class lacks `@register()`.

Recovery:

1. Confirm the YAML name exactly matches the Python class name or explicit registration name.
2. Confirm the module containing the class is imported before `YAMLConfig(...).model` or `create(...)` is called.
3. If adding a new component, decorate it with `@register()` and update the nearest package initializer or import path.
4. Run `python ../scripts/inspect_dfine_model.py --repo-root <d-fine-checkout> --config <config.yml> --build-model`.

## `Missing inject config` or invalid `type` style

Likely causes:

- A class has `__inject__ = ['field']`, but the YAML field is `null`, absent, or names a missing top-level block.
- An inline injected dictionary lacks `type`.
- A top-level block was renamed without updating the parent config.

Recovery:

- In the parent component block, ensure every injected field points to a registered config block or a dictionary with `type`.
- For `DFINE`, ensure `backbone`, `encoder`, and `decoder` point to `HGNetv2`, `HybridEncoder`, and `DFINETransformer` or compatible replacements.
- For `DFINECriterion`, ensure the `matcher` block has `type: HungarianMatcher` or a compatible registered matcher.

## HGNetv2 pretrained lookup fails

Symptoms include missing files under `weight/hgnetv2/`, network download failures, or hangs during inspection.

Recovery:

- For inspection/export smoke, set `HGNetv2.pretrained: False` before constructing `cfg.model`.
- Use `scripts/inspect_dfine_model.py` without `--allow-pretrained`; it disables HGNetv2 pretrained lookup by default.
- Only enable pretrained lookup when the user explicitly wants to test backbone pretraining and has the needed files/network.

## Channel or stride mismatch between backbone, encoder, and decoder

Symptoms include tensor shape errors during model construction or forward pass.

Likely causes:

- `HGNetv2.return_idx` changed without updating `HybridEncoder.in_channels` and `feat_strides`.
- `HybridEncoder.hidden_dim` changed without updating `DFINETransformer.feat_channels`.
- `DFINETransformer.num_levels` or `num_points` does not match supplied feature levels.

Recovery:

1. Compare the selected model-size config against the closest working stock config.
2. Keep `feat_strides`, `feat_channels`, and `num_levels` aligned across encoder and decoder.
3. Build the model first; run dummy forward only after construction succeeds.

## Checkpoint shape mismatch

Symptoms include missing/unexpected keys or size mismatch for decoder score heads, denoising embeddings, or distribution heads.

Likely causes:

- `num_classes` changed.
- Dataset family changed from Objects365 to COCO/custom.
- Architecture knobs such as hidden dim, layers, `reg_max`, or feature levels changed.

Recovery:

- For training fine-tuning, use `--tuning` so solver tuning logic can adjust compatible head parameters when possible.
- Do not combine `--resume` and `--tuning`.
- For export/inference, make sure the config matches the checkpoint that produced the weights; use the EMA extractor only to simplify key layout, not to change model shapes.

## Deploy-mode confusion

Symptoms include export/inference code producing different module state than training or missing postprocessor behavior.

Facts:

- Native export/inference wrappers load train-mode weights, then call `cfg.model.deploy()` and `cfg.postprocessor.deploy()`.
- Deploy mode sets eval state and lets modules with `convert_to_deploy()` fold or convert internal blocks.

Recovery:

- Load checkpoint weights into `cfg.model` before wrapping deploy model/postprocessor.
- Do not train after calling deploy on the same module instance.
- Route command construction to `inference-export` when the task is about ONNX/TensorRT/OpenVINO execution.
