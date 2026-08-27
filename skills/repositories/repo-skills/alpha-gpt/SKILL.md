---
name: alpha-gpt
description: "Route AlphaGPT data ingestion, factor mining, live strategy, and
  dashboard workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlphaGPT

Use this repo skill for the AlphaGPT crypto-quant system. It helps future agents
work with the repository's four main workflows without reopening the source tree
for basic navigation:

- data ingestion from Birdeye/DexScreener into Postgres/Timescale
- factor-token mining, StackVM formula execution, and training artifacts
- live strategy, risk, portfolio state, and Solana/Jupiter execution
- Streamlit dashboard monitoring and local fixture generation

## Start here

1. Read [references/repo-provenance.md](references/repo-provenance.md) when you need to check whether this skill still matches the current AlphaGPT checkout or before a refresh.
2. Read [references/install-and-operations.md](references/install-and-operations.md) for the public install baseline, dependency pin note, environment expectations, and safe import check.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting import, dependency, credential, DB, and live-operation failures.
4. Read [references/experiments-and-exclusions.md](references/experiments-and-exclusions.md) for optional research scripts and explicit exclusions.
5. Run [scripts/alpha_gpt_env_check.py](scripts/alpha_gpt_env_check.py) when you want an offline, no-network preflight across env vars, files, and imports.

## Route map

- [data-pipeline](sub-skills/data-pipeline/SKILL.md): OHLCV ingestion, provider config, DDL preview, and safe preflight checks.
- [factor-mining](sub-skills/factor-mining/SKILL.md): feature engineering, formula grammar, StackVM execution, backtest scoring, and training artifacts.
- [live-strategy](sub-skills/live-strategy/SKILL.md): strategy runner, portfolio state, risk controls, and guarded Solana/Jupiter execution.
- [dashboard-ops](sub-skills/dashboard-ops/SKILL.md): Streamlit dashboard, read-only state inspection, and local fixture generation.

## Public baseline

- Install from the repository root with `python -m pip install -r requirements.txt`.
- The source tree is not packaged as a `pyproject.toml`/`setup.py` distribution, so use the checkout itself as the import root when validating a local clone.
- If `execution.trader` fails on the newest Solana wheel because `TokenAccountOpts` is missing, consult the live-strategy troubleshooting notes for the verified `solana==0.36.12` and `websockets==15.0.1` compatibility pin.
- Core runtime facts were verified from the current source: source import roots are `data_pipeline`, `model_core`, `execution`, `strategy_manager`, and `dashboard`.

## Minimal import check

From a checkout that is on `PYTHONPATH` or otherwise visible to the environment, a safe smoke check is:

```bash
python -I -c "import data_pipeline, model_core, execution, strategy_manager, dashboard"
```

If you need a deeper no-network preflight, use the bundled env checker instead of touching databases, RPC endpoints, or wallets.

## What this skill does not do automatically

- It does not start the live strategy runner.
- It does not fetch Birdeye data or write Postgres rows as a default check.
- It does not submit Solana transactions.
- It does not launch Streamlit for you.
- It does not install optional research dependencies from `requirements-optional.txt` unless you explicitly choose the optional research workflows.

## Safe reading order for common tasks

- "Why is no market data showing up?" -> data-pipeline troubleshooting.
- "How do I inspect or validate a formula?" -> factor-mining references and smoke script.
- "How do I configure the bot safely?" -> live-strategy reference and offline config checker.
- "Why is the dashboard empty?" -> dashboard-ops reference and fixture generator.

## Notes for later refreshes

- Read `references/repo-provenance.md` and compare the current checkout before deciding whether to refresh this skill.
- If the repository adds package metadata, new workflows, or additional service/backends, route those through a refresh rather than widening the existing instructions silently.
