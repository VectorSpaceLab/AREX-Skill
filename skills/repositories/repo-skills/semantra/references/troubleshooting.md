# Semantra Troubleshooting

## Purpose

Read this for cross-cutting Semantra package installation, import, dependency,
model, cache, and local server failures. For workflow-specific problems, follow
the linked sub-skill troubleshooting references.

## Package import fails with `pkg_resources` missing

Symptom examples:

```text
ModuleNotFoundError: No module named 'pkg_resources'
```

Semantra 0.1.12 imports `pkg_resources` when loading the CLI. Some newer
Setuptools environments no longer expose that module by default.

Recovery options:

1. In the Semantra environment, install a Setuptools release that still provides
   `pkg_resources`, for example:
   ```sh
   python -m pip install 'setuptools<81'
   ```
2. Or update Semantra's version lookup to use `importlib.metadata` if you are
   maintaining the package.
3. Re-run:
   ```sh
   semantra --version
   semantra --help
   ```

## `semantra --help` works but model execution fails

Likely cause: model-specific dependencies, downloads, credentials, or hardware
are failing after the CLI starts.

Next steps:

- Local transformer model errors ->
  [models-and-embeddings troubleshooting](../sub-skills/models-and-embeddings/references/troubleshooting.md).
- Document/PDF/cache preprocessing errors ->
  [document-indexing troubleshooting](../sub-skills/document-indexing/references/troubleshooting.md).
- Query/UI/server errors after processing ->
  [interactive-search troubleshooting](../sub-skills/interactive-search/references/troubleshooting.md).

## OpenAI mode fails after installing current dependencies

Semantra 0.1.12 uses the legacy `openai.Embedding.create` API and declares
`openai>=0.27.2` without an upper bound. Current OpenAI SDK versions can import
but fail at runtime with an API-removed error.

Recovery choices:

- Use a compatible `openai<1` environment for Semantra OpenAI mode.
- Update Semantra's OpenAI integration to the current SDK API.
- Use a local transformer model instead.

Also confirm `OPENAI_API_KEY`, privacy approval, and cost approval before using
OpenAI mode.

## SVM mode fails with missing `sklearn`

`--svm` lazily imports `sklearn.svm`, but `scikit-learn` is not part of
Semantra's declared dependencies. Install it only when SVM mode is required:

```sh
python -m pip install scikit-learn
semantra --svm documents/*.txt
```

Do not use SVM with asymmetric models such as `sgpt` or `sgpt-1.3B`.

## First run downloads a model or is slow

Local transformer presets and custom Hugging Face models may download tokenizer
and model files on first use. Large corpora, overlapping windows, and large
models increase runtime and disk usage.

Recovery:

- Test with a tiny corpus and `--model minilm` first.
- Use `--no-server` for preprocessing-only runs.
- Choose a smaller model or smaller corpus.
- Confirm network/cache policy before running on private or offline systems.

## CUDA is visible but not required

Semantra can use CUDA through PyTorch when available, but core local transformer
search also works on CPU. Do not treat a CPU environment as broken unless the
user specifically requires GPU acceleration.

Check CUDA only when speed or GPU behavior matters:

```sh
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
PY
```

## Cache artifacts look stale or inconsistent

Use the document-indexing cache helper before deleting files:

```sh
python sub-skills/document-indexing/scripts/inspect_semantra_cache.py --cache-dir ./semantra-cache
```

If token/config/embedding/Annoy files disagree, rerun with `--force` or remove
only the affected document/config group.

## Server cannot bind or UI cannot load

- Port busy: use `--port 8081` or another free port.
- LAN access needed: use `--host 0.0.0.0` only after privacy review.
- Browser blank/static 404: the installed package may be missing bundled
  `client_public` assets. Reinstall from a distribution that includes package
  data or rebuild package assets if maintaining a checkout.

## Safe triage order

1. `semantra --version`
2. `semantra --help`
3. `semantra --list-models`
4. Root install inspector:
   ```sh
   python scripts/inspect_semantra_install.py --skip-cli
   ```
5. Workflow-specific checks from the relevant sub-skill.

Stop and ask before using credentials, sending private documents to external
APIs, installing broad optional dependencies, exposing the server beyond
localhost, or deleting a user's cache directory.
