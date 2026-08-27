# Petals Cross-Cutting Troubleshooting

Use this reference for failures spanning client code, server operation, prompt tuning, adapters, benchmarks, and environment setup. Route workflow-specific issues to the nearest sub-skill troubleshooting reference.

## Local package import fails

- Confirm an isolated environment and supported Python version.
- Run `python -m pip check` and print `petals.__version__` plus `transformers.__version__`.
- Petals snapshot `2.3.0.dev2` expects Transformers `>=4.43.1,<4.44.0`.
- If an older Hivemind build fails on `pkg_resources`, constrain build-time setuptools for that install step.
- Normal base import should not need `bitsandbytes`; if it does, inspect why a quantization/adapter path was imported.

## Public swarm or model access fails

- Separate local import health from remote access by running the safe checker first.
- Confirm model architecture support and Hugging Face gated-model access.
- Bound retry loops while debugging, for example with `PETALS_MAX_RETRIES=10`.
- For a private swarm, verify consistent `initial_peers`, `dht_prefix`, model identifier, and block ranges across clients and servers.
- For the public swarm, check whether the requested model is currently hosted and whether remote availability changes are acceptable.

## Generation/session errors

- Without an active session, pass exactly one of `max_new_tokens` or `max_length`.
- For interactive generation, reserve enough total cache with `model.inference_session(max_length=...)`, then reuse `generate(..., session=session)` or `generate(None, ...)`.
- Keep attention masks absent or all ones unless the selected Petals path explicitly supports the requested mask.
- Avoid relying on resumed-session beam search without checking the warning and behavior for the exact model.

## Server backend or quantization fails

- Treat quantization/adapters as optional backend features until verified.
- Run a tiny Torch backend smoke separately from bitsandbytes.
- If bitsandbytes is incompatible, use `--quant_type none` or repair the Torch/CUDA/Triton/bitsandbytes version set.
- Do not use a CPU import as evidence that quantized GPU serving works.

## Disk/cache and native checks

Pick a cache directory with enough space before launching long-running servers, use `--max_disk_space` where appropriate, preserve cache failure evidence, and verify credentials before treating cache misses as package bugs. Multi-process native checks need model variables, private peers, explicit timeouts, and cleanup traps; tiny CPU benchmark numbers are wiring health only.

## Continue in sub-skills

- Client code and `.generate()`: [../sub-skills/client-inference/references/troubleshooting.md](../sub-skills/client-inference/references/troubleshooting.md)
- Server/DHT CLI: [../sub-skills/server-swarms/references/troubleshooting.md](../sub-skills/server-swarms/references/troubleshooting.md)
- Prompt tuning/adapters: [../sub-skills/prompt-tuning/references/troubleshooting.md](../sub-skills/prompt-tuning/references/troubleshooting.md)
- Block internals: [../sub-skills/distributed-blocks/references/troubleshooting.md](../sub-skills/distributed-blocks/references/troubleshooting.md)
- Benchmarks/native checks: [../sub-skills/benchmarks-maintenance/references/troubleshooting.md](../sub-skills/benchmarks-maintenance/references/troubleshooting.md)
