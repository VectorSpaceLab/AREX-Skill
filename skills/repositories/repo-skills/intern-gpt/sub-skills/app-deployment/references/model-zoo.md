# Model zoo and checkpoint placement

InternGPT expects most local checkpoints under `model_zoo/` in the application working directory. Some dependencies also create their own cache/checkpoint directories. A syntactically valid `--load` string only proves the app knows the class names; it does not prove that weights, restricted licenses, CUDA kernels, or credentials are ready.

## Quick readiness checklist

Before launch, check the intended direct loads against this table.

| Capability | Direct load class | Expected local or cached assets | What fails when missing |
| --- | --- | --- | --- |
| Husky VQA/chat over images | `HuskyVQA` | `model_zoo/husky-7b-v0_01`; if absent, the app tries to build it from `model_zoo/husky-7b-delta-v0_01` plus a restricted LLaMA base under `model_zoo/llama/7B`, then writes `model_zoo/llama_7B_hf`. | Missing `config.json` under `model_zoo/llama_7B_hf`, missing `params.json` under `model_zoo/llama/7B`, or failed delta application. |
| SAM segmentation and mask extraction | `SegmentAnything`; template `ExtractMaskedAnything` | `model_zoo/sam_vit_h_4b8939.pth` (`vit_h`). | The app attempts a network download if absent; offline launches fail or hang. |
| OCR | `ImageOCRRecognition` | EasyOCR models/cache plus OpenCV runtime dependencies. | OCR init or first OCR call fails; app may still launch if not loaded. |
| LaMa/LDM inpainting | `LDMInpainting` | `model_zoo/ldm_inpainting_big.ckpt` plus inpainting config packaged with the app. | Inpainting/removal fails at model load or state-dict load. |
| Stable Diffusion / ControlNet image generation | `Text2Image`, `Image2Canny`, `CannyText2Image`, `Image2Hed`, `Image2Scribble`, `ScribbleText2Image`, `SegText2Image`, `ReplaceMaskedAnything` | Diffusers/Hugging Face model caches for Stable Diffusion, ControlNet, annotators, BLIP, and related processors. | First load may download very large models; restricted/offline environments fail. |
| ImageBind and StableUnCLIP cross-modal generation | `Anything2Image`; templates `Audio2Image`, `Thermal2Image`, `AudioImage2Image`, `AudioText2Image` | StableUnCLIP model cache and `checkpoints/imagebind_huge.pth`. | Audio/thermal/image-conditioned generation fails even if the `Audio` tab renders. |
| StyleGAN/DragGAN tab | `StyleGAN` | `model_zoo/stylegan2-ffhq-config-f.pt`. | `New Image` or DragGAN initialization fails; the app may attempt a network download if missing. |
| Video captioning | `VideoCaption` | `model_zoo/tag2text_swin_14m.pth`; Tag2Text configs and BERT tokenizer/cache. | Video upload/caption functions fail. |
| Action recognition | `ActionRecognition` | InternVideo/UniformerV2 checkpoint cache from the model hub. | Action recognition load or first prediction fails. |
| Dense captioning | `DenseCaption` | `model_zoo/grit_b_densecap_objectdet.pth`, GRiT configs, detectron2/CenterNet2-compatible runtime. | Dense captions fail, often with detectron2 build or missing-weight errors. |
| TikTok-style video generation | Template `GenerateTikTokVideo` from `ActionRecognition`, `VideoCaption`, `DenseCaption` | All video assets above, OpenAI key, Bark/speech dependencies, and ffmpeg. | Integrated clip generation fails even if individual video tools partially work. |

## Husky/LLaMA conversion contract

`HuskyVQA` is the most common model-zoo pitfall.

1. `model_zoo/husky-7b-delta-v0_01` is a delta, not a complete model.
2. The complete Husky model is built from the delta plus a restricted LLaMA 7B base. The operator must separately obtain permission for the LLaMA base.
3. The app expects the original base at `model_zoo/llama/7B` and converts it to a Hugging Face-style directory at `model_zoo/llama_7B_hf` before applying the Husky delta into `model_zoo/husky-7b-v0_01`.
4. If a run is interrupted during download or conversion, partial folders can be worse than absent folders. Missing `config.json` in `model_zoo/llama_7B_hf` or missing `params.json` in `model_zoo/llama/7B` means the base/conversion is incomplete.
5. After confirming that no useful completed weights are present, remove only the bad partial LLaMA/Husky conversion folders and rerun with a valid LLaMA base source. Preserve any licensed weights that were successfully downloaded.

Do not publish presigned LLaMA URLs, copied restricted weights, or private credential material in the skill tree, logs, or launch commands.

## `model_zoo/` layout sanity check

For a basic image-dialogue launch, the minimum local layout usually needs:

```text
model_zoo/
  husky-7b-delta-v0_01/      # delta supplied by the release package
  llama/7B/                  # restricted LLaMA base; operator-provided
  llama_7B_hf/               # generated conversion output
  husky-7b-v0_01/            # generated complete Husky model
  sam_vit_h_4b8939.pth       # SAM vit_h checkpoint
```

For DragGAN-only, a much smaller local layout can be enough:

```text
model_zoo/
  stylegan2-ffhq-config-f.pt
```

For full multimodal service, add the Tag2Text, GRiT, inpainting, ImageBind, StableUnCLIP, Stable Diffusion/ControlNet, action-recognition, and speech/video dependencies listed above.

## Model cache expectations

Some classes load from paths under `model_zoo/`; others call model-hub or public-download APIs if weights are absent. In restricted environments, treat every first-run download as a deployment risk:

- Pre-stage large and licensed weights before starting the service.
- Keep the application working directory consistent so relative paths such as `model_zoo/` and `certificate/` resolve correctly.
- Do not use a successful static `--load` validation as proof that model weights are present.
- For offline or production use, verify each required local checkpoint before invoking the class that uses it.
