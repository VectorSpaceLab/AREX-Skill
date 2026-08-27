---
name: rd-agent
description: "Operate Microsoft's RD-Agent research-agent framework for
  data-science, quantitative-finance, LLM fine-tuning, reinforcement-learning,
  and paper/model-copilot workflows."
metadata:
  disco-role: operating
  source-repository: microsoft/RD-Agent
  source-revision: 6762f84f9bc0f5c6486c50a00e128a57ac6c3683
  package: rdagent
license: MIT
disable-model-invocation: true
---

# RD-Agent

Use this skill when a task involves the **RD-Agent** Python package or a checkout of the `microsoft/RD-Agent` repository. RD-Agent is an agentic research framework, not a single model: it composes LLM calls, code generation, execution, evaluation, and experiment logs around several scenario families.

## Route first

Choose the smallest sub-skill that covers the user's requested workflow:

| Request shape | Read next |
|---|---|
| Install, environment checks, CLI help, UI/server startup, logs, config discovery, or safe maintenance | [setup-and-ops](sub-skills/setup-and-ops/SKILL.md) |
| Qlib factors, factor reports, quantitative research, backtests, or finance data-agent/model-agent flows | [quant-finance](sub-skills/quant-finance/SKILL.md) |
| Kaggle-style tabular work, data-science agent loops, dataset preparation, or competition artifacts | [competition-data-science](sub-skills/competition-data-science/SKILL.md) |
| LLM fine-tuning datasets, training jobs, merge/evaluation, or fine-tune UI | [llm-finetune](sub-skills/llm-finetune/SKILL.md) |
| AutoRL-Bench, RL scenario loops, benchmark agents, or post-training experiments | [rl-post-training](sub-skills/rl-post-training/SKILL.md) |
| General model copilot, paper-driven model exploration, or reusable model-research scaffolding | [paper-model-copilot](sub-skills/paper-model-copilot/SKILL.md) |

For a mixed request, read the relevant sub-skills in the order **setup → domain workflow → evaluation/troubleshooting**. Do not load every sub-skill by default.

## Operating model

1. **Establish the runtime.** Confirm Python is supported (the inspected project supports Python 3.10 and 3.11), the package is importable, and the requested command is available. For a checkout, install with `python -m pip install -e .`; for an installed distribution, use the package's normal environment. Keep API keys, data roots, model caches, and experiment outputs outside the skill tree.
2. **Select the scenario.** RD-Agent's public CLI exposes `data_science`, `fin_quant`, `fin_factor_report`, `llm_finetune`, `general_model`, `ui`, `server_ui`, and `ds_user_interact`. The RL benchmark entry point is `python -m rdagent.scenarios.rl.autorl_bench.run`.
3. **Make configuration explicit.** Prefer an existing example or scenario config, then override only the values needed for the task. Record dataset paths, model/provider settings, execution sandbox, output directory, and evaluation metric before launching an agent loop.
4. **Run the smallest smoke check.** Use `--help`, import checks, or a tiny fixture before a long experiment. Do not infer a successful experiment from process startup: inspect the generated summary, evaluator result, and logs.
5. **Preserve evidence.** Save the command, resolved configuration, commit/package version, metric definitions, and failure traceback with the experiment. Keep generated code and datasets in a separate run directory.

## Common preflight

```bash
python -c "import rdagent; print(rdagent.__file__)"
rdagent --help
rdagent health_check --no-check-env --no-check-docker
```

The health check can inspect Docker and external tools when those checks are enabled. Use the explicit `--no-check-*` flags only for a lightweight package/CLI smoke test; do not treat that result as proof that a containerized or GPU-backed workflow is ready.

## Safety and scope boundaries

- Agent loops can generate and execute code. Start with a disposable output directory and a restricted execution environment.
- Finance, Kaggle, model-training, and RL scenarios may require credentials, large datasets, Docker, CUDA, or external services. State those prerequisites instead of silently substituting a CPU or toy result.
- Avoid launching full training, benchmark servers, UI processes, or network downloads as a generic smoke test. Use the bundled helper scripts for deterministic checks.
- `fitz` may emit a deprecation warning: use of the warning alone is not a failure. AutoRL-Bench may report an empty registry when `SMITH_BENCH_DIR` is unset or points to a missing benchmark checkout.
- Never place provider keys, cookies, competition credentials, private data, or local absolute paths in a generated report or a reusable configuration.

## Evidence map

- [Package and CLI overview](references/package-overview.md) — public entry points and component boundaries.
- [Troubleshooting](references/troubleshooting.md) — failure classification and recovery sequence.
- [Provenance](references/repo-provenance.md) — source revision and inspection evidence.
- [Routing metadata](references/repo-routing-metadata.json) — scenario routing for the managed repo-skills router.

## Completion checklist

Before calling a task complete, report:

- the selected sub-skill and command/config used;
- environment and backend assumptions (CPU, CUDA, Docker, external data, or credentials);
- the output/evidence directory and the primary metric or artifact;
- any warnings, blocked prerequisites, or unverified capabilities;
- whether the run was a smoke check, a partial experiment, or a full result.
