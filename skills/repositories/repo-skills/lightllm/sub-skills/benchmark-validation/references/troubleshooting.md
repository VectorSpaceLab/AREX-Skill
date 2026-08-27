# Benchmark troubleshooting

## Benchmark starts but the service is not ready

### Symptoms
- The first benchmark request fails immediately.
- Throughput numbers look wrong because the model was still loading.

### Recovery
- Run a tiny smoke request first.
- Prefer readiness checks over health checks.
- Do not start a large benchmark until the server has accepted a real request.

## Wrong endpoint family

### Symptoms
- A benchmark succeeds but reports nonsensical latency or output lengths.

### Causes
- The script expected `/generate`, but the server was accessed through an
  OpenAI route, or vice versa.

### Recovery
- Match the benchmark script to the endpoint family in the API reference.
- Confirm the benchmark payload structure before running the full scenario.

## Tokenizer or model mismatch

### Symptoms
- Benchmark setup fails while loading the tokenizer or dataset.

### Causes
- The tokenizer path does not match the model checkpoint.
- A Hugging Face dataset or cache is missing.
- The benchmark assumes offline cache variables that are not set.

### Recovery
- Re-check the model directory and tokenizer path.
- Verify whether the benchmark expects online downloads or offline cache mode.
- Keep the benchmark environment variables consistent across runs.

## Proxy leakage

### Symptoms
- Local benchmark calls fail only in the current shell.

### Causes
- Proxy settings still route localhost requests out of the machine.

### Recovery
- Clear proxy variables for the smoke and benchmark shell.
- Add local addresses to `no_proxy`.

## Prompt-cache or PD benchmark oddities

### Symptoms
- Cache-related or PD-related timing spikes dominate the run.

### Causes
- The topology was not warmed up.
- The benchmark did not use the expected service topology.
- The model and cache settings disagree with the benchmark assumptions.

### Recovery
- Revisit the deployment route and the topology reference.
- Use the benchmark catalog to confirm the intended launch order and service
  family.

## Reproducibility issues

### Symptoms
- Two runs with the same label produce different results.

### Causes
- Different input lengths, different tokenizer/model paths, or different
  concurrency settings.
- The benchmark log omitted key environment state.

### Recovery
- Record the exact command, endpoint, model directory, and log directory.
- Keep the benchmark summary file with the raw logs.
