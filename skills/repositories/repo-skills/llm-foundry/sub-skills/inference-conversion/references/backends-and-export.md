# Backends, Export Prerequisites, and Safe Probing

Use this reference to decide whether an inference/export task can run in the current environment or must be treated as planning/reference-only. It complements [workflows.md](workflows.md) and [conversion-reference.md](conversion-reference.md).

## Safe smoke probe

The bundled smoke script is designed to be safe from any current working directory. It does not load large weights, download models, call endpoints, upload to Hugging Face Hub, upload to object storage, run ONNX export, or run FasterTransformer.

Common uses:

```bash
python scripts/llmfoundry_inference_smoke.py --check-env
```

```bash
python scripts/llmfoundry_inference_smoke.py \
  --hf-folder <local-hf-folder> \
  --composer-checkpoint <local-or-remote-composer-checkpoint> \
  --model-dtype bf16 \
  --device cuda:0 \
  --attn-impl flash
```

What it checks:

- whether common runtime modules are import-discoverable (`torch`, `transformers`, `composer`, `llmfoundry`, `onnx`, `onnxruntime`, Hub/client helpers, endpoint helpers, and MPI hints);
- whether the installed environment has the common runtime modules needed by the generated command plan;
- whether a local HF folder has config, tokenizer indicators, and weight-file indicators without loading weights;
- whether a local Composer checkpoint path exists or a remote URI was supplied;
- obvious option conflicts such as setting both a single `--device` and a `--device_map` strategy;
- common backend warnings such as `bf16` on CPU or `flash` attention without a discoverable flash-attention package.

Use `--strict` when a CI-like probe should return non-zero for detected errors.

## Hugging Face model loading prerequisites

A local or Hub `name_or_path` must resolve to a Transformers-compatible causal LM and tokenizer.

Minimum pieces for local offline work:

- `config.json`;
- tokenizer assets such as `tokenizer.json`, `tokenizer.model`, `vocab.json` plus `merges.txt`, or a usable `tokenizer_config.json` with referenced files;
- model weights such as `pytorch_model.bin`, sharded `pytorch_model-*.bin`, `model.safetensors`, sharded `model-*.safetensors`, or matching index JSON;
- custom modeling/tokenizer code if the config requires it and the user accepts `trust_remote_code`.

Backend controls:

- `device_map='auto'` uses Hugging Face Accelerate-style placement and can shard across available devices.
- `device='cuda:0'` or `device='cpu'` means one explicit device. Do not combine `device` with `device_map`.
- `model_dtype` controls weight dtype at load time. `bf16` and `fp16` are normally GPU-oriented; CPU support is limited and hardware-dependent.
- `autocast_dtype` affects generation compute context, not checkpoint storage.
- `attn_impl='flash'` is optional and only works when the model/config supports it, the package is installed, and the GPU/kernel combination is compatible. Use `attn_impl='torch'` as the conservative fallback, especially for export.

## Authentication and revision controls

Use these only when needed:

- `use_auth_token=true` or an explicit token string allows private/gated Hub access if the environment is logged in or has a token.
- `revision` pins a Hub branch, tag, or commit. Prefer a revision for reproducible conversion/export.
- Hub upload uses a Hub API token via cached login or environment token. Local conversion does not require a Hub token.

If credentials are missing, keep the task local or ask the user to provide/login with the appropriate token. Do not invent tokens or silently downgrade private model access to a public model.

## Object-store paths

Composer and ONNX conversion helpers can accept object-store-style URIs for selected inputs or outputs. Treat any URI with `://` as a remote side-effect boundary.

Before using a remote URI, confirm:

- credentials are present for that backend;
- the process has read permission for input checkpoints and write permission for output folders;
- the user accepts network transfer and storage cost;
- local temporary disk is large enough for the checkpoint/output staging that occurs before upload;
- the remote output path should be created/overwritten.

For a first recovery/debugging pass, prefer local input/output paths so failures are easier to inspect.

## ONNX export prerequisites

ONNX export is CPU-capable but memory-intensive. Requirements:

- `torch` and `transformers`;
- a local/cached HF model and tokenizer;
- enough CPU RAM for the model plus the random sample batch;
- an output folder with sufficient disk space;
- `onnx` and `onnxruntime` only when `--verify_export` is requested;
- `max_seq_len` supplied explicitly if the config does not provide it.

Bounded export strategy:

1. Start with a small `--export_batch_size` such as 1.
2. Use a realistic but bounded `--max_seq_len`; avoid jumping directly to very long context exports.
3. Keep attention implementation on `torch` for models with configurable attention.
4. Run without `--verify_export` first if dependencies or memory are uncertain.
5. Add `--verify_export` only after the export succeeds and `onnxruntime` is installed.

## FasterTransformer prerequisites: advanced reference-only

FasterTransformer support is MPT-focused and should be treated as advanced reference-only unless all prerequisites are explicitly present.

Conversion prerequisites:

- an MPT Hugging Face checkpoint or an MPT Composer checkpoint;
- the LLM Foundry utility that converts MPT weights into FT format;
- `infer_gpu_num` set to the intended tensor-parallel GPU count for runtime;
- output directory that does not already contain the target `<infer_gpu_num>-gpu` subfolder;
- supported model features. Some features such as clipped QKV or QK LayerNorm may require an explicit force decision because FT compatibility can be uncertain;
- `weight_data_type`/`output_precision` in `fp32` or `fp16` depending on the converter.

Runtime prerequisites:

- NVIDIA GPU(s) matching the converted checkpoint's tensor-parallel size;
- a built FasterTransformer PyTorch library, including the `libth_transformer.so` shared library path;
- `PYTHONPATH` or package path that exposes the FT Python modules;
- PyTorch built with MPI distributed backend for multi-process FT runs;
- `mpirun`/MPI runtime when using more than one process/GPU;
- tokenizer path, FT checkpoint path, runtime dtype, and generation settings.

Do not run FT as a smoke test. Check only for path/module/library presence unless the user explicitly asks for FT execution and accepts GPU/MPI/native-library side effects.

## Endpoint generation prerequisites: reference-only

Endpoint generation calls a remote OpenAI-compatible completions service. Required:

- URL from `--endpoint` or `ENDPOINT_URL`;
- optional API key in `ENDPOINT_API_KEY` if the service requires auth;
- network egress and any proxy settings;
- compatible request/response schema (`prompt`, generation parameters, `choices`, and `usage` fields);
- prompt inputs and an output target;
- dependencies for asynchronous HTTP and rate limiting.

Before running endpoint generation, ask whether prompts may be sent to the service and whether output should be written locally or to object storage. Keep it reference-only for offline verification.

## Routing optional backends

- If the user wants model architecture/config internals, route to `package-apis-configuration`.
- If the user wants training checkpoint production or callback YAML edits, route to `training-finetuning` and return here only for inference use of produced artifacts.
- If the user wants benchmark/ICL evaluation outputs, route to `evaluation`.
- If the user only needs a prerequisite report, use the smoke script plus this reference and stop before model load/export/network execution.
