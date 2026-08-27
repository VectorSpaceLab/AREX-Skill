# Document, Image, Prompt, and Persistence Troubleshooting

## Selection or mask appears offset

Recovery:

- Compare canvas `Extent`, selection `Bounds`, crop/context bounds, and mask
  extent.
- Ensure mask coordinates are converted relative to crop/context bounds.
- Confirm `Mask.to_image()` extent matches the image payload extent.
- Check padding/grow/feather/blend values in inpaint params.

## Generated result applied to wrong layer

Likely causes:

- Apply behavior setting changed.
- Active layer changed during async generation.
- Region output behavior created a group or transparency mask.
- Layer IDs were stale after document reload.

Recovery:

- Inspect `ApplyBehavior` and `ApplyRegionBehavior`.
- Use layer IDs rather than display names when possible.
- Restore active layer state around operations that temporarily switch layers.
- For region workflows, inspect region link type and target layer/group.

## Prompt comments, LoRAs, or wildcards behave unexpectedly

Use:

```bash
python sub-skills/document-image-state/scripts/inspect_prompt_style.py --prompt "cat <lora:fur:0.6> # note" --style-prompt "cinematic {prompt}" --lora-id fur --metadata
```

Check output fields in this order:

1. `comment_stripped`
2. `merged_with_style`
3. `after_lora_extraction`
4. `loras`
5. `wildcards_evaluated`
6. `after_layer_replacement`
7. `metadata_preview`

## LoRA tag not found

Likely causes:

- Name in prompt does not match any known file or alias.
- Weight omitted and no default metadata exists.
- Style LoRA exists but checkpoint architecture/server does not support it.
- Server did not discover the LoRA file.

Recovery:

- Provide available LoRA IDs to the prompt inspector.
- Check `FileLibrary` metadata for `lora_strength` and trigger words.
- Route to `server-resources` to inspect discovered LoRAs.

## Layer token replacement wrong

Symptoms: `<layer:name>` becomes the wrong `image N` reference or remains in the
prompt.

Recovery:

- Confirm the layer exists and names are unique enough.
- Check whether edit mode implicitly adds the canvas/reference image first; this
  can shift numbering.
- Check duplicate layer-token handling; repeated references should reuse the
  same image index rather than adding duplicates.
- Inspect collected control/reference images in the final `ConditioningInput`.

## Image format unsupported or WebP unavailable

`ImageFileFormat.from_extension` supports `.png`, `.webp`, `.jpg`, and `.jpeg`.
Qt WebP support can vary. If WebP fails, use the format fallback policy or save
PNG/JPEG according to user needs.

## Persisted setting falls back to default

Likely causes:

- Invalid enum string in settings JSON.
- Missing style/workflow file referenced by persisted ID.
- Property is transient and was never meant to persist.
- Document-specific state differs from global settings.

Recovery:

- Validate enum names against current enum members.
- Check style/workflow collection after reload.
- Separate document persistence bugs from global settings bugs.
