# Cross-Cutting Troubleshooting

Read this when a `generative-models` workflow fails before it is clearly owned by one sub-skill. For workflow-specific details, use the nearest sub-skill troubleshooting reference.

## Install And Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: sgm` | The package is not installed in the active Python environment. | Install the package, then run `python -c "import sgm; print(sgm.__version__)"`. |
| `ModuleNotFoundError` for `pytorch_lightning`, `omegaconf`, `open_clip`, `transformers`, `imwatermark`, or `cv2` | The repository metadata does not declare all runtime dependencies; the selected workflow needs optional packages. | Install the smallest dependency set for the chosen route. Run `python scripts/check_environment.py --json` to see which imports are missing. |
| `no module 'xformers'. Processing without...` | Optional memory-efficient attention package is absent. | This can be acceptable for inspection or CPU paths. For heavy sampling/training, install a PyTorch/CUDA-compatible `xformers` wheel only when the environment supports it. |
| `pip check` conflicts after installing broad requirements | Mixed PyTorch, Lightning, transformers, tokenizers, or CUDA package versions. | Rebuild a clean workflow-specific environment. Avoid installing all optional/UI/dev dependencies when only one route is needed. |

## Checkpoints And Model Weights

- API and config inspection helpers never load checkpoints; use them first when planning.
- Checkpoint-backed sampling expects exact filenames under the model path used by the workflow, such as SDXL API checkpoint names in `model_specs` or video-sampling names like `svd.safetensors`, `sv3d_u.safetensors`, `sv4d.safetensors`, and `sv4d2.safetensors`.
- Hugging Face model access may require license acceptance, authentication, or a manual download step. Do not assume network credentials are present.
- `missing keys` and `unexpected keys` during `load_state_dict` usually indicate a checkpoint/config mismatch or a model-version mismatch.

## CUDA, Precision, And Memory

- Many defaults use `device="cuda"` and half precision. CPU-only environments are fine for static inspection but not for practical generation.
- If CUDA is unavailable, avoid constructing checkpoint-backed pipelines unless the workflow explicitly supports CPU and the user accepts slow execution.
- For video sampling memory issues, use the `video-sampling` sub-skill and reduce `decoding_t`, `encoding_t`, `img_size`, or `num_steps` before trying broader environment changes.
- If a CUDA extension package fails to install, verify PyTorch version, CUDA wheel tag, driver support, GPU architecture, and whether a CPU fallback is acceptable.

## Config And Data Failures

- `KeyError: Expected key target to instantiate.` means an OmegaConf node intended for `instantiate_from_config` is missing `target`.
- Import errors from target strings usually mean a typo, a moved class path, or a missing optional dependency.
- Training configs with `USER`, `CKPT_PATH`, or placeholder data paths require user-specific edits before any run.
- Use `sub-skills/training-and-configs/scripts/inspect_training_config.py` for safe config validation before launching `main.py`.

## UI And Demo Failures

- Streamlit or Gradio demos may require optional UI packages, checkpoint files, CUDA, and an available server port.
- For automation, translate demo controls into `inference-api` or `video-sampling` workflows instead of launching a UI server.
- Watermark detection depends on image size and post-processing; bit-match counts are probabilistic evidence, not proof of provenance.

## When To Stop And Ask

Ask the user before downloading large checkpoints, accepting model licenses, starting UI servers, launching training/sampling jobs, mutating an existing environment, or using credentials/networked services.
