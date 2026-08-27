# Qlib workflow contract

## Inputs to make explicit

- Qlib provider URI and whether the local dataset is initialized.
- Market/universe and benchmark.
- Feature/factor sources, including any parquet or generated factor library.
- Train/validation/test dates and timezone.
- Model, seed, device, batch size, epochs, and worker count.
- Backtest strategy, capital, fees, slippage, and evaluator metric.

## Outputs to preserve

- Resolved YAML/config object.
- Generated factor/model source and its description.
- Import/syntax/evaluator logs.
- Signal, signal-analysis, and portfolio-analysis records when produced.
- A short comparison against the baseline with identical data and costs.

## Default-template clues

The checked-in examples describe Alpha158-style features, normalization/fill operations, Qlib models, CSI300/SH000300, and chronological dates. Use these only as a starting point. Verify the current template because data layout and model support can change between revisions.

## Stop conditions

Stop and report a blocked prerequisite when Qlib data is absent, the chosen evaluator cannot run on the available backend, or the result uses a different split/cost protocol than the baseline. Do not replace missing market data with synthetic random prices and call it a finance result.
