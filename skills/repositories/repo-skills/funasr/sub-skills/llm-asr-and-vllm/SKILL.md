---
name: llm-asr-and-vllm
description: "Route FunASR LLM-ASR model families, AutoModelVLLM acceleration,
  and backend caveats for Nano, GLM-ASR, and Qwen3-ASR."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# FunASR LLM-ASR and vLLM

Use this sub-skill when a task mentions Fun-ASR-Nano, Fun-ASR-MLT-Nano, GLM-ASR-Nano, Qwen3-ASR, `AutoModelVLLM`, vLLM weight preparation, LLM-ASR dtype/device decisions, or accelerator caveats. This route is for model-family and acceleration decisions, not for generic transcription, training, export, or server deployment.

## Fast route selection

- **Fun-ASR-Nano / Fun-ASR-MLT-Nano with vLLM throughput:** stay here. Use `AutoModelVLLM` or the Nano vLLM engine after confirming the model directory is the full checkpoint root, not the nested LLM config-only directory.
- **GLM-ASR-Nano with vLLM throughput:** stay here. Use the GLM vLLM path only for shorter/fixed segments and prefer `dtype="bf16"` or `dtype="fp32"`.
- **Qwen3-ASR:** stay here for dependency and backend routing, but do **not** use FunASR `AutoModelVLLM`. Use FunASR `AutoModel` for the package wrapper or the `qwen_asr` package's own model/runtime when intentionally using its vLLM-enabled stack.
- **Paraformer, SenseVoice, Conformer, CT-Transformer, punctuation, or ordinary ASR calls:** route to `../python-asr-pipelines/SKILL.md`; those model families are not accelerated by `AutoModelVLLM`.
- **OpenAI-compatible HTTP, realtime WebSocket, MCP, Docker, or packaged services:** route service setup to `../serving-and-runtime/SKILL.md` and return here only for Nano/GLM/Qwen3/vLLM-specific caveats.
- **Fine-tuning, LoRA training, manifest conversion, export, ONNX, or checkpoints:** route to `../training-data-and-export/SKILL.md`; only keep inference-time LoRA/CTC caveats here.

## Minimum facts to collect

1. Model family or model id: Fun-ASR-Nano, Fun-ASR-MLT-Nano, GLM-ASR-Nano, Qwen3-ASR, LLMASR, or a non-LLM FunASR family.
2. Runtime intent: standard `AutoModel`, FunASR `AutoModelVLLM`, direct Nano/GLM vLLM engine, or Qwen3 native `qwen_asr` runtime.
3. Backend and package state: CUDA/NPU/CPU, `torch` CUDA availability, `vllm` availability, `qwen-asr` and `transformers` versions when Qwen3 is involved.
4. Dtype and model length settings: `bf16` is the default recommendation; `fp16` can produce degraded output for Nano/GLM; `fp32` is the safer fallback on hardware without bfloat16.
5. Audio shape and workload: short segment, long recording needing VAD segmentation, batch throughput, streaming, timestamps, language hint, hotwords, and whether a service wrapper is involved.

## Operating workflow

1. Read [`references/vllm-and-models.md`](references/vllm-and-models.md) to classify the family and choose the right runtime path.
2. Run the bundled diagnostic before recommending vLLM installation or model loading:

   ```bash
   python scripts/check_vllm_ready.py --model-family Fun-ASR-Nano --target auto --device cuda:0 --dtype bf16
   ```

   The helper only inspects package/backend availability and model-family applicability. It does not download checkpoints, initialize vLLM, or allocate a live model.
3. If the helper reports a non-LLM or unsupported family, do not force vLLM. Use the standard `AutoModel` path and route generic usage to `python-asr-pipelines`.
4. If the helper reports missing optional packages, use the model-family-specific next steps in [`references/troubleshooting.md`](references/troubleshooting.md). Keep Qwen3 remediation separate from FunASR `AutoModelVLLM` remediation.
5. For a real vLLM run, verify the environment first, then construct the model with deterministic decoding defaults (`temperature=0.0`, `top_p=1.0`, `repetition_penalty=1.0`) and pass pre-segmented audio for long recordings.
6. If the task expands into API serving, realtime sessions, Docker, or benchmarks, switch to `serving-and-runtime` for service mechanics and keep this sub-skill as the model/backend caveat source.

## Safety and boundary notes

- vLLM is optional. A valid FunASR installation can import `AutoModelVLLM` while `vllm` itself is absent; absence only blocks accelerated runtime initialization.
- `AutoModelVLLM` accelerates autoregressive LLM-decoder ASR families. It is not a universal speed-up layer for all FunASR models.
- Qwen3-ASR is LLM-based but uses the external `qwen-asr` package and is explicitly not handled by FunASR `AutoModelVLLM`.
- Do not claim NPU/Ascend production support for Nano/vLLM unless the exact `torch_npu`, CANN, vLLM-Ascend, and operator stack is validated for the user's hardware.
- Hotwords passed to Nano/GLM vLLM are prompt hints, not deterministic post-processing replacements. Do not assume optional fuzzy/pinyin hotword matching is installed; use explicit mappings or the serving/text-normalization routes when deterministic replacement is required.
