---
name: video-sampling
description: "Run, adapt, and troubleshoot standalone SVD, SVD-XT, SV3D, SV4D,
  and SV4D2 video sampling workflows from bundled generative-models guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Video Sampling

Use this sub-skill when a task mentions `simple_video_sample`, SVD image-to-video, SV3D camera paths, SV4D video-to-4D, SV4D2, 8-view video-to-4D, low-VRAM `encoding_t`/`decoding_t`, video frame folders/globs, or background removal for video sampling.

## Route First

- Use `references/workflows.md` to choose between SVD/SVD-XT image-to-video, SV3D_u/SV3D_p multi-view image sampling, SV4D, SV4D2, and SV4D2 8-view mode.
- Use `references/cli-reference.md` for parameter defaults, safe command templates, and Fire-style list/boolean argument examples.
- Use `references/model-and-inputs.md` for checkpoint filenames, config names, frame/view counts, camera-list lengths, input formats, and output naming.
- Use `references/troubleshooting.md` for missing checkpoints, CUDA/VRAM failures, invalid inputs, camera-list mismatch, `remove_bg`/`rembg`, video write issues, and SV4D/SV4D2-specific failure modes.
- Use `scripts/inspect_video_sampling_cli.py` for static inspection: `python <path-to-this-sub-skill>/scripts/inspect_video_sampling_cli.py --script all --json`.

## Scope

- This sub-skill covers standalone video sampling workflows driven by `scripts/sampling/simple_video_sample.py`, `scripts/sampling/simple_video_sample_4d.py`, and `scripts/sampling/simple_video_sample_4d2.py`.
- Full sampling is checkpoint-bound and normally CUDA/GPU-bound; prefer the bundled static helper for planning and CI-safe inspection.
- For SDXL Python inference APIs, route to `../inference-api/SKILL.md`.
- For training or config authoring, route to `../training-and-configs/SKILL.md`.
- For Streamlit/Gradio app operation or watermark/NSFW filtering internals, route to `../demos-and-watermarking/SKILL.md`.

## Quick Decisions

- Image-to-video from one image or an image folder: use SVD/SVD-XT via `simple_video_sample.py --version svd` or `--version svd_xt`.
- 21-frame object orbit from one image: use SV3D_u via `simple_video_sample.py --version sv3d_u`.
- Custom 21-step elevation/azimuth camera path from one image: use SV3D_p via `simple_video_sample.py --version sv3d_p`.
- Video-to-4D with SV3D first-frame reference views: use SV4D via `simple_video_sample_4d.py`.
- Video-to-4D without SV3D reference generation: use SV4D2 via `simple_video_sample_4d2.py`.
- 8 novel views per temporal chunk: use SV4D2 8-view mode with `--model_path checkpoints/sv4d2_8views.safetensors`.
