# Video MLLM Troubleshooting

## Model or processor load fails

Check model ID/path, `trust_remote_code=True`, Transformers version, local cache availability, and whether the model requires gated/network access. Do not retry large downloads without approval.

## Video decoding or processor failure

Validate the video file independently. Reduce FPS or pixel budget for memory-constrained runs. Ensure `qwen-vl-utils` and video decoding backends are installed.

## CUDA out of memory

Lower FPS, `min_pixels`, `max_pixels`, `max_new_tokens`, or batch size. Use bf16 where supported. For long videos, memory can scale quickly with visual token count.

## SFT metadata failure

Validate `META_DATA_PATH` JSON and each referenced annotation/media path before launching. A missing object-store config or processor path can fail late in cluster jobs.

## Benchmark path failure

Evaluation scripts often contain dataset-specific root defaults. Replace them with local benchmark paths and verify that video IDs map to actual files.

## Flash Attention / FSDP failures

InternVideo3 SFT requires a more specialized training stack than inference. Match PyTorch, Transformers, Flash Attention, and GPU support before treating a failure as model-code related.
