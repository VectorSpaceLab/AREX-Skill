---
name: quant-finance
description: "Run and troubleshoot RD-Agent quantitative-finance factor and
  model workflows backed by Qlib, including factor-report and co-optimization
  loops."
metadata:
  disco-role: operating
  parent-skill: rd-agent
license: MIT
disable-model-invocation: true
---

# RD-Agent quantitative finance

Use this sub-skill for RD-Agent(Q), factor generation, factor reports, Qlib model research, finance data-agent/model-agent loops, and backtest interpretation.

## Choose the workflow

- `rdagent fin_quant` is the finance quant agent entry point for factor/model co-optimization.
- `rdagent fin_factor_report` is the inspected CLI entry point for factor-report-driven workflows. Run `--help` in the active version before using it; older documentation may call the flow `fin_factor`.
- Read the Qlib experiment templates and the active scenario config before changing dates, provider paths, model, or evaluator settings.

A typical safe sequence is:

```bash
rdagent fin_quant --help
rdagent fin_factor_report --help
# inspect the resolved configuration and data path
# run a tiny/debug iteration before a full loop
```

## Data and split contract

The documented defaults use local Qlib data (commonly `~/.qlib/qlib_data/cn_data`), the CSI300 universe, and `SH000300` as benchmark. The reference templates use chronological splits around 2008–2014 for training, 2015–2016 for validation, and 2017–2020 for test/backtest. Treat those values as template evidence, not universal defaults: record the actual provider URI, market, benchmark, dates, and timezone used by the run.

Factor-agent loop:

1. formulate a financially motivated hypothesis;
2. implement a factor with a name, description, formula, and variables;
3. evaluate it on the configured data;
4. combine new factors with the baseline feature set and run the model/backtest;
5. inspect signal and portfolio records;
6. use feedback to refine the next hypothesis.

Model-agent loop follows the same evidence discipline but may read a report/paper and generate model code. Do not compare runs if the universe, date split, transaction costs, or evaluator changed.

## Backtest hygiene

- Check chronological ordering and fit/validation/test boundaries before evaluating.
- Record the feature source, missing-value/normalization pipeline, model seed, `n_jobs`, device, and transaction-cost assumptions.
- Treat `SignalRecord`, signal analysis, and portfolio analysis as separate artifacts.
- Investigate leakage, survivorship bias, look-ahead features, and accidental test-set use before celebrating a metric.
- A generated factor that imports successfully is not a validated factor; require evaluator output and a reproducible artifact.

Read [qlib-contract.md](references/qlib-contract.md) for the template/data/evaluation contract. Use [the parent troubleshooting guide](../../references/troubleshooting.md) for provider, generated-code, and evaluator failures.
