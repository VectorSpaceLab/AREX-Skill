# Workflow map

Select by the requested **stage** first, then by model family. If a request contains several stages, split it into an ordered plan instead of choosing a leaf by model name alone.

| Request signal or model family | Primary route | First local material |
| --- | --- | --- |
| YAML training/evaluation, resume or load, fine-tuning, AMP, VisualDL, distributed launch, registry/config questions | [training-configs](../sub-skills/training-configs/SKILL.md) | [training workflows](../sub-skills/training-configs/references/training-workflows.md) |
| One image/portrait/face, restoration, denoising, super-resolution, cartoonization, makeup, parsing, StyleGANv2 latent sampling/editing, SinGAN, or `ppgan.apps` image predictors | [image-and-face-apps](../sub-skills/image-and-face-apps/SKILL.md) | [image workflows](../sub-skills/image-and-face-apps/references/image-workflows.md) |
| Video restoration/colorization/SR, frame interpolation, motion driving, First Order Motion, Wav2Lip, or audio/video alignment | [video-and-audio-apps](../sub-skills/video-and-audio-apps/SKILL.md) | [video workflows](../sub-skills/video-and-audio-apps/references/video-workflows.md) |
| Dataset download, folder layout, preprocessing, `dataroot`, paired/unpaired translation, DIV2K, REDS, Vimeo90K, LRS2, RealSR, CycleGAN, or Pix2Pix inputs | [data-preparation](../sub-skills/data-preparation/SKILL.md) | [dataset layouts](../sub-skills/data-preparation/references/dataset-layouts.md) |
| Checkpoint-to-static export, `.pdmodel`/`.pdiparams` inspection, Paddle Inference, TensorRT, Serving, Lite, C++, or TIPC planning | [deployment-export](../sub-skills/deployment-export/SKILL.md) | [export and inference](../sub-skills/deployment-export/references/export-and-inference.md) |

## Tie-breakers

- A named model does not change the stage: Wav2Lip **LRS2 preparation** is data preparation; Wav2Lip **media execution** is video/audio; Wav2Lip **static export** is deployment/export.
- CycleGAN/Pix2Pix/DIV2K/REDS/Vimeo90K references in a request about folders or preprocessing route to data preparation even when training is planned next.
- StyleGANv2 latent editing is image/face unless the user explicitly requests static export; then deployment/export owns the export stage.
- A custom checkpoint used by a predictor routes to image/face or video/audio based on its input media, not to training. A checkpoint being converted to a static artifact routes to deployment/export.

## Shared checks

Start with [install and setup](install-and-setup.md), then run [the install checker](../scripts/check_install.py). Use [the config checker](../scripts/check_config.py) for YAML parse and existing-key dotted override checks. Use [shared troubleshooting](troubleshooting.md) for cross-cutting failures, then the owning leaf's troubleshooting reference.

## Cross-workflow sequence

1. **Readiness:** choose CPU/GPU and verify package, optional modules, and ffmpeg as applicable.
2. **Data:** validate or preprocess inputs and set explicit `dataroot` paths before a train/evaluate run.
3. **Model stage:** train/evaluate/resume with [training-configs](../sub-skills/training-configs/SKILL.md), or run an already-weighted image/video predictor through its media leaf.
4. **Handoff:** preserve the checkpoint and config; send a static-artifact request to [deployment-export](../sub-skills/deployment-export/SKILL.md), which verifies prefixes and input signatures before runtime planning.

Do not imply that a successful CPU import validates CUDA, face, audio, TensorRT, or deployment runtime behavior.
