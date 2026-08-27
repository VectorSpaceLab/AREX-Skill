# Maintainer workflows

## Purpose

Use this reference when a task involves changing vLLM-Omni source code, model integrations, adapters, deploy defaults, or tests. It prioritizes focused, safe checks before expensive GPU/native examples.

## Test selection strategy

Start with the smallest check that exercises the changed surface:

| Change surface | First checks | Escalate when |
| --- | --- | --- |
| CLI parser, tracking namespace, stage overrides | CPU parser/config unit tests; safe CLI `--help` checks. | A launch command reaches runtime configuration. |
| Deploy YAML schema or stage defaults | Run the bundled deploy validator, then focused config-factory tests if available. | The change affects actual stage placement or connectors. |
| Offline prompt/output helpers | CPU prompt/output utility tests and synthetic output-access checks. | A real model output formatter changes. |
| OpenAI protocol or payload handling | Request schema/unit tests and no-network payload examples. | Server response streaming or media encoding changes. |
| Diffusion scheduler/attention/offload/quantization | Unit tests for config propagation and scheduler logic. | The change requires actual CUDA kernels, model weights, or throughput metrics. |
| TTS adapter | Static adapter contract checker and adapter-specific unit tests. | Audio codec, forced aligner, or model-specific dependency changes. |
| New model family | Registration/config/parser checks, then a tiny cached model smoke if available. | Full checkpoint generation or accuracy parity is needed. |

Do not launch broad `tests/e2e`, nightly, benchmark, or model accuracy suites unless the user explicitly asks and the required hardware/model cache is available.

## Pytest marker reading

The repository uses markers to separate lightweight and heavy cases. Treat marker names as routing signals:

- `cpu` and `core_model`: candidates for focused local verification when dependencies import.
- `diffusion`: may be CPU config tests or full GPU model tests; inspect the individual test before running.
- `advanced_model` and `full_model`: usually require larger model weights, accelerator hardware, or longer runtime.
- `example`: often means a documented workflow; do not assume it is cheap.
- Hardware decorators or notes naming `cuda`, `rocm`, `H100`, `MI300`, `NPU`, or multiple cards are backend gates, not ordinary skips.

## Editing model code safely

1. Identify whether the code is native vLLM-Omni logic, an adapter, or vendored/upstream parity code.
2. Preserve import order when comments say vLLM-Omni patches vLLM at import time.
3. Avoid touching broad registries and deploy defaults in the same patch as model math unless the change requires it.
4. Keep optional imports lazy where the package supports many model families with different extras.
5. Preserve response schema and output field names because serving clients and docs rely on them.
6. When changing scheduler or stage lifecycle code, consider abort/cleanup paths and pending input queues.
7. When changing multimodal output movement, preserve CPU/GPU transfer semantics and do not leak live GPU tensors into responses unless expected.

## Custom pipeline development loop

- Write the custom class and local import path.
- Run static syntax/import-path checks without loading the model.
- Instantiate only after the target CUDA environment is ready.
- Use a tiny prompt and minimal image/video dimensions when the model supports them.
- Check output fields with the offline-inference output-access guidance.
- Only then move to a server launch or benchmark.

## TTS adapter workflow

1. Run the bundled static checker against the adapter file.
2. Confirm prompt/reference-audio schema and required optional packages.
3. Confirm adapter output shape and response packaging in a CPU unit test if possible.
4. Test streaming chunk boundaries and forced aligner behavior separately from full audio quality.
5. Run a full model/audio smoke only when the voice model, codec, and hardware are available.

## Documentation and examples

When updating docs or examples:

- Keep `--omni` visible in serving commands.
- Prefer `extra_body` for diffusion-specific request parameters in SDK examples.
- Mark model downloads, gated checkpoints, and GPU/VRAM needs explicitly.
- Keep stage-based launch commands consistent across head and headless workers.
- Avoid absolute local paths in examples; use placeholders or user-provided paths.

## Escalation criteria

Escalate from static/CPU checks to GPU/full-model checks only when a claim depends on actual model execution:

- New kernel or attention backend behavior.
- Quantization/offload/cache compatibility.
- Model output quality, frame/audio validity, or streaming latency.
- Multi-GPU connector and stage handoff behavior.
- Real OpenAI-compatible server response with media payloads.
