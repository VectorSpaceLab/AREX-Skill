# Inference troubleshooting

This page focuses on the DreamOmni2 CLI workflows.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| The edit result follows the wrong image | The source/reference order is reversed | Put the source image first and the reference image second |
| The generation output ignores the intended composition | The instruction is too weak or the two reference images are not the ones you meant to use | Strengthen the instruction and confirm both inputs before rerunning |
| The saved image is missing | The `--output_path` directory does not exist or is not writable | Choose a writable path or create the parent directory first |
| The VLM prompt looks garbled | The output parser no longer matches the model's text wrapper | Inspect the raw VLM response and update `extract_vlm_text()` in `scripts/dreamomni2_common.py` if needed |
| The pipeline complains about model paths | The VLM or LoRA directories are missing or pointed at the wrong cache | Run `scripts/check_models.py` and correct the paths before launching |
| The run is out of memory | The VLM and FLUX stack are large for the current GPU | Use a larger GPU, lower the output size, or switch to a more memory-friendly model stack |
| `torch.cuda.is_available()` is false | The environment does not have the CUDA wheel or cannot see the GPU | Re-run `scripts/check_env.py` and fix the GPU/runtime setup before trying inference |
| The wrapper script cannot import the DreamOmni2 source modules | The repository checkout is not on the Python path | Run from an environment that can import the DreamOmni2 checkout or install the source tree before launching the wrappers |

## Recovery sequence

1. Confirm the CUDA environment with `scripts/check_env.py`.
2. Confirm the model paths with `scripts/check_models.py`.
3. Re-run the command with the source image first for editing workflows.
4. If the prompt text still looks wrong, inspect the raw VLM output before changing the diffusion call.
