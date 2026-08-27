---
name: rl-post-training
description: "Run and troubleshoot RD-Agent RL post-training and AutoRL-Bench
  experiments with explicit model, benchmark, workspace, grading, and backend
  evidence."
metadata:
  disco-role: operating
  parent-skill: rd-agent
license: MIT
disable-model-invocation: true
---

# RD-Agent RL post-training

Use this sub-skill for `rdagent` RL post-training, `autorl_bench`, agent-driven GRPO/RL experiments, benchmark grading servers, and result collection.

## Pick the surface

### RL post-training loop

The application entry point accepts a base model, benchmark, step/loop counts, and an overall timeout. The implementation can evaluate a baseline during scenario initialization and then run iterative training. Make the model/data directories and backend explicit before launching:

```bash
python rdagent/app/rl/loop.py \
  --base-model <model-name> \
  --benchmark <benchmark> \
  --loop-n 1 \
  --timeout <bounded-duration>
```

Use the active CLI help or module source to confirm optional flags. The scenario may need GPU, Docker/conda environments, model weights, and benchmark data.

### AutoRL-Bench

Probe without running a benchmark:

```bash
python -m rdagent.scenarios.rl.autorl_bench.run --help
```

A real run requires an agent id, task, base model, and timeout. It may download model/data assets and starts a local grading server:

```bash
python -m rdagent.scenarios.rl.autorl_bench.run \
  --agent example_agent \
  --task gsm8k \
  --model <huggingface-model-id> \
  --timeout <seconds> \
  --port <free-local-port>
```

Use `example_agent` and a tiny supported task only as a pipeline smoke test when the required assets are already available; do not call a long run a smoke test if it downloads gigabytes or trains a model.

## Workspace and result contract

Each AutoRL-Bench run gets an isolated workspace under the scenario workspace root. The runner prepares model/data links, starts a grading server, records baseline and submissions, writes run logs and scores, and appends a summary row to `results.csv`. Preserve the workspace path, `run.log`, `agent.log`, `scores.json`, baseline, best score, submission count, timeout, and success flag.

Important environment/configuration signals include `AUTORL_FILE_PATH`, `AUTORL_RDAGENT_ROOT`, `SMITH_BENCH_DIR`, and provider variables for the driver agent. The default resource root is a git-ignored `git_ignore_folder/rl_files` relative to the checkout; override it rather than storing weights in source control.

## Backend and data boundaries

- Model execution and realistic training normally require CUDA, compatible PyTorch/TRL/vLLM/OpenCompass-style dependencies, and enough disk.
- Some benchmarks require extra packages or Java; install only the benchmark-specific requirements for the selected task.
- Missing `SMITH_BENCH_DIR` can produce an empty Smith registry warning. Confirm registry discovery before interpreting it as “no benchmark.”
- Interrupts should terminate the whole child process group and preserve the workspace; inspect logs before restarting on a new port.

Read [benchmark-contract.md](references/benchmark-contract.md) and the parent troubleshooting guide before a run.
