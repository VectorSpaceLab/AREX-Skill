# Model config reference

OpenAssistant inference workers select models by `MODEL_CONFIG_NAME`. The shared registry maps names to `ModelConfig(model_id, max_input_length, max_total_length, quantized)` and exposes helpers:

- `is_llama`: true when `model_id` contains `llama` case-insensitively.
- `is_lorem`: true only for `model_id == "_lorem"`.
- `compat_hash`: `<model_id>-<max_total_length>-<max_input_length>-q|f`, where `q` means quantized and `f` means full precision.

Use [`../scripts/check_inference_config.py`](../scripts/check_inference_config.py) to list names or inspect a config from a checkout without downloading weights.

## Safe smoke configs

| Name | Model id | Use | Notes |
| --- | --- | --- | --- |
| `_lorem` | `_lorem` | CPU-only protocol/SSE/worker plumbing smoke | Worker does not load a tokenizer or contact the text-generation backend; generated text is lorem-style. |
| `distilgpt2` | `distilgpt2` | Tiny real-tokenizer/model development path | May download from Hugging Face unless cached. Use only when downloads are acceptable. |

## OpenAssistant model families in the registry

Representative names include:

```text
OA_SFT_Pythia_12B, OA_SFT_Pythia_12Bq, OA_SFT_Pythia_12B_4, OA_SFT_Pythia_12Bq_4,
OA_SFT_Llama_7B, OA_SFT_Llama_13B, OA_SFT_Llama_13Bq,
OA_SFT_Llama_30B, OA_SFT_Llama_30Bq, OA_SFT_Llama_30B_2, OA_SFT_Llama_30Bq_2,
OA_SFT_Llama_30B_5, OA_SFT_Llama_30Bq_5, OA_SFT_Llama_30B_6, OA_SFT_Llama_30Bq_6,
OA_SFT_Llama_30B_7, OA_SFT_Llama_30Bq_7, OA_SFT_Llama_30B_7e3,
OA_RLHF_Llama_30B_2_7k, Carper_RLHF_13B_1, Carper_RLHF_13Bq_1,
OA_SFT_Llama2_70B_10, OA_SFT_CodeLlama_13B_10
```

The suffix `q` denotes quantized config entries. It does not by itself install the required runtime, CUDA stack, model weights, or text-generation server image.

## GPU sizing heuristic

The worker documentation gives a conservative memory heuristic:

- Full precision-ish config: required GPU memory in GB is roughly `parameters_in_billions * 2.5`.
- Quantized config ending in `q`: required GPU memory in GB is roughly `parameters_in_billions * 1.25`.

Examples:

| Config family | Approx params | Non-quantized estimate | Quantized estimate |
| --- | ---: | ---: | ---: |
| 7B | 7 | 17.5 GB | about 8.75 GB if a q variant exists |
| 13B | 13 | 32.5 GB | 16.25 GB |
| 30B | 30 | 75 GB | 37.5 GB |
| 70B | 70 | 175 GB | 87.5 GB if quantized similarly |

Always leave headroom for tokenizer/model overhead, server process memory, KV cache, concurrent requests, and framework fragmentation. Increasing `MAX_PARALLEL_REQUESTS` raises throughput only when spare GPU memory exists.

## Config selection workflow

1. Prefer `_lorem` to validate server/worker/auth/SSE plumbing without downloads.
2. Use `distilgpt2` for a tiny real generation path when network/cache is available.
3. Use an OA SFT/RLHF config only after checking GPU memory, driver/runtime, cache location, and the proper worker image tag.
4. For LLaMA-family configs, use a worker/image path that supports LLaMA tokenizers and model loading.
5. For quantized configs, ensure the worker runtime has the quantization backend expected by the image and that the config name actually ends in `q`.

## Cache and download considerations

- Worker container examples use `OAHF_HOME` or Hugging Face cache mounts. The cache location can affect permissions because some containers run as root.
- `download_model.py` loads tokenizer and model with Transformers; it can be large and network-bound.
- `download_model_hf.py` snapshots a Hugging Face repo and normalizes JSON spelling for LLaMA/Llama compatibility.
- Do not trigger downloads as a diagnostic unless the user explicitly accepts network, disk, time, and credentials requirements.
