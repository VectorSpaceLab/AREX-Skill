# Hugging Face and Transformers usage

Evidence labels distilled into this reference: `classification/huggingface/README.md`, `classification/huggingface/convert.py`, `classification/huggingface/test.py`, and classification model/config evidence.

The Hugging Face path is separate from the local `classification/main.py` training path. Transformers use does not require importing the local InternImage checkout, but it does require `transformers`, `torch`, `Pillow`, network or cached model assets, and `trust_remote_code=True` for the published custom model code.

## Published model IDs

| Model ID | Role | Resolution / target | Notes |
| --- | --- | --- | --- |
| `OpenGVLab/internimage_l_22k_384` | backbone/pretrained visual model | 384, IN-22K | L-scale pretrained model |
| `OpenGVLab/internimage_xl_22k_384` | backbone/pretrained visual model | 384, IN-22K | XL-scale pretrained model |
| `OpenGVLab/internimage_h_jointto22k_384` | backbone/pretrained visual model | 384, joint -> IN-22K | H-scale, very large |
| `OpenGVLab/internimage_g_jointto22k_384` | backbone/pretrained visual model | 384, joint -> IN-22K | G-scale, extremely large |
| `OpenGVLab/internimage_t_1k_224` | ImageNet-1K classifier/backbone | 224 | T, source claim 83.5 top-1 |
| `OpenGVLab/internimage_s_1k_224` | ImageNet-1K classifier/backbone | 224 | S, source claim 84.2 top-1 |
| `OpenGVLab/internimage_b_1k_224` | ImageNet-1K classifier/backbone | 224 | B, source claim 84.9 top-1 |
| `OpenGVLab/internimage_l_22kto1k_384` | ImageNet-1K classifier/backbone | 384 | L fine-tuned from IN-22K, source claim 87.7 top-1 |
| `OpenGVLab/internimage_xl_22kto1k_384` | ImageNet-1K classifier/backbone | 384 | XL fine-tuned from IN-22K, source claim 88.0 top-1 |
| `OpenGVLab/internimage_h_22kto1k_640` | ImageNet-1K classifier/backbone | 640 | H, source claim 89.6 top-1, high memory |
| `OpenGVLab/internimage_g_22kto1k_512` | ImageNet-1K classifier/backbone | 512 | G, source claim 90.1 top-1, very high memory |

## Command-builder template

Use the bundled helper to print a standalone Transformers snippet:

```bash
python scripts/build_classification_command.py \
  --mode hf-transformers \
  --hf-model OpenGVLab/internimage_t_1k_224 \
  --hf-task both \
  --image CHANGE_ME/image.png
```

The generated snippet uses:

- `CLIPImageProcessor.from_pretrained(model_name)` to preprocess an image;
- `AutoModel.from_pretrained(model_name, trust_remote_code=True)` for backbone hidden states;
- `AutoModelForImageClassification.from_pretrained(model_name, trust_remote_code=True)` for classifier logits;
- CPU by default when CUDA is not available, although large H/G models may be impractical on CPU.

## Minimal backbone usage pattern

```python
from PIL import Image
from transformers import AutoModel, CLIPImageProcessor

model_name = "OpenGVLab/internimage_t_1k_224"
image = Image.open("CHANGE_ME/image.png").convert("RGB")
processor = CLIPImageProcessor.from_pretrained(model_name)
pixel_values = processor(images=image, return_tensors="pt").pixel_values
model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
hidden_states = model(pixel_values).hidden_states
print([tuple(x.shape) for x in hidden_states])
```

Expected signal: `hidden_states` is a sequence of stage outputs from the InternImage backbone. Use this for feature extraction into downstream code when no local checkpoint/config path is needed.

## Minimal classification usage pattern

```python
import torch
from PIL import Image
from transformers import AutoModelForImageClassification, CLIPImageProcessor

model_name = "OpenGVLab/internimage_t_1k_224"
image = Image.open("CHANGE_ME/image.png").convert("RGB")
processor = CLIPImageProcessor.from_pretrained(model_name)
pixel_values = processor(images=image, return_tensors="pt").pixel_values
model = AutoModelForImageClassification.from_pretrained(model_name, trust_remote_code=True)
logits = model(pixel_values).logits
label_id = int(torch.argmax(logits, dim=1))
print(label_id, tuple(logits.shape))
```

The published examples print an integer label ID, not a human-readable ImageNet class name. Add your own id-to-label mapping if the downstream task needs names.

## Conversion notes for local checkpoints

The source conversion script is not bundled as a runtime helper because it hardcodes local model folders, checkpoint filenames, and a test image. Its useful distilled logic is:

1. Load a Transformers config from the target local model directory with `AutoConfig.from_pretrained(..., trust_remote_code=True)`.
2. Create `AutoModelForImageClassification.from_config(config, trust_remote_code=True)`.
3. Load a PyTorch checkpoint dictionary and read `checkpoint['model']`.
4. For each state key, rename `gamma1` -> `layer_scale1` and `gamma2` -> `layer_scale2` when present.
5. Prefix each converted key with `model.` before loading into the Transformers classifier.
6. Save the converted model with `save_pretrained(target_dir)`.
7. Smoke-test with `CLIPImageProcessor` and an image, checking output shapes and logits.

Use this pattern only when the user owns the checkpoint and target model directory. It may need updates if a checkpoint schema does not use `checkpoint['model']` or if the custom Transformers code changes.

## Network, cache, and trust boundary

- `from_pretrained` may access the Hugging Face Hub unless the model and remote code are already cached.
- `trust_remote_code=True` executes repository-provided model code from the model ID or local model directory. Confirm this is acceptable for the user's trust policy.
- For offline runs, pre-populate the model cache or pass a local model directory to `--hf-model`.
- Published H/G models are large; memory pressure can occur even when the command is syntactically correct.

## DCNv3 notes for Transformers vs local source

The Hugging Face model card states that a PyTorch implementation can be used when the CUDA DCNv3 kernel is unavailable. The local classification configs, however, set `CORE_OP: DCNv3` and the local model modules import `ops_dcnv3`/`DCNv3` directly. Therefore:

- For Transformers inference, first treat missing custom code/cache/network as the likely failure surface.
- For local `main.py` or `extract_feature.py`, treat `ModuleNotFoundError: DCNv3` as a local operator installation/config issue and use `references/troubleshooting.md` plus the deployment sub-skill for DCNv3 build diagnosis.
- If experimenting with `MODEL.INTERN_IMAGE.CORE_OP=DCNv3_pytorch` in local configs, expect different speed/memory behavior and validate numerical acceptability before comparing metrics.
