# Workflows

## Main generation flow

1. Prepare the COCO image-generation TSV with the correct selected columns.
2. Confirm the image-generation checkpoint and the paired CLIP/VQGAN assets.
3. Render or inspect the command before launching the GPU job.
4. Keep enough generated images if you plan to compute FID or IS.

## Key command facts

- The repo's evaluation script uses selected columns `0,2,1`.
- The generation task uses a long target length and a code constraint range.
- The evaluation stack writes images to a generation directory and then scores them.

## VQGAN code conversion

- The code-conversion path expects integer tokens, a VQGAN config, and a VQGAN checkpoint.
- Use the TSV validator before trying to run code extraction.
- If the TSV row contains a raw caption but no code sequence, it is not ready for the image-generation workflow.

## Metric caveats

- FID and IS need many images to be meaningful.
- A tiny sample is useful for a smoke test but not for a reported score.
- Keep the generated-image directory separate from the input TSVs.
