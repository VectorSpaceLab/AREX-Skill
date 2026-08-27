# RD-Agent package and CLI overview

## Package shape

The public package is `rdagent`. The inspected source groups user-facing flows under `rdagent.app` and reusable scenario implementations under `rdagent.scenarios`; shared agent, coder, evaluator, configuration, logging, and execution pieces live under `rdagent.components`, `rdagent.core`, and `rdagent.log`.

Important application modules:

- `rdagent.app.cli` — Typer-based command surface and command registration.
- `rdagent.app.data_science` — data-science loop and configuration.
- `rdagent.app.kaggle` — competition-oriented loop.
- `rdagent.app.qlib_rd_loop` — quantitative factor/model loops and report-to-factor flow.
- `rdagent.app.finetune` — data-science and LLM fine-tuning orchestration.
- `rdagent.app.rl` — RL loop entry point.
- `rdagent.app.general_model` — general-model and model-copilot flow.
- `rdagent.app.utils.health_check` — environment and optional Docker checks.

## CLI entry points

The package exposes the `rdagent` executable. The stable top-level commands observed in the inspected revision are:

```text
health_check
ui
server_ui
data_science
ds_user_interact
fin_quant
fin_factor_report
llm_finetune
general_model
```

The exact options are version-sensitive. Always run `rdagent <command> --help` in the active environment before composing a long command. The skill's examples intentionally use help and health-check commands rather than embedding credentials or machine-specific paths.

## Scenario boundaries

- **Data science / Kaggle:** generate or refine code against a tabular or structured-data task, then evaluate with the scenario's configured metric and artifact layout.
- **Quant finance:** factors and models are evaluated through Qlib-oriented experiment templates; data availability and leakage control are part of the result, not optional setup.
- **Fine-tuning:** dataset preparation, job configuration, training/merge/evaluation, and UI summaries are separate phases. A successful job submission is not a validated checkpoint.
- **RL post-training:** AutoRL-Bench has its own registry and optional benchmark checkout. An empty registry warning can be a missing benchmark root, not an agent failure.
- **General model / paper copilot:** use this for model-research scaffolding and general model generation; it is not a replacement for a domain-specific evaluator.

## Configuration principles

1. Start from the scenario's checked-in example or config object.
2. Make the LLM/provider, dataset, execution backend, and evaluator explicit.
3. Keep outputs in a run-specific directory and preserve the resolved configuration.
4. Separate orchestration errors, generated-code errors, evaluator failures, and data/credential failures in the report.
5. Re-run a deterministic tiny fixture before retrying a long loop.
