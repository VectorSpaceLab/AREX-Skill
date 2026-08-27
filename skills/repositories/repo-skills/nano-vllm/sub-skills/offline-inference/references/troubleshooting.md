# Offline inference troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: flash_attn` or a missing compiled symbol | FlashAttention is absent or was built for a different torch/CUDA/Python ABI. | Run the root environment probe, then install a compatible FlashAttention build; do not substitute CPU torch for full inference. |
| `assert os.path.isdir(model)` | A remote id, weight file, or misspelled path was passed. | Pass the directory containing config, tokenizer, and safetensors files. |
| `AutoConfig`/tokenizer error | The export is incomplete or is not Qwen3-compatible. | Check `config.json`, tokenizer files, and model-family metadata before debugging prompts. |
| Missing parameter during safetensors loading | Weight names do not match the Qwen3 packed-module mapping. | Use the model-internals contract checker; this package is not a generic Hugging Face loader. |
| Temperature assertion | `temperature <= 1e-10` was supplied. | Use a positive temperature; this implementation intentionally rejects greedy zero-temperature sampling. |
| Empty-prompt/index error | A token-id prompt was empty. | Supply a non-empty string or token-id list. |
| Generation ends early | EOS was sampled or `max_tokens` was reached. | Check `ignore_eos` and `max_tokens`; avoid `ignore_eos=True` except for controlled measurements. |
| `CUDA out of memory` or no KV-cache blocks | Length/batch/memory settings exceed VRAM. | Reduce `max_model_len`, `max_num_batched_tokens`, `max_num_seqs`, or workload. Keep a margin below total memory. |
| CUDA graph capture error | Graph capture is incompatible with the current shape/backend or a prior error polluted the process. | Retry with `enforce_eager=True`; if eager works, treat graph capture as a separate tuning issue. |
| NCCL/child-process hang | Tensor parallel process setup, visible devices, rendezvous, or main guard is wrong. | Start with `tensor_parallel_size=1`, use a main guard, check visible GPUs/NCCL, and explicitly shut down the engine. |
| Results appear out of order or are strings instead of records | Internal sequence ids or the output contract was assumed incorrectly. | Read the returned list in request order and access `output["text"]`/`output["token_ids"]`. |
