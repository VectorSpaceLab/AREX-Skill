# Inference Troubleshooting

## Checkpoint problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `config.json` missing | Wrong directory or incomplete download | Validate the local checkpoint directory before model load. |
| `qwen.tiktoken` missing | Checkpoint assets not fetched with LFS or snapshot incomplete | Re-download/copy tokenizer assets; do not patch tokenizer code first. |
| `QWenTokenizer` not found | Missing remote-code files or `trust_remote_code` omitted | Use trusted checkpoint with remote code and set `trust_remote_code=True`. |
| Shard load error | Incomplete model shards or wrong quantized/base checkpoint | Compare expected shard files and model id. |

## Generation behavior

- Poor instruction following: check whether a base checkpoint was loaded for a chat task.
- Gibberish streaming output: update checkpoint-side tokenizer/model code and review byte-token decoding behavior.
- Prompt echoed in batch outputs: verify left padding, distinct pad token, prompt length slicing, and ChatML context construction.
- Early stop around `Observation:`: tool-use prompts or stop words may be configured; route to prompting-tool-use-tokenization.

## Memory and backend

- CPU-only is likely slow; set expectations and avoid benchmarking it as a deployment path.
- CUDA OOM: reduce model size, sequence length, batch size, precision, or use quantized checkpoints/vLLM after compatibility checks.
- FlashAttention install failure: skip it first and prove native Transformers works; then match torch/CUDA/Python/GPU generation if acceleration is necessary.
- AutoGPTQ import/load errors: isolate a compatible version matrix rather than upgrading every package in place.
- KV-cache quantization and FlashAttention are not a safe combination in the documented Qwen path.

## Network and trust

Remote model identifiers can trigger network downloads and remote-code execution. When the user has no network, use a local checkpoint. When the user does not trust the source, do not set `trust_remote_code=True` until they accept the risk or provide a trusted local copy.
