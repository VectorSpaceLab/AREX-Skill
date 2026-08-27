# Inference API Reference

## Key imports

```python
from colossalai.inference import InferenceConfig, InferenceEngine
```

Inspected signatures:

```text
InferenceConfig(max_batch_size=8, max_output_len=256, max_input_len=256, dtype=torch.float16, kv_cache_dtype=None, prompt_template=None, do_sample=False, beam_width=1, top_k=50, top_p=1.0, temperature=1.0, use_spec_dec=False, max_n_spec_tokens=5, block_size=16, tp_size=1, pp_size=1, micro_batch_size=1, use_cuda_kernel=False, use_cuda_graph=False, enable_streamingllm=False, patched_parallelism_size=1, ...)
InferenceEngine(model_or_path, tokenizer=None, inference_config=None, verbose=False, model_policy=None)
```

Important methods:

- `generate(request_ids=None, prompts=None, *args, **kwargs)`: run inference and return generated text/images/arrays depending on model type.
- `add_request(request_ids=None, prompts=None, *args, **kwargs)`: enqueue requests.
- `step()`: execute a scheduling step.

## Configuration groups

- Capacity: `max_batch_size`, `max_input_len`, `max_output_len`, `block_size`.
- Sampling: `do_sample`, `beam_width`, `top_k`, `top_p`, `temperature`, `no_repeat_ngram_size`, `repetition_penalty`, `forced_eos_token_id`, `ignore_eos`.
- Parallelism: `tp_size`, `pp_size`, `micro_batch_size`, `patched_parallelism_size`.
- Acceleration: `use_cuda_kernel`, `use_cuda_graph`, `high_precision`, `kv_cache_dtype`.
- Speculative decoding: `use_spec_dec`, `max_n_spec_tokens`, `glimpse_large_kv`.
- Long context: `enable_streamingllm`, `start_token_size`, `generated_token_size`.

## Minimal validation

Construct `InferenceConfig` first. Then validate model/tokenizer loading separately before adding parallelism, speculative decoding, CUDA graph, or fused kernels.
