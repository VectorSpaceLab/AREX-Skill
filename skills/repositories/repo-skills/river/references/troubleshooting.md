# Cross-Cutting Troubleshooting

## When to read

Read this when River fails to install, import, build from source, or run a minimal online-learning smoke test. Workflow-specific issues live in each sub-skill's `references/troubleshooting.md`.

## Install and build failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: river` | River is not installed in the Python environment running the code. | Install with `pip install river`, or install the current checkout with an editable install when doing repo maintenance. Re-run `scripts/check_river_environment.py`. |
| Rust extension modules such as `river._river_rust.stats` fail to import | Source build did not compile the maturin extension, or a wheel for the active Python/platform is missing. | Prefer a released wheel for normal package use. For source installs, make sure maturin can use a Rust toolchain, then reinstall River and run the environment check. |
| Build fails around `maturin`, `cargo`, or Rust compiler discovery | Source checkout install needs Rust build tooling. | Install a Rust toolchain in the build environment or switch to a prebuilt River wheel. Do not claim source-build verification until the Rust modules import. |
| Importing `river.stream` fails on an older Python with `csv.DictReader` generic errors | The checkout uses typing syntax that may require a newer Python than a nominal lower bound suggests. | Use a newer supported Python and rerun import checks, or refresh this skill after upstream metadata/code changes. This skill was verified with Python 3.13. |
| Mini-batch methods fail with missing `pandas` | `learn_many`, `predict_many`, `predict_proba_many`, and `transform_many` use pandas objects. | Install the optional pandas support (`pip install "river[pandas]"`) or rewrite the workflow to use one-sample `*_one` methods. |
| Optional stream adapters fail for SQL, sklearn, polars, or external services | Optional dependency is absent or the service/client is not configured. | Install only the adapter dependency required by the chosen workflow. For ordinary CSV/array/dict streams, avoid optional adapters. |

## Runtime smoke checks

Run the bundled root check after installation or after changing Python versions:

```sh
python scripts/check_river_environment.py --samples 20
```

Expected signals:

- The script prints `river_version=...`.
- Imports for core modules and Rust extension modules print `import_ok=...`.
- The quickstart loop prints a sample count and an accuracy value.

Use `--skip-rust` only when you are deliberately checking a partial, source-tree-only import. Do not treat a skipped Rust check as full package verification.

## Data and API pitfalls

- River expects feature dictionaries for most `*_one` methods. If your data is an array or dataframe, route through `stream.iter_array`, `stream.iter_pandas`, `stream.iter_frame`, or convert rows to dictionaries.
- Many models can produce `None` or an empty probability dictionary before seeing enough labels. Update metrics only when the prediction is usable, or use `evaluate.progressive_val_score`, which already handles the common paths.
- Metrics must match model output type. Probability metrics need `predict_proba_one`; label metrics need labels; clustering metrics receive cluster ids; anomaly metrics often need scores.
- River generally follows Python's EAFP style and avoids heavy input validation. Bad feature types or target labels may fail inside a model rather than at a separate validation layer.

## When to switch references

- For estimator contracts, read `sub-skills/online-core-api/references/troubleshooting.md`.
- For pipeline feature flow, read `sub-skills/pipelines-and-features/references/troubleshooting.md`.
- For stream parsing and metrics, read `sub-skills/streaming-evaluation/references/troubleshooting.md`.
- For supervised model choice and wrappers, read `sub-skills/supervised-models/references/troubleshooting.md`.
- For drift, anomaly, clustering, time series, bandits, recommenders, or imbalanced learning, read `sub-skills/specialized-workflows/references/troubleshooting.md`.
