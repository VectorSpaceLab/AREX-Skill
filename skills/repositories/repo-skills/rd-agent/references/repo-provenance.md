# RD-Agent repo-skill provenance

## Source

- Repository: `microsoft/RD-Agent`
- Origin observed during production: `https://github.com/microsoft/RD-Agent.git`
- Source revision: `6762f84f9bc0f5c6486c50a00e128a57ac6c3683`
- Branch observed: `main`
- Package import name: `rdagent`
- Package version observed in the inspection environment: `0.1.dev1`
- Production timestamp: `2026-08-11T18:56:14Z`

The production checkout's tracked source tree was clean at the time provenance was recorded. Generated skill and verification artifacts live under the repository's ignored `skills/` area and are intentionally not part of source provenance.

## Evidence inspected

The skill was distilled from repository-owned material, including:

- `README.md`, `.env.example`, `pyproject.toml`, `requirements.txt`, `constraints/3.10.txt`, `constraints/3.11.txt`, and `requirements/*.txt`.
- Documentation under `docs/`, especially installation/configuration, UI, API reference, scenario catalog, and scenario-specific pages for data science, quant finance, fine-tuning, and model copilot.
- CLI and app modules under `rdagent/app/`, including `cli.py`, `main.py`, `utils/health_check.py`, data-science, Kaggle, Qlib, fine-tune, RL, and general-model modules.
- Scenario modules under `rdagent/scenarios/`, including data-science, Kaggle, Qlib experiment templates, fine-tuning datasets/training/benchmark utilities, and AutoRL-Bench.
- Component configuration and evaluator modules under `rdagent/components/` and logging helpers under `rdagent/log/`.

## Runtime evidence

A private inspection environment was prepared during production to prove the package and CLI surface. The reusable skill does not depend on that environment or expose its local paths.

Recorded smoke evidence included:

- `python -m pip check`
- `import rdagent`, `import rdagent.app.cli`, and selected scenario/component imports
- `rdagent --help`
- `rdagent health_check --no-check-env --no-check-docker`
- `rdagent data_science --help`
- `rdagent fin_quant --help`
- `rdagent fin_factor_report --help`
- `rdagent llm_finetune --help`
- `rdagent general_model --help`
- `rdagent ui --help`
- `rdagent server_ui --help`
- `rdagent ds_user_interact --help`
- `python -m rdagent.scenarios.rl.autorl_bench.run --help`

Non-fatal warnings observed during inspection:

- `fitz` deprecation warning recommending `pymupdf`.
- AutoRL-Bench warning that a configured Smith benchmark directory was missing, yielding an empty registry.

## Verification artifacts

Production and verification artifacts are stored outside the runtime skill tree under `skills/tests/rd-agent/` in this checkout. Runtime instructions deliberately avoid absolute local paths so the skill can be reused with other RD-Agent checkouts or installations.
