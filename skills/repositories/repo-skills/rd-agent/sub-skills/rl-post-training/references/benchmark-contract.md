# RL and AutoRL-Bench contract

## Run inputs

- agent id and driver model/provider;
- task/benchmark and its extra requirements;
- base model id and model cache/root;
- data root and optional `SMITH_BENCH_DIR`;
- GPU/container/conda backend;
- timeout, step/loop budget, and free local grading port.

## Run artifacts

Keep the isolated workspace, baseline score, every submission score, best score and improvement, agent/grading logs, run metadata, and the global summary row. A baseline or empty score list is not a successful post-training result.

## Benchmark semantics

The runner prepares resources, creates a workspace, starts a grading service, evaluates a baseline, launches the agent, collects scores, and closes the service. Each invocation is an independent evaluation unit. Do not compare runs with different model ids, task versions, evaluator code, or time budgets without recording those differences.

## Blocking evidence

Use `BLOCKED_REQUIRED_BACKEND` when CUDA, a required benchmark package, model weights, or a required external benchmark checkout is unavailable. A CPU import or `--help` result can validate packaging but cannot prove RL training or benchmark execution.
