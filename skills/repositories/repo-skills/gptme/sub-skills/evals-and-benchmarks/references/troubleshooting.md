# Troubleshooting

This reference lists the most common eval and benchmark failures and the safest next check.

## Import and environment problems

### `ModuleNotFoundError` when running `gptme-eval`

Common missing modules include `multiprocessing_logging` or `tabulate`.

What it usually means:

- the installed environment does not include the eval-capable package set,
- the `gptme-eval` entry point is present but the runtime dependencies are incomplete.

Next step:

- verify the package install instead of trying to work around the import,
- use the bundled command builder or result summarizer only after the CLI imports cleanly.

### `gptme-eval --list` fails before listing suites

This happens for the same reason as above: the command imports the eval package before it can print the suite inventory.

Fix:

- repair the local install,
- then retry `gptme-eval --list`.

### `No models configured`

The runner only auto-populates default models when it can see provider credentials.

Fix:

- pass `--model` explicitly, or
- configure the provider keys through the normal configuration path.

This sub-skill does not own provider setup; if the issue is about key storage or model routing, route to configuration-and-providers.

## Docker and isolation problems

### `--use-docker` cannot re-exec

Likely causes:

- Docker daemon is unavailable,
- the eval image cannot be built,
- the checkout is not accessible from the container.

Next step:

- verify Docker first,
- then re-run with a smaller suite and a single model.

### Docker run sees no credentials

The eval runner forwards a fixed set of known provider variables and config-backed values through an internal env file.

If the model still cannot authenticate:

- confirm the credential exists in the normal config path,
- confirm the chosen provider key matches the model prefix,
- do not rely on unrelated shell variables.

### Docker image build is slow or flaky

This is usually a host/network/Docker issue, not an eval bug.

Use:

- a smaller suite,
- a single model,
- an explicit timeout,
- the shortest reproducible command you can build.

## SWE-bench problems

### `--run-harness` fails

The official SWE-bench harness path requires Docker and the benchmark extras.

Safe checklist:

1. run `gptme-eval-swebench --info` first,
2. generate predictions without the harness,
3. enable `--run-harness` only when Docker and the benchmark dependencies are ready.

### Dataset or instance lookup fails

Use `--info` to confirm the dataset name, split, and instance IDs before launching a longer run.

If the dataset is huge or remote access is slow, keep the problem narrow with `-i` and a single instance.

## T-bench problems

### `tb --version` fails

The terminal-bench CLI is missing or unhealthy.

Next step:

- install the benchmark dependency set for the environment,
- retry only after `tb --version` is healthy.

### T-bench support is unavailable in this Python install

The project metadata marks `terminal-bench` with a Python `>=3.12` requirement, so a 3.11 runtime may not expose `gptme-eval-tbench` cleanly.

If the command is unavailable:

- use a compatible benchmark environment,
- do not assume the base gptme install is enough.

## Results and analysis problems

### `No eval results found`

The analysis tools only read local timestamped result files.

Check:

- the directory you passed,
- the `EVAL_RESULTS_DIR` override,
- whether the run actually wrote `eval_results.csv`.

### Trend analysis sees no data

Trend commands expect timestamped directories whose names look like `YYYYMMDD_HHMMSSZ`.

If the timestamps are missing or malformed, the trend logic will skip them.

### The summarizer prints `ignored` rows

That usually means the CSV has malformed or incomplete rows.

Use the summary anyway, then inspect the raw CSV if the ignored count is unexpectedly high.

## Cost, timeout, and scale problems

### Runs are too expensive

Lower the scope before tweaking the model:

- one suite,
- one model,
- one format,
- one timeout,
- one Docker mode.

Then scale up only after that point is stable.

### Tests time out

Next step:

- raise `--timeout`,
- reduce `--parallel`,
- run a smaller suite,
- choose a faster model for the diagnostic pass.

### Pass rates look inconsistent

Check whether the two runs differed in any of these:

- Docker mode,
- tool format,
- timeout,
- `--parallel`,
- `--no-lessons`,
- pass-rate gate file,
- provider or provider-side routing.

## Maintainer-only checkout tasks

These tasks are valid benchmark maintenance work, but they should be done from a gptme checkout and only when the benchmark budget is explicit:

- rebuilding the eval image,
- publishing or refreshing result branches,
- running the full benchmark matrix,
- mass-updating benchmark artifacts.

If the issue is only about reading results, use the bundled helper scripts instead of rebuilding anything.
