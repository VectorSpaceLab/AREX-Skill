# Troubleshooting

## Common failure modes

### The TSV validator says the code length is wrong

- Check the image-code sequence length.
- Confirm the code tokens are integers separated by spaces.
- Re-run `scripts/validate_image_gen_tsv.py` after fixing the data.

### The generation command cannot find CLIP or VQGAN assets

- Confirm the checkpoint paths in the command.
- Make sure the CLIP and VQGAN files belong to the same generation setup.
- Do not launch the full job until all three assets are present.

### The generated-image metric looks meaningless

- FID and IS need many images.
- Use a small sample for smoke tests only.
- Keep the output directory and the evaluation statistics separate.

### The workflow fails on the first CUDA call

- Use the setup sub-skill to confirm the backend first.
- Check that the GPU build of PyTorch is visible.
- Do not treat a CPU import check as proof that image generation is ready.

## Recovery order

1. Validate the TSV.
2. Confirm the checkpoints.
3. Render the command.
4. Only then generate or score images.
