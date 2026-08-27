# Inference workflows

## Offline inference modes

| Mode | Use when | Notes |
|---|---|---|
| Synchronous direct | Single process group submits prompts directly to the engine. | Simpler for local scripts and smoke tests. |
| Synchronous coordinator | Primary rank submits requests; workers run through coordinator. | Closer to distributed serving behavior. |
| Asynchronous | Caller needs asyncio integration or nonblocking request handling. | Use `MegatronAsyncLLM`. |
| HTTP serving | OpenAI-compatible endpoint is required. | Uses coordinator path and `ServeConfig`. |

## Offline command template

```bash
python -m torch.distributed.run \
  --nproc-per-node <GPUS> \
  examples/inference/offline_inference.py \
  --load <checkpoint-root> \
  --tokenizer-type <TokenizerType> \
  --tensor-model-parallel-size <TP> \
  --pipeline-model-parallel-size <PP> \
  --num-tokens-to-generate <N> \
  --prompts "Hello Megatron"
```

Add `--use-coordinator` when testing coordinator mode. Add `--async-mode` for async wrapper behavior.

## Server command template

```bash
python -m torch.distributed.run \
  --nproc-per-node <GPUS> \
  examples/inference/launch_inference_server.py \
  --load <checkpoint-root> \
  --tokenizer-type <TokenizerType> \
  --tensor-model-parallel-size <TP> \
  --pipeline-model-parallel-size <PP> \
  --host 127.0.0.1 \
  --port 5000 \
  --frontend-replicas 4
```

Use `0.0.0.0` only when the user intentionally exposes the service.

## Prompt and output handling

- Inline prompts are best for smoke tests.
- Prompt files are useful for batches, but verify whether per-request generation lengths are supported by the chosen wrapper.
- JSON result dumps should include prompts, generated tokens/text, throughput, memory, and engine step counters when available.
- Validate prompt length against context max tokens unless chunked prefill is enabled.

## Legacy text generation tools

Megatron-LM also contains older dynamic/static text generation server tools. Prefer high-level APIs for new tasks unless the user is reproducing a legacy workflow, comparing behavior, or using a feature not yet exposed in the high-level wrapper.

## Preflight checklist

- Environment imports Torch CUDA and Megatron inference modules.
- Checkpoint format and model args match selected model provider.
- Tokenizer files or metadata are available to all ranks.
- TP/PP/CP sizes match checkpoint and launch world size.
- Output path is writable.
- Server port is free and allowed by network policy.
