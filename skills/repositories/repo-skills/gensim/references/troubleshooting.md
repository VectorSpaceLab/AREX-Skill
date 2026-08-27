# Cross-Cutting Troubleshooting

## When to read

Read this when Gensim fails to install/import, optional functionality is missing,
a workflow is unexpectedly slow, or data/model artifacts do not load. Workflow-
specific troubleshooting lives in each sub-skill's `references/troubleshooting.md`.

## Install and import failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'gensim'` | Package is not installed in the Python running the task. | Run `python -m pip install gensim`, then verify with `python -c "import gensim; print(gensim.__version__)"`. Use the same Python executable for install and execution. |
| Import failure mentioning `numpy`, `scipy`, BLAS, LAPACK, or compiled extensions | Scientific Python dependency or compiled wheel mismatch. | Reinstall/upgrade `numpy` and `scipy` in a clean environment. Prefer wheels or Conda on platforms where building NumPy/SciPy from source is hard. |
| Slow linear algebra, LSI/LDA much slower than expected | NumPy/SciPy linked to slow BLAS/LAPACK or too many/too few BLAS threads. | Inspect `python -c "import scipy; scipy.show_config()"`. Use a faster BLAS build if performance matters; tune environment thread variables only after measuring. |
| `pip check` reports broken requirements | Dependency resolver left incompatible package versions. | Create a fresh environment or repair the reported packages before trusting model results. |
| Local checkout import differs from installed version | Current directory or `PYTHONPATH` shadows the intended package. | Run from a neutral directory and check `importlib.metadata.version('gensim')`; avoid relying on implicit checkout imports. |

Use [`../scripts/check_gensim_environment.py`](../scripts/check_gensim_environment.py)
for a privacy-safe import/dependency check.

## Optional dependency errors

| Symptom | Optional surface | Recovery |
| --- | --- | --- |
| `ImportError` mentioning Annoy | Approximate nearest-neighbor indexer | Install `annoy` or use exact `MatrixSimilarity`/`Similarity` instead. |
| `ImportError` mentioning NMSLIB | NMSLIB approximate indexer | Install `nmslib` only if wheels support your Python/platform; otherwise use exact indexes or Annoy. |
| `ImportError` for `ot` or POT | Word Mover's Distance | Install POT or avoid WMD; use cosine/soft-cosine alternatives when acceptable. |
| `ImportError` for `Pyro4` | Distributed LDA/LSI | Install the `distributed` extra or prefer `LdaMulticore`/single-machine models. |
| `ImportError` for `visdom` | Callback visualization | Install Visdom only for visualization; metrics can often be logged without it. |
| Missing NLTK data or scikit-learn | Documentation examples | Avoid full docs examples in production unless those packages/data are intentionally installed. |

Do not install all extras by default. Select only the optional surface needed by
the task.

## Data and model artifact failures

- **Raw strings passed to `Dictionary.doc2bow`**: pass a token list such as
  `doc.lower().split()` or `gensim.utils.simple_preprocess(doc)`, not the raw
  string.
- **Empty vectors**: query tokens may all be out-of-vocabulary for the dictionary
  or model. Check preprocessing and vocabulary construction.
- **Feature mismatch**: a transformation or similarity index expects the same
  feature-id space used at training/indexing time. Reuse the same `Dictionary`
  and preprocessing pipeline.
- **Compression/format errors**: choose the loader matching the file format
  (`MmCorpus`, `SvmLightCorpus`, `BleiCorpus`, etc.) and confirm whether the
  file is plain, `.gz`, or `.bz2`.
- **Large downloads via `gensim.downloader`**: call `api.info(name)` first, set
  `GENSIM_DATA_DIR` intentionally, and use `return_path=True` when you only need
  a path. Some pretrained models are gigabytes.
- **Wikipedia dump workflows are huge**: full XML dumps are network, CPU, disk,
  and time intensive. Test with tiny fixtures before scheduling full conversion.

## Reproducibility and randomness

- Set `seed`/`random_state` where models expose them.
- Use `workers=1` for deterministic tiny smoke tests; parallel training can
  introduce order-dependent floating-point differences.
- Do not assert exact topic ordering or embedding coordinates in production
  checks. Assert shapes, vocabulary size, non-empty topics, and semantic ranking
  properties when possible.

## When to stop

Stop and ask for a narrowed scope or more resources when the task requires:

- a large pretrained model download not already present in cache,
- a full Wikipedia dump or benchmark-scale corpus,
- optional dependencies that do not have wheels for the chosen Python/platform,
- multi-node distributed services, or
- exact reproduction of stochastic topics/embeddings beyond reasonable tolerance.
