# Cross-cutting Troubleshooting

## Start With the Right Checker

| Problem area | Use |
|---|---|
| Missing source files or model assets | `scripts/check_repository_assets.py` |
| PyTorch/ONNX inference assets and optional imports | `sub-skills/portrait-inference/scripts/check_photo2cartoon_assets.py` |
| Face alignment, segmentation graph, crop/mask contract | `sub-skills/preprocessing/scripts/preprocess_contract_check.py` |
| Dataset folder/schema issues | `sub-skills/data-and-training/scripts/validate_dataset_layout.py` |
| Model class shape/checkpoint issues | `sub-skills/model-internals/scripts/model_forward_smoke.py` |

## Installation and Import Failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| No package metadata or `pip install -e` fails | The repo is not packaged with setup metadata. | Use a checkout as a source tree. Add that checkout to `PYTHONPATH` or use bundled helpers with explicit `--repo-root`; do not expect a wheel distribution. |
| `ModuleNotFoundError` for `cv2`, `face_alignment`, `tensorflow`, `dlib`, `onnxruntime`, or `cog` | Workflow-specific optional dependency is missing. | Install only the dependency group for the selected workflow in a private env/container. Avoid broad legacy installs in a shared environment. |
| TensorFlow graph/session errors | The source uses `tf.compat.v1` graph/session APIs and an external `.pb` graph. | Verify `seg_model_384.pb` exists and use a TensorFlow version that still supports `tf.compat.v1.Session` and graph import. |
| dlib build failure | Python/platform/compiler mismatch for dlib wheels or source build. | Prefer a private Python 3.8-era container for exact Cog behavior; otherwise choose a supported wheel/toolchain before installing. |
| `torchvision` import needed for training object | `models/UGATIT_sadalin_hourglass.py` imports torchvision transforms. | Install torchvision only when training/data-loader construction is needed; architecture smoke checks can load `models/networks.py` directly without it. |

## Asset Failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Missing `.pt`, `.onnx`, `.pb`, or MobileFaceNet files | External assets are not tracked because `.gitignore` excludes model files. | Ask the user to provide the assets or point to an authorized download. Do not invent or silently download them. |
| Checkpoint key mismatch | File is from another training script/export or was saved in a different format. | Use `model-internals` checkpoint guidance and inspect keys. Inference needs `genA2B`; training checkpoints need all generator/discriminator keys. |
| Dataset folders absent | Training data has not been prepared under the expected domain layout. | Use `data-and-training` data-format guidance and validator before training. |

## Backend and Runtime Failures

- CUDA is optional for this skill's safe checks but important for practical training and sometimes speed. Verify actual torch CUDA allocation before claiming GPU readiness.
- ONNX Runtime provider names are environment-specific. Query available providers and choose one that exists.
- OpenCV writes BGR images; the repo converts BGR -> RGB before preprocessing and RGB -> BGR before saving. Double conversions produce wrong colors.
- `torch.nn.functional.upsample` deprecation warnings are expected in modern torch and do not by themselves mean the source model is broken.

## When to Route Deeper

- If the symptom says no face was found or masks/crops look wrong, route to `sub-skills/preprocessing/SKILL.md`.
- If the symptom involves `.pt`/`.onnx` prediction, route to `sub-skills/portrait-inference/SKILL.md`.
- If the symptom involves `trainA`, `trainB`, `ImageFolder`, loss weights, batch size, or checkpoints from training, route to `sub-skills/data-and-training/SKILL.md`.
- If the symptom involves tensor shapes, model classes, `genA2B` keys, Soft-AdaLIN, or Face ID loss, route to `sub-skills/model-internals/SKILL.md`.
