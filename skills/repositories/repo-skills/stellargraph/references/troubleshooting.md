# Cross-Cutting Troubleshooting

## When to read

Read this when StellarGraph import, installation, optional dependency, TensorFlow,
GPU, dataset-cache, or Neo4j failures affect more than one workflow. For
workflow-specific shape, generator, split, or model failures, also read the
nearest sub-skill troubleshooting file.

## Python and package installation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ERROR: Package 'stellargraph' requires a different Python` or TensorFlow wheels cannot resolve | StellarGraph metadata targets Python `>=3.6,<3.9`; modern Python versions are usually unsupported for this package line. | Use a Python 3.8 or 3.7 environment. Then install `stellargraph` and rerun the root environment check script. |
| `ModuleNotFoundError: No module named 'stellargraph'` | Package is not installed in the active Python. | Run `python -m pip install stellargraph` in the same environment that will execute the workflow. Confirm with `python -c "import stellargraph as sg; print(sg.__version__)"`. |
| `ModuleNotFoundError: No module named 'tensorflow'` during `import stellargraph` | TensorFlow dependency is absent or installation was incomplete. | Reinstall `stellargraph` into a supported Python environment; if installing from a local checkout, install its runtime dependencies too. Run `python -m pip check`. |
| Import errors mentioning `typing_extensions`, `protobuf`, `numpy`, or `keras` | Mixed modern packages with an older TensorFlow/StellarGraph stack. | Prefer a clean supported Python environment instead of upgrading packages in place. Pin old-package-compatible versions only after checking `pip check`. |

## Safe environment smoke check

Use the bundled root diagnostic before deeper workflow work:

```bash
python scripts/check_stellargraph_environment.py --help
python scripts/check_stellargraph_environment.py
```

If using an uninstalled local checkout, add `--repo-root PATH_TO_CHECKOUT`. The
script never downloads datasets, starts Neo4j, or requires GPU by default.

## TensorFlow GPU messages

StellarGraph's core workflows can run on CPU for tiny checks and most API
inspection. TensorFlow may print messages such as:

- `Could not find cuda drivers on your machine, GPU will not be used`
- `Cannot dlopen some GPU libraries`
- `Skipping registering GPU devices`

Treat these as **optional GPU availability warnings** unless the user explicitly
requires GPU execution. If GPU is required, verify TensorFlow's GPU stack with a
small device allocation before running model code; a visible NVIDIA device from
system tools is not proof that TensorFlow can use it.

## Optional dependency extras

| Need | Extra or package family | Notes |
| --- | --- | --- |
| Notebook demos and plotting-heavy examples | `stellargraph[demos]` | Installs demo helpers such as Jupyter, `gensim`, `rdflib`, `numba`, and plotting packages; many demos still download datasets. |
| Community detection demo | `stellargraph[igraph]` or `python-igraph` | `python-igraph` has platform-specific install constraints; do not make it a default dependency. |
| Neo4j connector workflows | `stellargraph[neo4j]` / `py2neo` plus a running Neo4j service | Importing connector classes is not the same as connecting to a database. |
| Repo test suite execution | test extra from package metadata | This is a maintainer/development dependency set, not required for ordinary package use. |

## Dataset download and cache failures

StellarGraph dataset loaders call `download()` when their data is missing. This
can fail because of network access, remote host changes, license constraints,
write permissions, or a stale local cache.

Recovery steps:

1. Set `STELLARGRAPH_DATASETS_PATH` to a writable cache location if the default
   user cache is not suitable.
2. Instantiate the dataset class and inspect `base_directory` before attempting
   download.
3. Use `download(ignore_cache=True)` only when you intentionally want to delete
   and re-fetch expected files.
4. If a task does not require the real public dataset, prefer a tiny synthetic
   `StellarGraph` fixture and avoid network access.

## Neo4j connector failures

Common causes:

- `py2neo` is missing because the `neo4j` extra was not installed.
- The database service is not running, the host/port is wrong, or authentication
  policy differs from the example setup.
- Node feature or ID properties differ from the connector defaults (`ID` and
  `features`).
- A task expects local in-memory `StellarGraph` methods on a Neo4j-backed graph;
  some connector methods are service queries and can be slower or limited.

Use the model-ops/interpretability Neo4j reference for connector-specific
routing and do not start containers or services unless the user approves.

## Graph/model workflow failures

- Data schema and constructor errors: read
  [`../sub-skills/graph-data-loading/references/troubleshooting.md`](../sub-skills/graph-data-loading/references/troubleshooting.md).
- Generator shape, node/link ID, or sampler errors: read
  [`../sub-skills/sampling-generators/references/troubleshooting.md`](../sub-skills/sampling-generators/references/troubleshooting.md).
- Node model/generator pairing errors: read
  [`../sub-skills/node-classification-gnns/references/troubleshooting.md`](../sub-skills/node-classification-gnns/references/troubleshooting.md).
- Link split, negative sampling, or KG scoring errors: read
  [`../sub-skills/link-prediction-kg/references/troubleshooting.md`](../sub-skills/link-prediction-kg/references/troubleshooting.md).
- Embedding-specific optional dependency or extraction errors: read
  [`../sub-skills/embedding-workflows/references/troubleshooting.md`](../sub-skills/embedding-workflows/references/troubleshooting.md).
- Graph classification and time-series shape errors: read
  [`../sub-skills/graph-time-series-workflows/references/troubleshooting.md`](../sub-skills/graph-time-series-workflows/references/troubleshooting.md).
