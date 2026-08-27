# Stanza Troubleshooting

Start here for cross-cutting failures, then continue with the nearest sub-skill troubleshooting reference:

- neural pipelines and resources: `../sub-skills/pipelines-and-resources/references/troubleshooting.md`
- documents and CoNLL-U: `../sub-skills/documents-and-conllu/references/troubleshooting.md`
- CoreNLP client: `../sub-skills/corenlp-client/references/troubleshooting.md`
- training and data preparation: `../sub-skills/training-and-data-prep/references/troubleshooting.md`
- visualization and demos: `../sub-skills/visualization-and-demos/references/troubleshooting.md`

The paths above are relative to this reference file. Run `python ../scripts/check_environment.py` from this directory, or `python scripts/check_environment.py` from the skill root, for a no-download diagnostic.

## Install and import failures

### `ModuleNotFoundError: No module named 'stanza'`

Install the distribution into the Python environment that will run the workflow:

```bash
python -m pip install stanza
python -c "import stanza; print(stanza.__version__)"
```

For source development, use `python -m pip install -e /path/to/stanza`. Do not rely on the checkout being the current directory: that can hide an installation or interpreter mismatch.

### A base dependency does not import

Run:

```bash
python scripts/check_environment.py
python -m pip check
```

Confirm that `python` and `pip` refer to the same environment. Install the package rather than patching imports individually; its metadata declares PyTorch, NumPy, requests, protobuf, NetworkX, tqdm, Hugging Face Hub, platformdirs, emoji, and UD tools. Keep PyTorch wheels consistent with the target CPU/CUDA runtime.

### Protobuf errors

Stanza imports protobuf through `google.protobuf`. If imports or generated messages fail, inspect the installed protobuf version and `pip check`, remove conflicting duplicate environments, and reinstall Stanza's declared dependency set. CoreNLP protobuf issues can also reflect a Python/Java CoreNLP version mismatch; use the CoreNLP sub-skill troubleshooting reference before regenerating protocol files.

## Resource and pipeline failures

### Models or `resources.json` are missing

Model data is not bundled with this skill or necessarily with the Python wheel. Stage it explicitly with `stanza.download(...)`, subject to approval for network and disk use. For offline checks, set `download_method=DownloadMethod.NONE` and point `model_dir` or `STANZA_RESOURCES_DIR` at a prepared cache.

Do not repeatedly delete the whole cache. First verify:

- the requested language and processor names;
- `model_dir` and `STANZA_RESOURCES_DIR` precedence;
- package compatibility for the installed Stanza version;
- proxy, certificate, and Hugging Face/network settings;
- cache permissions and free disk space.

### Processor dependency or package errors

Use the pipeline sub-skill's processor dependency guidance. Typical chains include tokenize before downstream processors, MWT where the language requires it, POS before lemma/depparse, and constituency prerequisites as documented by the selected package. Do not infer that every processor exists for every language or package.

### CUDA is unavailable or out of memory

CUDA is optional for ordinary functional use. Check it with:

```bash
python scripts/check_environment.py --check-cuda
```

Use `use_gpu=False` or an explicit CPU device for a functional fallback. For GPU OOM, reduce batch sizes and document length, avoid loading unneeded processors, and ensure that the installed PyTorch build matches the driver. A successful `torch` import does not prove CUDA availability.

## Document and CoNLL-U failures

- Preserve the distinction between `Token` and `Word`; multi-word tokens can contain several words.
- CoNLL-U IDs may be integers, ranges, or decimal empty-node IDs. Do not coerce every ID to a plain integer.
- Preserve sentence comments and fields not being changed.
- Validate head indices, blank-line sentence boundaries, and the ten-column shape before blaming the model.

Use `sub-skills/documents-and-conllu/scripts/validate_conllu.py` for local format validation.

## CoreNLP failures

The Python package provides a client, not a complete Java runtime and model distribution. Before starting a managed server, run:

```bash
python scripts/check_environment.py --check-java
python sub-skills/corenlp-client/scripts/check_corenlp_client.py --help
```

For connection refused, distinguish a managed server from `start_server=False`/external endpoint mode. Check Java, jars/classpath, endpoint, port conflicts, startup timeout, memory, and model jars. Starting or downloading CoreNLP is side-effectful and must be explicit.

For 4xx/5xx responses, capture annotators, properties, input/output format, endpoint, timeout, and the server log. Pattern-engine helpers have engine-specific payload requirements; route Semgrex, TokensRegex, Tregex, Ssurgeon, and Tsurgeon problems to the CoreNLP sub-skill.

## Training failures

Training is data-, compute-, and task-specific. Before a full run:

1. validate corpus paths and formats;
2. render a command with `sub-skills/training-and-data-prep/scripts/build_training_command.py`;
3. inspect the selected module's `--help`;
4. run a tiny smoke without external experiment logging;
5. approve compute, downloads, checkpoints, and output paths.

Missing pretrains, charlms, embeddings, or dataset-root environment variables are data-preparation failures, not package-import failures. Do not silently substitute a different language treebank or overwrite an existing model directory.

## Visualization failures

Install only the optional backend required by the selected workflow. Browser, Streamlit, notebook, spaCy, and matplotlib dependencies are not all part of the base runtime. Prefer generating static HTML from existing annotations when model execution or a server is unnecessary. Treat browser/server launch and notebook execution as explicit side effects.

## When to refresh the skill

Refresh when Stanza changes public pipeline/document/CoreNLP signatures, resource manifest behavior, supported CoNLL-U fields, training entry points, extras, or the source baseline recorded in `repo-provenance.md`.
