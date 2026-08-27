# Inference Workflow Troubleshooting

## Import or setup fails before request construction

Use the root environment checker first. Most workflow helpers import
`ai_diffusion`, Qt classes, and the bundled websockets package.

```bash
QT_QPA_PLATFORM=offscreen python scripts/check_krita_ai_diffusion_environment.py --strict
```

If it reports missing websockets, fix packaging/submodule state before debugging
workflow code.

## Serialization fails or image payload is too large

Symptoms:

- `WorkflowInput.to_dict()` raises while serializing image data.
- A client rejects payloads because images are too large.
- Round-trip loses enum/dataclass types.

Recovery:

- Use `image_format=None` for structure-only inspection.
- Use `max_image_size` to catch oversized payloads intentionally.
- Confirm image fields are `ai_diffusion.image.Image`, not PIL/NumPy objects.
- Round-trip with `WorkflowInput.from_dict()` and compare key fields.

## Wrong `WorkflowKind`

Likely causes:

- `strength < 1.0` triggers refine/image-to-image behavior.
- Active selection/mask triggers inpaint.
- Upscale workspace settings choose simple or diffusion-tiled upscale.
- Graph workspace sets custom mode.
- Region-only settings route to region refine.

Recovery:

1. Print or inspect `WorkflowInput.kind` and `images` fields with the bundled
   helper.
2. If the source is `DocumentModel.generate()`, inspect workspace state in
   `ui-workspaces`: `workspace`, `strength`, `region_only`, selection, active
   layer, `upscale.use_diffusion`, and custom mode.
3. Do not force a kind manually unless the required fields for that kind are
   present.

## Inpaint mask missing or wrong extent

Symptoms:

- Inpaint request has no `images.hires_mask`.
- Mask size does not match `images.initial_image`.
- Selection appears offset or cropped incorrectly.

Recovery:

- Confirm the active Krita selection or region mask was collected before
  request construction.
- Compare `ExtentInput.input`, `initial`, `desired`, and `target`.
- Check `InpaintParams.target_bounds`, `grow`, `feather`, and `blend`.
- For layer/selection extraction issues, route to `document-image-state`.

## Model, LoRA, or control resource not found

Symptoms:

- `Style checkpoint ... not found`.
- Unsupported quantized format error.
- LoRA does not appear in `CheckpointInput.loras`.
- Control mode fails during graph lowering.

Recovery:

- Check `ClientModels.checkpoints`, LoRA list, and architecture compatibility.
- Run the server resource lister and inspect required custom nodes.
- Verify LoRA tags were extracted from prompt text and that style LoRAs were
  added to the checkpoint input.
- Some architectures support fewer features: CFG, clip skip, LCM, attention
  guidance, regions, and edit/reference behavior vary by `Arch`.

## Prompt output is surprising

Symptoms:

- Comments remain in prompt.
- Wildcards choose unexpected options.
- Negative prompt disappears in live preview.
- `<layer:name>` tokens become `image N` references with unexpected numbering.

Recovery:

- Use `inspect_prompt_style.py` for comments, style merge, LoRA, wildcards, and
  metadata.
- Remember CFG/liveness can affect negative prompt behavior; live CFG of `1.0`
  can produce an empty final negative prompt.
- Layer-token numbering depends on implicit canvas/edit references and unique
  layer collection order; use `document-image-state` for layer mapping.

## Tiled upscale cost is unexpectedly high

`WorkflowInput.passes_count` for `upscale_tiled` is twice the number of tiles:

```text
2 * max(1, ceil(target.width / desired.width) * ceil(target.height / desired.height))
```

Reduce target size, desired tile size, batch count, or overlap as appropriate,
and warn the user before launching expensive generation.
