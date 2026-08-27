# Qwen-VL troubleshooting

## Install and import problems

### Symptom: `ModuleNotFoundError`
Likely cause: the workflow-specific extras were not installed.

- `transformers`, `torch`, or `accelerate`: install the common runtime group.
- `modelscope`: install the inference extras if you want the ModelScope loading path.
- `gradio`, `fastapi`, `uvicorn`, `openai`, `pydantic`, `sse-starlette`: install the serving extras.
- `peft` or `deepspeed`: install the finetuning extras.
- `pycocotools`, `pycocoevalcap`, `pandas`, `openpyxl`, or `av`: install the evaluation extras.

### Symptom: Qwen custom classes do not load
Likely cause: `trust_remote_code=False` or a checkpoint/model mismatch.

- Use `trust_remote_code=True` for the Qwen-VL loaders.
- Use `Qwen/Qwen-VL-Chat` for chat-style requests and `Qwen/Qwen-VL` for base-model generation.
- If the user wants Int4 or Q-LoRA behavior, make sure they selected the intended quantized checkpoint and not a plain chat model by accident.

## CUDA and backend issues

### Symptom: the smoke helper reports no CUDA
Likely cause: the environment has a CPU-only torch build or no visible GPU.

- CPU import success is not enough to validate training, service, or benchmark workflows.
- Use the bundled smoke helper to check the runtime before assuming the GPU workflows are available.

### Symptom: `deepspeed` warns about `CUDA_HOME`
Likely cause: the toolkit path is missing, or you do not have a CUDA toolkit installed for optional extension builds.

- The warning does not block simple imports or help text.
- It does matter if you want to build optional CUDA extensions or use more advanced DeepSpeed paths.

## Service issues

### Symptom: `stream: true` or malformed function-call requests fail
Likely cause: the bundled OpenAI-compatible service has limited request handling.

- Follow the serving sub-skill for the exact request shape the bundled API accepts.
- Do not promise streaming unless the request path has been confirmed to support it.
- For browser exposure, prefer `127.0.0.1` until the user explicitly chooses `0.0.0.0` or sharing.

## Training issues

### Symptom: data validation errors or malformed grounding tags
Likely cause: the conversation JSON does not follow the documented alternating-turn layout.

- Use the finetuning sub-skill and the bundled validator before launching training.
- Make sure image prompts use the documented `Picture n: <img>...</img>` pattern.
- Keep grounding coordinates normalized and keep `<ref>` paired with `<box>` when you want box supervision.

## Evaluation issues

### Symptom: benchmark scripts cannot find datasets or annotations
Likely cause: the local `data/` layout does not match the expected benchmark layout.

- Follow the evaluation sub-skill's data-layout reference before trying to rerun the benchmark.
- Prefer the CPU-capable conversion and scoring helpers when the benchmark only needs data shaping or scoring.
- Reserve distributed inference for the cases that genuinely need model forward passes.

## When to switch sub-skills

- If the current question is about a direct response to one image, route to `inference`.
- If the current question is about exposing the model as an API, route to `serving`.
- If the current question is about making the model learn from a dataset, route to `finetuning`.
- If the current question is about benchmark metrics or submissions, route to `evaluation`.
