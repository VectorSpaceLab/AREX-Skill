---
name: image-to-video
description: "Route I2VGen-XL image-to-video inference, local predictor/demo
  references, input lists, checkpoints, person variant overrides, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# image-to-video

Use this sub-skill when the task is about VGen's I2VGen-XL image-to-video path: one input image plus one text caption produces a short video. This includes local config-driven inference, the `image|||caption` list format, I2VGen-XL checkpoint selection, the person-specialized config variant, and optional local demo/deployment wrappers.

Do **not** use this sub-skill for text-to-video, DreamVideo subject/motion customization, InstructVideo reward fine-tuning/inference, or generic VideoComposer/HiGen/VideoLCM routing.

## Route quickly

1. Confirm the user wants I2VGen-XL image-to-video, not a text-only or customization workflow.
2. Check that CUDA inference is available. The verified drafting environment had CUDA PyTorch plus `xformers`, `open-clip-torch`, `fairscale`, `diffusers`, `transformers`, `piq`, `scikit-image`, and an OpenCV-compatible NumPy stack; CPU-only execution is not a valid proof for this workflow.
3. Validate the input list before spending GPU time:

   ```bash
   python sub-skills/image-to-video/scripts/check_i2vgen_inputs.py data/test_list_for_i2vgen.txt --check-exists --root /path/to/VGen
   ```

4. Prefer the bundled local launcher for reproducible repository work. Point `--repo-root` at a checkout that contains `inference.py`:

   ```bash
   python sub-skills/image-to-video/scripts/run_i2vgen_inference.py --repo-root /path/to/VGen --dry-run --cfg configs/i2vgen_xl_infer.yaml -- \
     test_list_path data/test_list_for_i2vgen.txt \
     test_model models/i2vgen_xl_00854500.pth
   ```

5. Use `configs/i2vgen_xl_infer_person.yaml` only when the user has the person-specialized checkpoint and matching person input list/caption assets, or when they explicitly want to adapt that variant.
6. Treat `predict.py` and `gradio_app.py` as reference-only/demo surfaces unless the user explicitly asks for Cog/Replicate or ModelScope/Gradio deployment and accepts network-backed demo dependencies.

## Bundled references

- `references/workflows.md` explains the config variants, list schema, local command shape, checkpoint expectations, person overrides, and optional demo wrappers.
- `references/troubleshooting.md` covers missing models, malformed lists, CUDA/distributed failures, demo dependency problems, save/playback issues, and known content limitations.
- `scripts/check_i2vgen_inputs.py` validates I2VGen-XL image-plus-caption list files and can optionally check that referenced images exist.

## Operating guardrails

- Keep model downloads, ModelScope caches, Cog deployment setup, and Gradio installs out of the required local inference path unless the user asks for them.
- Do not silently switch to T2V, DreamVideo, or InstructVideo configs when an I2VGen-XL checkpoint or list file is missing; report the missing I2VGen asset and request or locate the correct replacement.
- For quick smoke runs, reduce `round` to `1` and keep only one active non-comment line in the list. The repository demo list recommends one data point at a time.
- Keep local environment paths and private cache locations out of handoffs and user-facing instructions.
