# Cross-Cutting Troubleshooting

Read this before changing dependencies, rebuilding extensions, lowering model quality, or starting long GPU/model jobs.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'lmdeploy'` | Active Python environment does not have LMDeploy installed | Install `lmdeploy` in the active environment or run from the intended source checkout after editable install. Re-run `python scripts/check_lmdeploy_environment.py`. |
| `No module named 'mmengine.config.lazy'` | Stale or incompatible `mmengine` package | Upgrade `mmengine`/`mmengine-lite` in the active environment, then re-run import checks. |
| `No module named '_turbomind'` | TurboMind extension missing, not built, or shadowed by running inside a source checkout | Use a prebuilt `lmdeploy` wheel for normal users. For source work, build TurboMind with the correct Python/CUDA toolchain or set `DISABLE_TURBOMIND=1` when only PyTorch/Python inspection is needed. |
| `rdkit` missing | Chemistry-specific optional/runtime dependency absent | Install `rdkit` only if the selected model/media workflow needs chemistry support. Text LLM, normal VLM, serving, and config inspection often do not need it. |

## CUDA, NCCL, and Runtime Libraries

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `libnccl.so.2 not found` | NCCL runtime library not visible to the process | Prefer packaged LMDeploy runtime dependencies. If using manually installed NCCL packages, add the package library directory to `LD_LIBRARY_PATH` for the shell that launches LMDeploy. |
| `cudaFreeAsync ... not defined` | CUDA runtime/toolkit too old for the installed package | Use a CUDA runtime/toolkit compatible with the LMDeploy/PyTorch wheel, or install an LMDeploy wheel built for the current CUDA stack. |
| `torch.cuda.is_available()` false on a GPU host | Wrong torch wheel, driver/container visibility, or missing devices | Check `nvidia-smi`, container GPU flags, and torch CUDA wheel tag. Do not debug LMDeploy before torch sees CUDA. |

## Memory and Session Length

| Symptom | Applies to | Recovery |
| --- | --- | --- |
| CUDA OOM during pipeline/server startup | TurboMind or PyTorch | Lower `cache_max_entry_count`, `session_len`, `max_batch_size`, or tensor parallel assumptions. For CLI use `--cache-max-entry-count`; for Python use engine config dataclasses. |
| API `finish_reason: length` | Serving APIs | Increase `--session-len` or reduce prompt/history length. If the model context window is fixed, truncate or summarize earlier turns. |
| Multi-image VLM OOM or truncation | VLM pipeline/server | Increase `session_len` when possible, reduce images/frames/resolution, or lower `VisionConfig(max_batch_size=...)`. |

## CLI and API Misuse

- Always run `lmdeploy <command> --help` in the target environment before relying on a flag from memory.
- `lmdeploy serve api_server` and `lmdeploy chat` share many backend flags, but server transport/auth/parser flags belong only to `serve api_server`.
- When auth is enabled with `--api-keys`, add `Authorization: Bearer <key>` to OpenAI/Responses/Anthropic client requests.
- If OpenAI Responses and Anthropic endpoints are both documented in a task, keep them separate: `/v1/responses` is for Responses-style clients; `/v1/messages` is for Anthropic-style clients.

## Quantization Failures

- Calibration OOM: lower `--calib-seqlen`, keep `--batch-size 1`, then consider sample count/search-scale trade-offs.
- Disk errors while saving weights: verify free space in `--work-dir` before retrying large model quantization.
- `flash_attn` missing for Qwen-family quantization: install the optional dependency only if the selected quantization path requires it and the CUDA/PyTorch stack can build or install it.
- Wrong `--model-format`: AWQ outputs load with `--model-format awq`; GPTQ outputs load with `--model-format gptq`.

## Source Checkout and Maintainer Work

- For Python-only inspection or PyTorch model work, avoid compiling TurboMind unless the task requires it: `DISABLE_TURBOMIND=1 pip install -e .`.
- For TurboMind source builds, align `CUDACXX`, CUDA toolkit, Python executable, and `CMAKE_BUILD_TYPE`; a build for one Python environment may not load in another.
- For PyTorch tensor parallel scripts, guard pipeline creation with `if __name__ == "__main__":` to avoid multiprocessing bootstrap errors.
- For new model support, use `sub-skills/backend-extension/SKILL.md` and run focused config/model tests in the current checkout before broad test suites.

## When to Stop

Stop and ask for user confirmation before:

- Downloading model weights or datasets.
- Starting a long-running server, benchmark, quantization, or native GPU test.
- Installing broad extras or changing a user-provided environment.
- Running commands that require credentials, external services, or destructive writes.
