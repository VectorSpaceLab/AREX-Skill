---
name: image-generation
description: "Guides OFA text-to-image generation, VQGAN code conversion, CLIP
  ranking, and image-generation validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# image-generation

Use this sub-skill when a user wants to run OFA text-to-image generation, inspect VQGAN code inputs, or reason about the image-generation evaluation stack.

## Trigger phrases

- "Generate images with OFA"
- "VQGAN code conversion"
- "How do I validate image-generation TSVs?"
- "What do the FID / IS helpers need?"
- "Why does image generation need CLIP and VQGAN checkpoints?"

## What this sub-skill owns

- text-to-image generation,
- code-token TSV layout and validation,
- VQGAN code extraction / code sequence handling,
- CLIP and generated-image scoring notes,
- FID / IS caveats and output layout.

## What it excludes

- caption / VQA / RefCOCO / OCR / ImageNet -> `vision-language-tasks`,
- generic diffusion or LoRA workflows outside OFA,
- pretraining -> `pretraining`,
- setup and launch mechanics -> `setup-and-command-building`.

## Read these files

- [references/workflows.md](references/workflows.md) for the generation flow and metric caveats.
- [references/troubleshooting.md](references/troubleshooting.md) for checkpoint, code-range, and metric issues.
- [scripts/validate_image_gen_tsv.py](scripts/validate_image_gen_tsv.py) to check code TSVs before GPU work.

## Typical workflow

1. Validate the image-generation TSV.
2. Confirm the VQGAN and CLIP checkpoints.
3. Choose whether you are generating codes or generating final images.
4. Only then launch the GPU workflow and compute metrics on a sufficiently large sample.

## Notes

- The code sequence is part of the data contract; a valid caption alone is not enough.
- FID and IS are not meaningful on tiny samples.
- A generation checkpoint usually depends on both the CLIP and VQGAN assets.
