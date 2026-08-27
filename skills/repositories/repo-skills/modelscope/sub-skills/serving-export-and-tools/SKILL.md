---
name: serving-export-and-tools
description: "Serve ModelScope pipelines, plan vLLM handoffs, use exporter APIs,
  and safely inspect checkpoint utility side effects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving, Export, and Tools

Use this sub-skill when a task asks for ModelScope HTTP serving, vLLM
ModelScope integration, exporter APIs, Docker launch patterns, or safe planning
around large/destructive checkpoint utilities.

## Route by task

- **Local HTTP service, FastAPI endpoints, Docker serving, or vLLM choice:** read
  [references/serving.md](references/serving.md).
- **ONNX, TorchScript, TensorFlow SavedModel/frozen graph, or exporter support
  triage:** read [references/export-and-tools.md](references/export-and-tools.md).
- **Checkpoint conversion, Megatron conversion, weight diff/recover, or any
  destructive/large model utility:** read
  [references/export-and-tools.md](references/export-and-tools.md) first, then
  run the bundled planner with `python scripts/checkpoint_conversion_plan.py --help`.
- **Server, dependency, port, cache, GPU/VRAM, credential, vLLM, exporter, or
  checkpoint failures:** read
  [references/troubleshooting.md](references/troubleshooting.md).

## Route away

- General in-process `pipeline(...)`, `Model.from_pretrained(...)` inference, and
  task/model construction belong in `../pipelines-and-models/SKILL.md`.
- Hub login, tokens, cache policy, model download flags, dataset/model listing,
  and CLI download/upload workflows belong in `../hub-and-cli/SKILL.md`.

## Safety defaults

- Treat serving and export commands as potentially **model-loading** operations:
  they may allocate GPU/CPU memory and may populate the ModelScope cache if the
  requested model is not already local.
- Treat CUDA, domain-specific extras, vLLM execution, and large-model serving as
  optional and unverified for this production scope. Preflight hardware and
  package availability before promising them.
- Never run checkpoint conversion tools directly on the only copy of a model.
  First run the bundled dry-run planner, confirm expected output names, make an
  external backup or work on a copy, and verify enough disk space.

## Minimal command memory

ModelScope server is the ModelScope FastAPI wrapper. Its core CLI shape is:

```bash
modelscope server \
  --model_id "$MODEL_ID_OR_LOCAL_MODEL_DIR" \
  --revision "$REVISION" \
  --host 127.0.0.1 \
  --port 8000 \
  --debug info \
  --external_engine_for_llm True
```

The inspected wrapper parses `--external_engine_for_llm` with Python `bool`;
verify target-version behavior before assuming a string value disables it.

vLLM is a separate runtime. Use the ModelScope-aware vLLM pattern only when vLLM
is installed and the model is vLLM-compatible:

```bash
VLLM_USE_MODELSCOPE=True python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_ID_OR_LOCAL_MODEL_DIR" \
  --revision "$REVISION" \
  --port 9090
```
