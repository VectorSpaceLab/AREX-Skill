# FunASR troubleshooting

This page is cross-cutting. If the problem is specific to subtitles, services, vLLM, text cleanup, or training/export, route to the matching sub-skill after checking the item here.

## Install and import

- `import funasr` should work in a healthy install.
- `from funasr import AutoModel` requires PyTorch.
- If `AutoModel` fails because `torch` is missing, install a compatible torch/torchaudio pair first and then re-run the FunASR import.
- Use `funasr.get_import_errors()` or `FUNASR_IMPORT_DEBUG=1` when optional submodules fail to import and you need the names of the missing helpers.

## Hub and model selection

- `ms` and `hf` are both supported hubs.
- If a download is slow or fails, confirm the hub, model id, and network environment before changing anything else.
- If the user wants a first model, check `model-overview.md` rather than guessing from a single clean demo.
- If a task mentions a model family rather than a workflow, route through the model-overview page and then to the right sub-skill.

## Audio decoding

- `load_bytes()` distinguishes raw PCM from container audio.
- If a file path is invalid, fix the path rather than passing a string into the model and waiting for a cryptic type error.
- If container audio fails to decode, verify `soundfile` / `torchaudio` first and use `ffmpeg` only when the user explicitly wants that backend.

## Service startup

- `funasr-server` needs the server extras used by the serving sub-skill, typically including `fastapi`, `uvicorn`, and multipart upload support.
- Realtime problems often come from chunk size, endpoint mode, sample rate, or keepalive settings rather than the model itself.
- Browser or CORS issues are usually solved by matching the trusted origin exactly.
- `funasr_mcp_server.py`-style helpers need local-file access and a valid stdio handshake.

## Optional backend and dependency issues

- Nano / GLM / Qwen3 backend choice belongs in `llm-asr-and-vllm`.
- Pynini / ITN / TN problems belong in `text-normalization`.
- Manifest and export problems belong in `training-data-and-export`.
- Missing `vllm`, `pypinyin`, `qwen-asr`, or runtime SDK dependencies should be treated as optional unless the user explicitly asked for that path.

## Useful recovery pattern

1. Run the safe environment helper: `python scripts/check_funasr_env.py --check-cli --check-torch`.
2. Confirm the model family and route.
3. Check the sub-skill troubleshooting page for the workflow-specific fix.
4. Re-run only the smallest safe command that proves the fix.

## What not to do

- Do not assume a GPU backend is available just because the host has a GPU.
- Do not use a CPU-only import as proof of vLLM, CUDA, or other accelerator coverage.
- Do not tell users to run source checkout files directly from the runtime skill.
