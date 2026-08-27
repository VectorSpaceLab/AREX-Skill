# Training Troubleshooting

## DeepSpeed or Transformers import failures

- **Symptom**: `ImportError` or version conflicts when importing `torch`, `transformers`, `deepspeed`, or `datasets`.
- **Likely cause**: the environment was built with a mismatched CUDA/torch stack or a stale pip wheel.
- **Recovery**: verify the target prefix first, then reinstall the training dependencies into a fresh private environment if needed.

## `torch` loads but CUDA is unavailable

- **Symptom**: `torch.cuda.is_available()` is `False` even though GPUs are visible on the host.
- **Likely cause**: a CPU-only torch wheel, broken driver passthrough, or a partially repaired prefix.
- **Recovery**: confirm the environment was built with the CUDA-capable wheel expected by the repo workflow.

## `flash_attn` / attention backend issues

- **Symptom**: the training script warns that flash-attention is unavailable or incompatible.
- **Likely cause**: optional extension wheels are absent or do not match the torch/CUDA ABI.
- **Recovery**: disable the optional flag first, then add the extension only if the workflow truly needs it.

## Dataset schema or registry mismatches

- **Symptom**: `dataset` cannot be found or `load_dataset` fails on the training JSON.
- **Likely cause**: the registry name in `dataset_info.json` does not match the YAML or CLI argument.
- **Recovery**: compare the dataset file name, dataset registry key, and prompt template before relaunching.

## DeepSpeed runtime issues

- **Symptom**: training starts but exits during launch, gradient accumulation, or distributed initialization.
- **Likely cause**: incorrect `deepspeed` config, too many GPUs requested, or a missing distributed backend.
- **Recovery**: start from the smallest documented batch size and a single-node launch, then scale up.

## ColossalAI dataset prep issues

- **Symptom**: the pretraining dataset script cannot find input directories or the tokenizer.
- **Likely cause**: the CLI arguments point to the wrong data tree or tokenizer checkpoint.
- **Recovery**: confirm the input directories contain JSONL files and the tokenizer path is valid before running the splicer.
