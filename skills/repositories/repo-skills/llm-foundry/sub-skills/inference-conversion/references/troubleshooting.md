# Troubleshooting Inference and Conversion

Start by separating four classes of failure: missing artifact, missing dependency/credential, incompatible runtime backend, or expected side effect not authorized.

## Quick triage

1. Is the input local, remote object storage, or Hugging Face Hub?
2. Is the requested action read-only, local write, remote upload, network endpoint call, or GPU/native-library execution?
3. Can the task be bounded with the safe smoke script before loading weights?
4. Does the task actually belong here, or should it route to training, evaluation, data preparation, or model configuration?

Run the safe probe when possible:

```bash
python scripts/llmfoundry_inference_smoke.py --check-env --strict
```

Add local artifact checks without loading weights:

```bash
python scripts/llmfoundry_inference_smoke.py \
  --hf-folder <local-hf-folder> \
  --composer-checkpoint <checkpoint-or-uri> \
  --model-dtype bf16 \
  --device cuda:0 \
  --attn-impl flash
```

## Failure-mode matrix

| Symptom | Likely cause | Action |
|---|---|---|
| `name_or_path` not found | Local HF folder path is wrong, mounted volume missing, or Hub id requires network | Verify local folder exists and has `config.json`; if using Hub, confirm network and auth. |
| Local HF folder has config but fails load | Missing tokenizer files, missing weights, incompatible custom code, or wrong `trust_remote_code` decision | Inspect folder for tokenizer/weight indicators; decide whether custom code is trusted; pin `revision` for Hub models. |
| Composer conversion says `state` key missing | File is not a full Composer `Trainer` checkpoint | Use a full Composer checkpoint, not a raw PyTorch state dict or already-converted HF weights. |
| Composer conversion cannot find Hugging Face integration state | Checkpoint lacks tokenizer/HF model integration metadata | Confirm training used Composer `HuggingFaceModel`; otherwise use training code/config to reconstruct tokenizer/model manually. |
| No Hugging Face token / 401 / gated repo | Private/gated Hub model or upload target without valid token | For local conversion, skip Hub upload. For Hub load/upload, login or set an approved token and confirm access. |
| Hub upload works but `--test_uploaded_model` fails | Upload incomplete, token cannot read back, model too large to reload, dtype mismatch, or custom code issue | First verify local folder; then test Hub reload separately with adequate memory and `trust_remote_code` if approved. |
| `trust_remote_code` error or prompt to trust code | Model config references custom Python code | Enable only if the repo/folder is trusted. For untrusted sources, choose a standard-Transformers model or inspect code in a sandbox. |
| `--device` and `--device_map` both set | Mutually exclusive loading strategies | Use `--device` for one explicit device or `--device_map` for Accelerate placement, not both. |
| `bf16`/`fp16` fails on CPU | CPU or installed torch build does not support requested low precision | Use `fp32` on CPU. Use GPU for `bf16`/`fp16` inference when hardware supports it. |
| CUDA out of memory during generation/chat | Model too large, batch too large, sequence length too long, or device map unsuitable | Reduce `max_batch_size`, `max_new_tokens`, `max_seq_len`; use `device_map auto`; choose smaller dtype; use a smaller model. |
| CPU RAM exhausted during conversion/export | Composer/HF model must be loaded in CPU RAM; ONNX sample batch is too large | Use smaller model, more RAM, smaller `export_batch_size`/`max_seq_len`, or a machine designed for conversion. |
| Flash attention import/kernel failure | Optional flash-attention backend missing or incompatible | Use `--attn_impl torch` unless flash attention is installed and compatible with the GPU, dtype, and model. |
| MPT ONNX export fails with attention op errors | Non-exportable attention backend | Force attention implementation to `torch`; reduce sequence length; ensure opset/dependencies are compatible. |
| ONNX verification mismatch | Numerical tolerance, unsupported op, dtype/device difference, dynamic shape issue, or ONNX Runtime gap | First export without verification; then run `--verify_export` with small batch/sequence; compare dependency versions. |
| ONNX verification cannot import `onnx` or `onnxruntime` | Optional verification dependencies missing | Install/check those packages or export without `--verify_export`. |
| Object-store input cannot be read | Missing credentials, wrong bucket/prefix, unsupported backend, or network/proxy issue | Verify backend credentials externally; retry with a local copy for debugging. |
| Object-store output/upload fails | No write permission, parsed prefix mismatch, target exists, or network failure | Write locally first; then copy/upload with explicit credentials and overwrite policy. |
| Output folder already exists | Converter/exporter may create folders or refuse conflicting target dirs | Use a new output path or intentionally clean/stage the target after user approval. |
| Chat model repeats format markers or ignores roles | Tokenizer chat template does not match model training format | Inspect/adjust `tokenizer.chat_template`; set a clear `system_prompt`; avoid assuming legacy user/assistant format flags. |
| Chat stops too early or never stops | Stop tokens not in tokenizer vocabulary or wrong stop sequence | Check `--stop_tokens`; use `history_fmt` to inspect rendered prompt; align stop tokens with the model template. |
| Prompt file is not split as expected | Missing or wrong `--prompt-delimiter` | Use `file::<path>` and set an explicit delimiter; verify expected number of prompts before generation. |
| Endpoint script says URL missing | Neither `--endpoint` nor `ENDPOINT_URL` is set | Provide endpoint URL only after the user approves network use. |
| Endpoint 401/403 | Missing/invalid `ENDPOINT_API_KEY` or service-specific auth header expectations | Confirm the service auth scheme; do not print secrets in logs. |
| Endpoint bad response schema | Service is not OpenAI-compatible completions or returns non-JSON errors | Inspect one redacted response; adapt client or use the provider's official SDK. |
| FT cannot load `libth_transformer.so` | FasterTransformer was not built or `lib_path` is wrong | Treat FT as reference-only until the native library path exists and matches the Python/CUDA/PyTorch environment. |
| FT multi-GPU hangs/fails | PyTorch lacks MPI backend, `mpirun` mismatch, wrong tensor parallel size, or checkpoint converted for different `infer_gpu_num` | Verify MPI-enabled PyTorch, launch process count, GPU visibility, and `<infer_gpu_num>-gpu` checkpoint folder. |
| FT conversion refuses model features | MPT config has unsupported `clip_qkv` or `qk_ln` | Do not force conversion unless the user accepts accuracy/compatibility risk. |

## Memory and precision guidance

- Prefer `fp32` for CPU debug and conversion sanity checks.
- Prefer `bf16` on Ampere-or-newer GPUs when the model and torch build support it.
- Prefer `fp16` only when the model/backend is known to be stable in half precision.
- For a first generation smoke, set `max_new_tokens` small, batch size 1, and disable warmup if measuring is not needed.
- For ONNX, sequence length drives sample input size and graph shape pressure; reduce `max_seq_len` before changing unrelated settings.

## Credential hygiene

- Never paste tokens into generated files or logs.
- Use cached login or environment variables for Hub and endpoint credentials.
- Confirm remote uploads separately from local conversion/export.
- Treat `--test_uploaded_model` as a network read plus full model reload, not as a harmless local check.

## Routing reminders

- If the user asks how to configure `HuggingFaceCheckpointer` inside a training YAML, route the YAML/training callback edit to `training-finetuning` and use [conversion-reference.md](conversion-reference.md) only for artifact semantics.
- If the user asks why MPT attention config fields behave a certain way, route to `package-apis-configuration`.
- If the user asks for ICL/eval metrics, route to `evaluation`.
