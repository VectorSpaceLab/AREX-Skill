# Experiments And Exclusions

## Purpose

This reference explains which AlphaGPT repository artifacts informed the skill
only as background and which were excluded from the selected operating graph.
Use it when a future task asks whether optional scripts should be installed,
ported, or covered by a refresh.

## Selected main system

The generated skill covers the repository's main crypto-quant pipeline:

1. `data_pipeline/` fetches Solana meme-token data and writes Postgres/Timescale tables.
2. `model_core/` mines formula-token factors and writes strategy artifacts.
3. `strategy_manager/` consumes a formula, monitors positions, and applies risk rules.
4. `execution/` wraps Solana RPC and Jupiter quote/swap/sign/send operations.
5. `dashboard/` displays local portfolio, market snapshot, logs, and STOP control.

## Reference-only or excluded artifacts

| Artifact | Decision | Why |
| --- | --- | --- |
| `lord/experiment.py` | Reference-only optional experiment | It demonstrates LoRD-style low-rank regularization with modular-addition experiments, long training, and plot outputs. The main model already includes LoRD classes, so this script is not needed for normal AlphaGPT operation. |
| `times.py` | Excluded from main skill | It targets Chinese-market/Tushare data, contains a hardcoded Tushare token, performs network fetches and cache writes, and uses optional visualization dependencies. It is a separate experiment rather than the crypto live-trading pipeline. |
| `requirements-optional.txt` | Skipped by default | Its dependencies support the optional experiments, not the selected main workflows. Install it only when a user explicitly selects those experiments. |
| `paper/20251226.pdf` | Excluded / separate paper workflow | The PDF is binary research material. If a user asks to distill the paper itself, use a paper-skill workflow rather than widening this repo skill. |
| `assets/`, `showcase.png`, `helpme.jpg` | Excluded | Images do not expose APIs, commands, or reusable operating procedures for the generated skill. |

## If a user asks about the excluded experiments

- Confirm whether they want to run optional research scripts or refresh the repo skill to include them.
- Warn that `times.py` uses external Tushare access and a hardcoded token in source; do not publish or reuse secret-like values.
- Install `requirements-optional.txt` only in an isolated environment and only after confirming network/data permissions.
- Prefer tiny-step CPU dry runs for `lord/experiment.py` before full phase diagrams or mechanism analysis.
- Keep optional experiment artifacts separate from live-trading artifacts such as `best_meme_strategy.json` and `portfolio_state.json`.
