# Architecture and Model Components

Read this when a task requires HunyuanVideo terminology, model-component routing, or API-level reasoning before choosing a setup, inference, optimization, or web-demo workflow.

## Model overview

HunyuanVideo is a text-to-video diffusion system that denoises in a spatial-temporally compressed latent space. The key code-owned components are:

- `HYVideoDiffusionTransformer`: the dual-stream/single-stream transformer backbone. The released configs include `HYVideo-T/2` and `HYVideo-T/2-cfgdistill`; the default parser choice is `HYVideo-T/2-cfgdistill`.
- `AutoencoderKLCausal3D`: a causal 3D VAE. The default `884-16c-hy` VAE uses 16 latent channels, spatial compression ratio 8, and temporal compression ratio 4.
- `TextEncoder`: wraps the primary decoder-only LLM text encoder and secondary CLIP-L text encoder. Default text encoder paths are resolved under the model base as `text_encoder` and `text_encoder_2`.
- `FlowMatchDiscreteScheduler`: the flow-matching Euler scheduler used by the inference pipeline; examples use `--flow-shift 7.0` and `--flow-reverse`.
- `HunyuanVideoSampler`: high-level loader/predictor used by `sample_video.py` and `gradio_server.py`.

## Important implementation facts

- The default parser model is `HYVideo-T/2-cfgdistill`, which enables guidance embedding in the transformer config.
- `--vae 884-16c-hy` implies latent channel count 16. Passing a different `--latent-channels` value raises a sanity-check error.
- In `HunyuanVideoSampler.predict`, output height/width are aligned upward to multiples of 16 before sampling.
- For the default VAE, `video_length` must be `1` or satisfy `(video_length - 1) % 4 == 0`. Common choices are 65 frames (about 2s) and 129 frames (about 5s).
- If `guidance_scale == 1.0`, the negative prompt is cleared in `predict`; otherwise a default negative prompt is used when no negative prompt is supplied.
- Output samples are saved as MP4 grids at 24 fps by the canonical sampling script.

## Prompt rewrite note

`hyvideo/prompt_rewrite.py` contains prompt templates for Normal and Master rewrite modes. It does not call a rewrite model by itself. Use it as a prompt-template reference when a user asks how HunyuanVideo expects rewritten English video descriptions; do not imply it performs local rewriting without the separate HunyuanVideo-PromptRewrite model.

## When to route elsewhere

- For model-file paths and text encoder preprocessing, use `sub-skills/checkpoint-and-setup/`.
- For CLI/API sampling commands, use `sub-skills/inference/`.
- For FP8 or multi-GPU behavior, use `sub-skills/parallel-and-optimization/`.
- For Gradio UI behavior, use `sub-skills/web-demo/`.
