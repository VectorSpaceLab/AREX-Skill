# Qwen-VL installation

This skill was built and checked against a CUDA-capable inspection environment that confirmed a compatible `torch` wheel, `transformers==4.32.0`, `peft==0.5.0`, `deepspeed`, and the service/evaluation helper packages used by the bundled scripts.

## Minimum install groups

Install only the groups that match the workflows you plan to use.

### Common runtime

```bash
python -m pip install --upgrade pip
python -m pip install torch transformers accelerate pillow numpy tqdm
```

### Inference extras

```bash
python -m pip install modelscope
```

### Serving extras

```bash
python -m pip install gradio fastapi uvicorn openai pydantic sse-starlette
```

### Finetuning extras

```bash
python -m pip install peft==0.5.0 deepspeed
```

### Evaluation extras

```bash
python -m pip install pycocotools pycocoevalcap pandas openpyxl av
```

## Recommended smoke checks

After installing the packages you need, run the bundled smoke helper:

```bash
python scripts/runtime_smoke.py --check-cuda
```

To test one or more imports without launching a service or loading weights, add `--import` flags:

```bash
python scripts/runtime_smoke.py --import transformers --import torch
```

## Workflow-specific notes

- `transformers` and `trust_remote_code=True` are required for the custom Qwen-VL model APIs.
- `gradio`, `fastapi`, `uvicorn`, `openai`, `pydantic`, and `sse-starlette` are only needed for the bundled service entrypoints.
- `peft` and `deepspeed` are only needed for the finetuning sub-skill.
- `pycocotools`, `pycocoevalcap`, and `av` are only needed for benchmark work.
- If you need the optional Int4 or Q-LoRA path, keep the quantization extras that your environment already supports; do not assume they are present just because the base model imports succeed.
