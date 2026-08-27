---
name: cli-and-api
description: "Use gpt-image-cli from the command line or OpenAI Python SDK for
  GPT Image 2 generation, reference-image editing, inpainting, output control,
  and safe no-API preflight."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# cli-and-api

Use this sub-skill when a task requires the `gpt-image` CLI or equivalent OpenAI Python SDK calls for GPT Image 2:

- text-to-image generation;
- single-reference or multi-reference image edits;
- mask-based inpainting;
- output file naming, image count, format, compression, size, quality, moderation, or background parameters;
- safe command preflight before a real OpenAI Images API call.

Do **not** use this sub-skill for prompt-style or gallery selection; route that to [`../prompt-gallery/SKILL.md`](../prompt-gallery/SKILL.md). Do **not** use it for repository contribution, gallery metadata, plugin packaging, or release edits; route that to [`../repo-maintenance/SKILL.md`](../repo-maintenance/SKILL.md).

## Safety boundary

The CLI and SDK paths call the OpenAI Images API when executed. Real calls require `OPENAI_API_KEY`, network access, and may incur cost. Never run a real generation/edit request unless the user has explicitly asked to execute it in the current session and accepts the credential/cost boundary. For planning, diagnostics, and command assembly, use the bundled helper in no-execute mode.

The CLI loads credentials in this order without overriding an existing process environment variable: process environment, then `./.env`, then `~/.env`. Never print, write, or transform API-key values.

## Operating loop

1. **Classify endpoint**:
   - no `-i/--image` inputs -> text-to-image via `client.images.generate`;
   - one or more `-i/--image` inputs -> edit via `client.images.edit`;
   - `-m/--mask` requires at least one `-i/--image` and uses the edit endpoint.
2. **Preflight before execution**:
   - verify `gpt-image` or `python -m gpt_image_cli.cli` is available;
   - verify reference image and mask paths exist;
   - check whether an API key is available without exposing it;
   - select output path, size, quality, count, and format.
3. **Build command** with explicit flags, keeping `--quality` as the cost/fidelity knob.
4. **Execute only on explicit user approval**. Surface stderr and exit code on failure; do not retry expensive calls blindly.
5. **Report output paths** printed by the CLI, plus the key flags used.

## Fast examples

```bash
# Safe diagnostics only; does not call OpenAI.
python scripts/gpt_image_cli_helper.py preflight

# Build a generation command without executing it.
python scripts/gpt_image_cli_helper.py build-command \
  -p "a photorealistic convenience store at 10pm" \
  --size 1k --quality low -f drafts/store.png

# Real text-to-image call; run only after user approval and key/cost confirmation.
gpt-image -p "a photorealistic convenience store at 10pm" \
  --size 1k --quality high -f store.png

# Real single-reference edit.
gpt-image -p "Make it a winter evening with heavy snowfall; keep the chessboard layout." \
  -i chess.png --quality high -f chess-winter.png

# Real multi-reference edit.
gpt-image -p "Use Image 1 as the person and Image 2 as the product; match lighting and keep identity." \
  -i person.png -i product.png --size portrait --quality medium -f campaign.png

# Real mask inpaint; opaque mask areas are preserved and transparent areas regenerate.
gpt-image -p "replace the sky with aurora" \
  -i photo.png -m sky_mask.png -f aurora.png
```

## References

- [`references/cli-reference.md`](references/cli-reference.md): complete CLI flags, defaults, endpoint routing, output naming, examples, exit codes.
- [`references/api-reference.md`](references/api-reference.md): OpenAI SDK mapping, verified constants/functions, size shortcuts, output behavior.
- [`references/troubleshooting.md`](references/troubleshooting.md): missing keys, missing CLI/import backend, file validation, `input_fidelity`, output-format mistakes, API errors/refusals.

## Bundled helper

Use [`scripts/gpt_image_cli_helper.py`](scripts/gpt_image_cli_helper.py) for deterministic no-network preflight and command construction. It does not call the API by default. The helper only delegates to `gpt-image` when `build-command --execute` is passed explicitly.
