# Training workflows

## Single-concept training

1. Validate the concept inputs and prior-preservation layout first.
2. Decide whether you want only K/V updates or full cross-attention updates.
3. Choose whether to train the text encoder, add modifier tokens, or do both.
4. Set the output directory and launch the diffusers training entry point through `accelerate`.
5. Expect a `delta.bin` output in the training directory.

## Multi-concept training

1. Put the concept objects into a JSON manifest.
2. Make sure the manifest has one object per concept and one prompt pair per concept.
3. Validate the manifest with `scripts/validate_training_inputs.py`.
4. Launch the training entry point with the manifest instead of the single-concept flags.

## Prior-preservation choices

- **Generated prior**: the route synthesizes class images locally when the class directory is short.
- **Real prior**: the route rewrites the class fields to the bundle layout produced by the data-preparation route.

## SDXL route

The SDXL branch uses two tokenizers and two text encoders, a larger default resolution, and SDXL-specific crop-coordinate ids. Use it when the base model is SDXL or when you need the XL checkpoint shape.

## After training

- Sample the output with the inference route.
- Use the checkpoint-tools route if you want to compress or compose the delta.
- If you plan to publish, check the Hub settings before enabling `--push_to_hub`.
