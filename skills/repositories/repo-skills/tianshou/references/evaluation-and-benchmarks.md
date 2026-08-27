# Evaluation and Benchmarks

## Safe Evaluation Path

Tianshou's evaluation utilities cover experiment launching and rliable-based multi-run analysis. Treat them as a separate workflow from first-pass training smokes.

Use this order:

1. Build or load one tiny experiment and prove it can run with one seed.
2. Disable rendering and keep output directories explicit.
3. Use `SequentialExpLauncher` before `JoblibExpLauncher` so failures are easier to inspect.
4. Increase seeds/env steps only after the one-seed workflow is stable.
5. Run rliable aggregation only after logged experiment directories contain comparable train/test data.

## Public Utilities

| Utility | Use |
| --- | --- |
| `ExpLauncher` | Base launcher abstraction for experiment collections. |
| `SequentialExpLauncher` | Safe first launcher; runs experiments serially. |
| `JoblibExpLauncher` | Parallel launcher using joblib when multi-process execution is deliberate. |
| `JoblibConfig` | Controls `n_jobs`, backend, and verbosity for joblib launch. |
| `RegisteredExpLauncher` | Enum for registered launcher creation. |
| `load_and_eval_experiment` and rliable helpers | Load logged results and compute aggregate/plot outputs. |

## Benchmark Guardrails

The repository includes benchmark evidence and launcher scripts, but benchmark-scale workflows are not smoke tests. Before adapting a benchmark request:

- Confirm optional dependencies for the environment family.
- Confirm where logs/results should be written.
- Reduce to one algorithm, one environment, one seed, and tiny step counts.
- Avoid external dataset or ROM downloads unless explicitly authorized.
- Do not assume GPU availability; make device selection explicit.

## When to Route Elsewhere

- Use `sub-skills/highlevel-experiments/SKILL.md` for persisted high-level `Experiment` construction and normal `.run()` usage.
- Use `sub-skills/procedural-training/SKILL.md` for trainer and algorithm objects that produce evaluation results.
- Use `sub-skills/offline-and-specialized-rl/SKILL.md` for rliable imports, multi-seed planning, offline benchmark datasets, and benchmark safety.
- Use `sub-skills/envs-and-vectorization/SKILL.md` for optional environment engines such as MuJoCo, Atari, EnvPool, VizDoom, Box2D, and PettingZoo.

## Validation Signals

A bounded evaluation plan is ready only when:

- The package import smoke passes.
- The task environment can reset/step in a vector env.
- The algorithm/trainer construction smoke passes.
- The expected logged directory shape is documented.
- The requested optional evaluation dependencies import.
- The run budget is explicit enough to avoid accidental benchmark-scale execution.
