# Cross-Cutting FLA Troubleshooting

Use this before selecting a deeper route when the failure surface is unclear.

## Start with the surface

| Symptom family | First route |
| --- | --- |
| `fla`, `torch`, `triton`, CUDA, ROCm, XPU, NPU, TileLang, FlashKDA, or env-var setup fails. | `../sub-skills/setup-and-backends/SKILL.md` |
| Operator call shape, state, varlen, dispatch fallback, Triton compilation, NaNs, or gradient mismatch. | `../sub-skills/ops-kernels-and-dispatch/SKILL.md` |
| Layer/model/config construction, Hugging Face auto registration, generation, training, evaluation, fused losses. | `../sub-skills/layers-and-models/SKILL.md` |
| KDA-specific gate/beta/safe-gate, FlashKDA, TileLang KDA, or context-parallel issue. | `../sub-skills/kda-and-context-parallel/SKILL.md` |
| Benchmark gate fails, speedup is noisy, op missing from registry, profiler handoff, benchmark JSON. | `../sub-skills/benchmarking-and-optimization/SKILL.md` |

## Fast triage commands

Run these from the generated skill directory or the owning sub-skill directory. They do not download data, train, or run native tests.

```bash
python sub-skills/setup-and-backends/scripts/check_fla_runtime.py --show-env-vars
python sub-skills/ops-kernels-and-dispatch/scripts/inspect_fla_ops.py --filter kda
python sub-skills/layers-and-models/scripts/smoke_layer_model.py --device cpu
python sub-skills/kda-and-context-parallel/scripts/smoke_kda.py --help
python sub-skills/benchmarking-and-optimization/scripts/fla_verify_op_command.py --op chunk_gla
```

If a script path is shown inside a sub-skill, run it from that sub-skill directory as `python scripts/<helper>.py ...`.

## Common root causes

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Bare install imports poorly or lacks `torch`/`triton` | Backend dependencies are not base deps. | Install the intended backend extra and matching PyTorch wheel family. |
| CUDA unavailable after installing CUDA extra | Driver/runtime mismatch, wrong wheel, or CUDA hidden by environment. | Check `torch.cuda.is_available()`, device count, wheel suffix, and environment variables before touching FLA code. |
| Optional backend not selected | Package missing, env gate disabled, env var set too late, or verifier rejected the call. | Set env vars before Python starts, check optional package importability, and compare with dispatch disabled. |
| CPU smoke passes but kernel task fails | CPU is import/config-only for many FLA capabilities. | Use a backend-capable environment for operator, layer forward, KDA, or benchmark verification. |
| `AutoModelForCausalLM` cannot build an FLA config | FLA models not imported/registered, optional dependency missing, or config invalid. | Import config from `fla.models`, use tiny no-fused config first, and avoid hybrid attention unless dependencies are installed. |
| Benchmark speedup has a red gate | Correctness failed before timing. | Do not promote the speedup; fix correctness and rerun full gate. |
| KDA optional acceleration silently falls back | FlashKDA/TileLang/intra-card verifier constraints not satisfied. | Route to KDA troubleshooting and inspect dtype, shape, inference mode, `safe_gate`, `lower_bound`, state layout, and CP context. |

## Safety boundaries

- Do not run training, evaluation, checkpoint downloads, long benchmarks, or distributed context-parallel jobs as smoke checks.
- Do not mutate a user's environment to repair backend wheels without permission; use a private environment or ask.
- Do not change tests, references, tolerances, precision, or public APIs to make a failure disappear.
- Do not import optional backend packages just because hardware exists; install only the variant needed by the task.
