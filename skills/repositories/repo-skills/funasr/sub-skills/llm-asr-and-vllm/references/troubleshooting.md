# LLM-ASR and vLLM troubleshooting

## Purpose

Use this reference when Nano/GLM/Qwen3 LLM-ASR setup fails, when vLLM availability is unclear, or when backend-specific warnings could be mistaken for model errors. Start with the bundled diagnostic:

```bash
python scripts/check_vllm_ready.py --model-family Fun-ASR-Nano --target auto --device cuda:0 --dtype bf16
```

The diagnostic is safe in CPU-only environments because it does not load live models.

## Failure map

| Symptom or message | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'vllm'` during `AutoModelVLLM` or direct Nano/GLM vLLM engine initialization | `vllm` is an optional accelerator dependency and is not required for importing FunASR itself. | If the family is Nano/GLM/LLMASR and you really need vLLM, install a vLLM build compatible with the NVIDIA driver CUDA version, then reinstall/verify FunASR without independently mismatching torch wheels. If the model is Qwen3-ASR, do not install FunASR `AutoModelVLLM`; use the Qwen3 instructions below. |
| `Model 'Paraformer' cannot use vLLM`, `Model 'SenseVoice' cannot use vLLM`, or similar | The model is not an autoregressive LLM-decoder ASR family. | Use standard FunASR `AutoModel` and route the task to generic ASR guidance. vLLM is the wrong backend for non-LLM models. |
| `Model 'Qwen3ASR' cannot use vLLM: Uses external qwen-asr package with optimized inference` | Qwen3-ASR is LLM-based, but not supported by FunASR `AutoModelVLLM`. | Use FunASR `AutoModel` with the Qwen3 wrapper, or use `qwen_asr.Qwen3ASRModel` and the `qwen-asr[vllm]` extra for the native Qwen3 vLLM/streaming stack. |
| `dtype='fp16' can produce degraded or garbage transcription` | Nano/GLM audio embeddings are numerically sensitive in fp16. | Prefer `dtype="bf16"`. On hardware without bfloat16 support, use `dtype="fp32"`. Treat fp16 as a last-resort compatibility mode and benchmark accuracy before trusting output. |
| Repeated punctuation such as `!!!!!!!!` from vLLM while standard generate looks normal | Prompt-embedding dtype, checkpoint pairing, or sampling parameters are wrong. Non-neutral repetition penalty is especially risky in prompt-embeds mode. | Keep `temperature=0.0`, `top_p=1.0`, `repetition_penalty=1.0`, and ensure prompt embeddings are float32 when handed to vLLM. Verify that the full checkpoint root and extracted vLLM language-model directory match. Capture generated token ids, finish reason, prompt embedding dtype, and shape for one failing sample. |
| CUDA `scatter gather index out of bounds` when using `repetition_penalty` | vLLM prompt-embeds mode has no prompt token IDs to penalize. | Set `repetition_penalty=1.0`. FunASR Nano/GLM helpers clamp non-neutral values, but wrappers should avoid forwarding non-neutral values in the first place. |
| `model.pt not found`, nested Qwen config directory missing, or `No LLM weights found` during weight preparation | The path is not the full FunASR checkpoint root, the model was only partially downloaded, or the checkpoint does not contain expected `llm.*` tensors. | Point `model` at the full Nano checkpoint root. Re-download the complete checkpoint if needed. Do not point FunASR `AutoModelVLLM` directly at the nested Qwen config-only directory. |
| `No language_model weights found in safetensors` for GLM-ASR vLLM preparation | The GLM checkpoint files do not contain the expected `language_model.*` tensors or are incomplete. | Re-check the model id/revision and download completeness. Use standard `AutoModel` until a complete GLM checkpoint is present. |
| Timestamps are missing even though text transcription works | CTC/timestamp modules were configured but the checkpoint lacks complete `ctc_decoder.*` and `ctc.*` weights, or the weight shapes do not match. | Treat timestamps as optional. Text output remains valid. Use a checkpoint known to include complete CTC weights if character timestamps are required. |
| Long audio returns a partial transcript, truncates, or degrades without a clear exception | Nano vLLM is segment-level and can hit `max_new_tokens` before the audio ends. GLM-ASR also should not be assumed to support long segments. | Pre-segment with VAD and pass segments, or use a high-level standard `AutoModel` path with VAD for long recordings. For GLM-ASR, use fixed/short segments rather than dynamic long-audio VAD. |
| Duplicate result keys after GLM batch inference | Result keys are derived from audio basenames; repeated basenames can collide. | The GLM vLLM engine de-duplicates colliding keys with suffixes such as `_1`, `_2`. If downstream code builds `{key: text}`, keep filenames distinct or preserve the de-duplicated keys. |
| Hotwords do not behave like deterministic replacement | Nano/GLM vLLM hotwords are prompt hints. Optional fuzzy/pinyin behavior may not be installed, and fuzzy matching is not a guarantee. | For decoding bias, pass explicit hotword strings and compare with hotwords disabled. For deterministic term replacement, use explicit post-processing mappings through the serving/text-normalization routes. |
| `qwen-asr package is required for Qwen3-ASR` | Qwen3-ASR's external package is missing. | Install the Qwen3 wrapper dependencies: `pip install -U "qwen-asr==0.0.6" "transformers==4.57.6" accelerate`. If you intentionally need Qwen3 native vLLM/streaming, install `pip install -U "qwen-asr[vllm]==0.0.6" "transformers==4.57.6" accelerate`. |
| `transformers is required by qwen-asr` | `qwen-asr` is installed without a compatible `transformers`. | Run the remediation command reported by `check_vllm_ready.py` or by FunASR's Qwen3 dependency check. Do not repair this by installing FunASR `AutoModelVLLM`. |
| `Qwen3-ASR dependency mismatch: qwen-asr==... requires transformers... but the active environment has transformers==...` | `qwen-asr` declares a `transformers` specifier that the installed version does not satisfy. | Use the exact command in the error, for example: `pip install -U "qwen-asr==0.0.6" "transformers==4.57.6" accelerate`. For native Qwen3 vLLM/streaming, use the matching `qwen-asr[vllm]` extra rather than a newer arbitrary vLLM. |
| Qwen3 native vLLM/streaming starts with `rope_scaling` / `thinker_config` warnings after installing a newer vLLM | The Qwen3 native stack depends on the vLLM version pinned by `qwen-asr[vllm]`; newer vLLM config parsing can degrade multimodal positional handling. | Reinstall with `pip install -U "qwen-asr[vllm]==0.0.6" "transformers==4.57.6" accelerate` and avoid separately upgrading vLLM for this Qwen3 native path. |
| Qwen3 streaming lacks automatic endpointing or VAD behavior | Qwen3-ASR's open-source streaming API is incremental but does not include a server-side endpoint VAD layer. | Use explicit client turn boundaries such as a `STOP` message, or add an external endpoint detector. Do not look for Fun-ASR-Nano segmentation VAD behavior inside Qwen3's streaming core. |
| NPU/Ascend PyTorch `AutoModel` reaches the backend but `AutoModelVLLM` fails in rotary embedding, `TransData`, or similar operator paths | PyTorch backend compatibility and vLLM-Ascend operator support are separate. | Treat NPU as experimental for Nano/vLLM. Capture `torch`, `torch_npu`, CANN, vLLM-Ascend, NPU model, dtype, and a full stack trace with backend blocking enabled. Prefer CUDA/vLLM, standard PyTorch CPU/GPU, or a validated edge runtime for production. |
| Driver/CUDA errors appear before FunASR model code runs | The vLLM/torch/torchaudio/torchvision wheel set does not match the NVIDIA driver CUDA capability. | Let vLLM own the torch wheel trio and choose a vLLM build compatible with the driver. Do not install a random newer torch after vLLM unless the vLLM compatibility matrix says so. |

## Diagnostic interpretation

- `PASS model-family`: the family is a supported FunASR `AutoModelVLLM` family.
- `FAIL model-family`: the family should not use FunASR `AutoModelVLLM`; the helper will name the correct route.
- `WARN vllm-missing`: imports and standard `AutoModel` may still work; accelerated runtime is unavailable until vLLM is installed.
- `WARN dtype`: the requested dtype is allowed but may reduce transcript quality.
- `WARN qwen3`: Qwen3 dependency fixes must use `qwen-asr` commands, not FunASR `AutoModelVLLM` commands.
- `WARN npu`: backend compatibility is not equivalent to production support.

## What to capture before escalating

For Nano/GLM vLLM issues:

- FunASR version, model id or local checkpoint revision, `vllm` version, `torch` version, CUDA driver capability, GPU model, `dtype`, `tensor_parallel_size`, `gpu_memory_utilization`, and `max_model_len`.
- Whether the same short audio segment works through standard `AutoModel`.
- Whether the input is one long recording or pre-segmented audio.
- Sampling parameters, especially `temperature`, `top_p`, `top_k`, and `repetition_penalty`.
- Whether timestamps were requested and whether the checkpoint contains complete CTC weights.

For Qwen3-ASR issues:

- `qwen-asr`, `transformers`, and `accelerate` versions.
- Whether the path is FunASR `AutoModel` wrapper or native `qwen_asr` runtime.
- Whether native vLLM/streaming was requested and which `vllm` version was installed.
- The exact dependency mismatch or startup warning, including the remediation command if emitted.
