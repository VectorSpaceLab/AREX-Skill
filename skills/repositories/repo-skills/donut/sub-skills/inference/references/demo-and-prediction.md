# Demo and prediction

This reference covers the Donut inference path that future agents should use for one image at a time.
It is self-contained and does not depend on the original repository checkout at runtime.

## Core API reminders

The installed package exposes the following public signatures:

```python
DonutConfig(input_size=[2560, 1920], align_long_axis=False, window_size=10, encoder_layer=[2, 2, 14, 2], decoder_layer=4, max_position_embeddings=None, max_length=1536, name_or_path='', **kwargs)
DonutModel(config)
DonutModel.from_pretrained(pretrained_model_name_or_path, *model_args, **kwargs)
DonutModel.inference(image=None, prompt=None, image_tensors=None, prompt_tensors=None, return_json=True, return_attentions=False)
```

The source implementation also provides:

```python
model.json2token(obj, update_special_tokens_for_json_key=True, sort_json_key=True)
model.token2json(tokens, is_inner_value=False)
```

## Load a checkpoint

`DonutModel.from_pretrained(...)` accepts either a Hugging Face model ID or a local checkpoint directory.
It always loads the `official` revision for public Donut checkpoints, and it can resize decoder position embeddings when you pass a different `max_length` than the checkpoint was trained with.

```python
from donut import DonutModel

model = DonutModel.from_pretrained("naver-clova-ix/donut-base-finetuned-cord-v2")
# or
model = DonutModel.from_pretrained("/path/to/local/checkpoint")
```

If you need an offline-only run, point at a local checkpoint directory and use the bundled CLI flag `--local-files-only`.

## Prompt and task selection

Use the exact prompt family the checkpoint was fine-tuned with.
If the prompt does not match the task family, the model may still return text, but the JSON structure will usually be wrong.

| Task family | Prompt template | Notes |
| --- | --- | --- |
| CORD / structured extraction | `<s_cord>` | Default choice for receipt-style parsing checkpoints. |
| RVL-CDIP / classification | `<s_rvlcdip>` | Usually returns a JSON object with a `class` field. |
| DocVQA | `<s_docvqa><s_question>{question}</s_question><s_answer>` | Put the question inside the question tag and keep the answer tag open. |
| Other task-specific fine-tunes | `<s_{task}>` | Replace `task` with the checkpoint's task token family. |

The source demo uses raw user text in the DocVQA question slot.
If you are reproducing dataset evaluation logic, match the evaluation script's question casing rules.

## Single-image inference

Use the CLI wrapper for a single local image:

```bash
python scripts/run_inference.py \
  --model naver-clova-ix/donut-base-finetuned-cord-v2 \
  --image /path/to/document.png \
  --task cord
```

For DocVQA:

```bash
python scripts/run_inference.py \
  --model naver-clova-ix/donut-base-finetuned-docvqa \
  --image /path/to/document.png \
  --task docvqa \
  --question "What is the invoice total?"
```

To compare prompt variants on the same image, repeat `--prompt`:

```bash
python scripts/run_inference.py \
  --model naver-clova-ix/donut-base-finetuned-cord-v2 \
  --image /path/to/document.png \
  --prompt "<s_cord>" \
  --prompt "<s_rvlcdip>"
```

The CLI prints a JSON object with the model, chosen device, image path, and a `results` list.
Each entry contains the prompt and either the parsed JSON prediction or the raw token string when `--raw-token` is used.

## Raw output and token conversion

`DonutModel.inference(..., return_json=False)` returns the generated token string with the first task start token stripped.
That is useful when you want to diagnose prompt mismatch before converting the output back to JSON.

A round-trip example:

```python
from donut import DonutModel

# model is a loaded DonutModel instance
payload = {
    "total": {"price": "25.000"},
    "menu": [{"nm": "Lemon Tea", "cnt": "1"}],
}

tokens = model.json2token(payload, sort_json_key=True)
restored = model.token2json(tokens)
```

Notes:

- `json2token` emits nested `<s_key>...</s_key>` tags and joins list items with `<sep/>`.
- `token2json` returns ordered JSON-like Python objects; if no Donut tags are present, it falls back to `{"text_sequence": tokens}`.
- Special categorical tokens such as `<paid/>` round-trip back to their plain label form.
- `sort_json_key=True` is the default and gives stable token order for the same JSON payload.

## Image preprocessing behavior

The encoder input path follows the model implementation:

1. Convert the input to RGB.
2. If `align_long_axis` is enabled and the image orientation disagrees with the canvas, rotate by 90 degrees.
3. Resize the shorter edge to `min(input_size)`.
4. Thumbnail into the target canvas.
5. Pad to the exact canvas size, centered by default.

Inference uses deterministic padding.
Random padding is a training-time behavior in the dataset pipeline, not the inference path.

## CPU and CUDA behavior

The model behaves differently depending on the active device:

- On CUDA, inference converts image tensors to `half()` and moves the model and tensors to GPU.
- On CPU, inference keeps float32 and does not use half precision.
- If you want to debug a checkpoint on CPU even though the host has a GPU, pass `--device cpu`.
- If you want the automatic behavior, pass `--device auto` or omit the flag in the CLI wrapper.

The demo launcher follows the same device rules.

## Gradio demo launcher

The bundled demo wrapper mirrors the source `app.py` workflow but keeps all runtime behavior inside this skill tree.

Examples:

```bash
python scripts/launch_demo.py \
  --model naver-clova-ix/donut-base-finetuned-docvqa \
  --task docvqa \
  --port 7860
```

```bash
python scripts/launch_demo.py \
  --model naver-clova-ix/donut-base-finetuned-cord-v2 \
  --task cord \
  --sample-image /path/to/sample.png
```

Useful launch flags:

| Flag | Meaning |
| --- | --- |
| `--host` | Gradio bind address. Use `0.0.0.0` for remote access. |
| `--port` | Gradio port. Change it when another process already uses the default. |
| `--share` | Ask Gradio to create a temporary public share link. |
| `--sample-image` | Seed the demo with a local example image. |
| `--sample-question` | Optional example question for DocVQA demos. |
| `--device` | `auto`, `cpu`, or `cuda`. |
| `--local-files-only` | Disable Hub downloads when you already have a local checkpoint. |

If the demo fails to bind, change the port first.
If you need a CPU-only demo on a GPU host, force `--device cpu`.
