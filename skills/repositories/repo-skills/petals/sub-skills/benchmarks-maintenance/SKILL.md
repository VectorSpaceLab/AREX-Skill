---
name: benchmarks-maintenance
description: "Construct safe Petals benchmark command templates, choose tiny
  private-swarm maintenance smokes, route focused native checks, and interpret
  benchmark health signals without launching expensive workflows by default."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Petals Benchmarks and Maintenance

Use this sub-skill for Petals benchmark command construction, tiny smoke benchmarks, focused native maintenance checks, or CI-style private CPU swarm upkeep. Prefer safe command templates and checklists; do not launch benchmarks, model downloads, training-like loops, DHT peers, or server processes unless the user explicitly approves runtime, network, cache, and cleanup constraints.

Read [references/benchmarking.md](references/benchmarking.md), [references/native-smoke-tests.md](references/native-smoke-tests.md), and [references/troubleshooting.md](references/troubleshooting.md). Use `python scripts/build_benchmark_command.py --help` to print commands. The builder targets the bundled runner `scripts/run_petals_benchmark.py`, which should be executed only after approval.

Route production server launch design to `server-swarms`, client generation to `client-inference`, prompt-tuning APIs to `prompt-tuning`, and low-level block correctness to `distributed-blocks`.
