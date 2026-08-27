# API Overview

This reference summarizes shared Transformers APIs used across sub-skills. Use the focused sub-skill references for detailed recipes and failure handling.

## Package Identity

- Distribution name: `transformers`
- Import module: `transformers`
- Generated skill baseline version: `5.13.0.dev0`
- Console script: `transformers`, routed to `transformers.cli.transformers:main`

## Common Loading APIs

| API | Primary owner | Notes |
| --- | --- | --- |
| `pipeline(...)` | Inference pipelines | High-level inference across task families. Important parameters include `task`, `model`, preprocessors, `device`, `device_map`, `dtype`, `trust_remote_code`, `revision`, and `model_kwargs`. |
| `AutoConfig.from_pretrained(path_or_id, **kwargs)` | Inference, generation, model extension | Loads config from Hub id, local directory, or checkpoint. Use it for cheap local/offline validation before loading weights. |
| `AutoTokenizer.from_pretrained(path_or_id, *inputs, **kwargs)` | Tokenizers/processors | Loads tokenizer assets; use `local_files_only=True` for offline checks and `use_fast` to control fast-vs-slow implementation. |
| `AutoProcessor.from_pretrained(path_or_id, **kwargs)` | Tokenizers/processors | Loads multimodal processors when model families combine text, image, audio, or video preprocessing. |
| `GenerationConfig(**kwargs)` | Generation, serving CLI | Stores decoding parameters; validate conflicts before calling `generate()` or serving endpoints. |
| `TrainingArguments(...)` | Training | Defines `Trainer` run settings, distributed options, precision, logging/eval/save cadence, Hub push, and optimizer settings. |
| `ContinuousBatchingConfig(...)` | Generation, serving CLI | Configures paged KV cache, scheduling, CUDA graphs/compile, request queue, offload, and logprob behavior. |

## Optional Dependency Boundaries

Transformers uses lazy imports. A base install can expose many names but raise an informative `ImportError` only when a backend-dependent class is used.

Typical boundaries:

- PyTorch: model classes, `Trainer`, most pipelines, generation execution, tensor parallelism, FSDP/DeepSpeed integration.
- `tokenizers`: fast tokenizer backend.
- `sentencepiece`, `tiktoken`, `mistral-common`: tokenizer families and conversion paths.
- Pillow, torchvision, timm: vision processors and vision pipelines.
- torchaudio, librosa, pyctcdecode, phonemizer: audio processors and ASR/audio pipelines.
- fastapi, uvicorn, pydantic, openai, rich, requests/httpx: CLI serving and chat/client conveniences.
- accelerate, datasets, evaluate, peft: training, placement, fine-tuning, and evaluation workflows.
- bitsandbytes, GPTQ/AWQ/torchao/quanto/etc.: quantization-specific workflows.

## Safe Validation Sequence

1. Import `transformers` and print `transformers.__version__`.
2. Use `AutoConfig.from_pretrained(..., local_files_only=True)` for local checkpoint structure checks.
3. Use tokenizer/processor smoke checks before model execution.
4. Construct config objects (`GenerationConfig`, `TrainingArguments`, quantization configs) before running heavyweight workflows.
5. Run the nearest bundled sub-skill script with `--help` or dry-run flags.
6. Only download, allocate GPU memory, launch services, or start training after the dry-run path passes.

## Trust And Security

- `trust_remote_code=True` executes model repository Python code. Use it only after reviewing the code or when the user explicitly accepts the risk.
- Never hard-code Hub tokens or credentials in generated scripts or examples.
- Prefer `token=True` to use the user's configured credential when gated/private access is required.
- Treat CLI server startup as a long-lived service side effect; prefer preflight unless the user asks to run it.
