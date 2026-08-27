# Inference and Demo Troubleshooting

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Blank output or nonsense output | Reference or target mask is empty, non-binary, or misaligned. | Run the input validator first. |
| The crop misses the object | Mask bounding box is too loose or the object is too small. | Repair the mask and confirm the crop assumptions. |
| The demo’s refinement toggle fails | Optional `iseg` weight is missing. | Disable the toggle or provide the weight. |
| The demo launches but does not behave as expected | Coarse masks or the source demo bug around the interactive toggle. | Document the caveat and keep the toggle optional. |
| Cog fetches a model during launch | Cache is empty and network access is required. | Note the network dependency or pre-cache the model. |
| Inference fails on a missing checkpoint | Config placeholders were never patched. | Return to setup and checkpoints. |

## Recovery checklist

1. Validate the masks.
2. Confirm the checkpoint paths.
3. Confirm the repo root and Python imports.
4. Check the generation settings only after the data and paths look right.

## Notes

- Generation problems are usually data-shape problems, not prompt problems.
- A successful import check does not mean the demo will launch successfully.
- The source repo uses a 512x512 generation canvas and a 224x224 reference
  conditioning size.
