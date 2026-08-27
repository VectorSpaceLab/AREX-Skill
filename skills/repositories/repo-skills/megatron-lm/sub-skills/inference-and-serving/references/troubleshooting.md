# Inference and serving troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| Checkpoint load fails | Wrong checkpoint format, model args, or parallel sizes. | Route to checkpointing; verify `--load`, tracker, `--ckpt-format`, TP/PP layout. |
| Tokenizer mismatch | Tokenizer model/vocab differs from checkpoint training tokenizer. | Use the checkpoint's tokenizer metadata/files and verify vocab size/padding. |
| Prompt longer than context | Input prompt token length exceeds context max tokens. | Reduce prompt, increase context if model supports it, or enable supported chunked prefill mode. |
| `--prompt-file` with per-request token lengths rejected | High-level API uses one sampling-params object per generate call. | Use uniform `--num-tokens-to-generate`, split calls by generation length, or use a lower-level path. |
| Coordinator workers hang on exit | Primary rank failed to propagate shutdown or exception occurred before context exit. | Ensure context managers are used and catch/propagate errors cleanly across ranks. |
| HTTP server not reachable | Bound to local host, wrong port, firewall, or frontend processes failed. | Check `host`, `port`, logs, and process list; use local host for development. |
| Port already in use | Previous server process still running. | Stop old process or choose another port. |
| CUDA graph capture error | Shape/context/capture settings incompatible with workload or backend. | Disable CUDA graphs for diagnosis, then re-enable with supported prompt lengths and scopes. |
| Very low throughput | Batch size, prompt lengths, coordinator overhead, KV cache, or precision settings inefficient. | Compare direct vs coordinator, inspect memory, tune batch/request sizes, and validate kernels. |
| Rank-specific crash masked by NCCL timeout | One worker hit an earlier Python exception. | Scan every rank log for the first traceback before changing NCCL settings. |

## Server safety

Never expose a generation server on all interfaces without explicit user intent and environment/network authorization. Prefer local bind host for tests.
