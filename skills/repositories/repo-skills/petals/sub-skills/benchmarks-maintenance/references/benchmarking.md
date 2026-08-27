# Benchmark Command Construction and Health Signals

Petals benchmark families create distributed clients, connect to DHT peers, may trigger Hugging Face artifact downloads, and can run for a long time. This sub-skill constructs commands and interprets health signals; it does not run them by default.

Use the print-only helper:

```bash
python scripts/build_benchmark_command.py inference --model "$MODEL_NAME" --initial-peer "$INITIAL_PEERS" --smoke
python scripts/build_benchmark_command.py forward --model "$MODEL_NAME" --initial-peer "$INITIAL_PEERS" --smoke
python scripts/build_benchmark_command.py training --model "$MODEL_NAME" --initial-peer "$INITIAL_PEERS" --task cls --smoke
```

The helper emits a command that uses the bundled `scripts/run_petals_benchmark.py` runner. The runner is skill-owned and self-contained, but actual execution may contact peers, download artifacts, and run distributed workloads. Use only after explicit approval.

## Families

- `inference`: one-token-at-a-time autoregressive generation inside an inference session; final speed is generated tokens per second.
- `forward`: random-token forward pass; final speed is `batch_size * seq_len / step_time`.
- `training`: prompt-tuning style forward/backward wiring for `cls` or `causal_lm`; final output has forward and backward speeds.

For smoke checks, prefer `--torch-dtype float32`, one process, private peers, sequence length 3, one warmup step, one measured step, batch size 3, and prompt length 1. Tiny CPU private-swarm numbers are wiring signals, not production throughput.
