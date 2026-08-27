---
name: paddle-workflows
description: "Use face.evoLVe PaddlePaddle training, quantization, Paddle
  Inference, and Paddle Lite workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# paddle-workflows

Use this sub-skill when the task is about the PaddlePaddle side of face.evoLVe: Paddle training configuration, Paddle model component inspection, quantization-aware training, post-training quantization, Paddle Inference server demos, Paddle Lite edge demos, or diagnosing missing Paddle deployment artifacts.

## Route here for

- Running or planning PaddlePaddle training from ImageFolder identity folders using IR/IR-SE/ResNet backbones, ArcFace/CosFace/SphereFace/Am_softmax/Softmax heads, and Focal/Softmax losses.
- Inspecting Paddle backbone/head/loss source components without accidentally importing the local `paddle/` source package as the PaddlePaddle framework.
- Exporting a trained Paddle backbone to `.pdmodel`/`.pdiparams`, enabling QAT with `SAVE_QUANT_MODEL`, or preparing dynamic/static PaddleSlim quantization.
- Preparing the Paddle Inference FaceDatabase workflow, `face_data.fdb`, demo video input, GPU predictor settings, and recognition thresholds.
- Preparing Paddle Lite `.nb` model artifacts and runtime prerequisites for edge inference demos.

## Route elsewhere

- Generic ImageFolder identity-folder validation, low-shot pruning, or dataset cleanup belongs in `data-preparation`.
- MTCNN alignment details and face-crop generation belong in `face-alignment` unless the Paddle demo-specific FaceDatabase flow is the focus.
- PyTorch training, PyTorch checkpoint extraction, and PyTorch verification metrics belong in `pytorch-training` or `feature-extraction-verification`.

## Bundled references and scripts

- Read [references/paddle-training-deployment.md](references/paddle-training-deployment.md) when planning Paddle training, export, QAT, post-training quantization, Paddle Inference, or Paddle Lite deployment prerequisites.
- Read [references/troubleshooting.md](references/troubleshooting.md) when diagnosing PaddlePaddle import shadowing, missing PaddleSlim/requests, absent `.pdmodel`/`.pdiparams`/`.nb` artifacts, hard-coded GPU predictor settings, FaceDatabase/video/font problems, or data layout errors.
- Run [scripts/inspect_paddle_components.py](scripts/inspect_paddle_components.py) for a safe CPU component smoke check that reports the installed PaddlePaddle version and a Paddle backbone output shape from a working face.evoLVe checkout.

## Verification boundary

Construction evidence confirmed only safe import/component checks: PaddlePaddle and PaddleSlim imported, and a Paddle IR_50 CPU eval forward produced a `[2, 512]` embedding shape. Full Paddle training, QAT quality, post-training quantization, Paddle Inference video recognition, and Paddle Lite edge deployment remain artifact/hardware-dependent and are not verified unless the user supplies data, trained/exported models, videos, fonts, and compatible runtimes.
