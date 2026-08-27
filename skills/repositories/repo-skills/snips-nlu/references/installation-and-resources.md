# Installation and language resources

## Purpose

Read this when a task starts with installing Snips NLU, checking whether the package is usable, resolving missing language resources, or deciding which Python/package versions are safe for Snips NLU `0.20.x`.

## Public installation baseline

Snips NLU is a Python package whose public import is `snips_nlu` and whose command-line entry points are:

```bash
python -m snips_nlu --help
snips-nlu --help
```

The package version represented by this skill is `0.20.2`; the persisted engine model format is `0.20.0`.

Public install command:

```bash
pip install snips-nlu
```

For development from a checkout, editable install is also normal:

```bash
python -m pip install -e .
```

Do not assume Python 3.11+ works for this old release. The package metadata allows Python 2.7 and Python >=3.5, but its dependency pins include old scikit-learn releases. A Python 3.8 CPU environment is a practical target for Snips NLU `0.20.x` when current Python versions fail to resolve wheels.

## Minimal import and CLI check

Use the root helper for a read-only environment check:

```bash
python scripts/check_snips_nlu_environment.py --json
```

Manual checks:

```bash
python - <<'PY'
from snips_nlu import SnipsNLUEngine
from snips_nlu.dataset import Dataset
from snips_nlu.__about__ import __version__, __model_version__
print(__version__, __model_version__)
print(SnipsNLUEngine, Dataset)
PY

python -m snips_nlu version
python -m snips_nlu model-version
python -m snips_nlu --help
```

Expected version output for this skill baseline:

```text
0.20.2
0.20.0
```

## Runtime dependency surfaces

Base package workflows rely on:

- `numpy`, `scipy`, `scikit-learn`, `sklearn-crfsuite`, and `python-crfsuite` for classical ML and CRF slot filling.
- `snips-nlu-parsers` and `snips-nlu-utils` for language parsing and resource utilities.
- `pyaml` / `PyYAML` for YAML dataset authoring conversion.
- `requests` for resource download commands.

Optional extras in package metadata:

| Extra | Use |
|---|---|
| `metrics` | Installs `snips-nlu-metrics` for `cross-val-metrics` and `train-test-metrics` output. |
| `test` | Adds test/lint helpers for the repository's native tests. Not required for using the package. |
| `doc` | Sphinx documentation build dependencies. Not required for runtime tasks. |

## Language resources

Snips NLU needs language resources before many training/parsing workflows can run with default configs or built-in entities. The docs describe the public download command:

```bash
python -m snips_nlu download en
# or
snips-nlu download en
```

Supported dataset language codes in this release are:

```text
de, en, es, fr, it, ja, ko, pt_br, pt_pt
```

Resource-related commands are covered by `sub-skills/cli-workflows/SKILL.md`.
Dataset/entity semantics are covered by `sub-skills/dataset-and-resources/SKILL.md`.

### Offline and network-aware behavior

- Do not silently download resources in a diagnostic or validation helper.
- If a workflow fails with `MissingResource` or a message such as `Language resource 'en' not found`, tell the user to install/link resources explicitly.
- If the task cannot use network, restrict work to dataset conversion/validation, API signature inspection, CLI help/version checks, or workflows that pass explicit in-memory resources.

## Source install on unsupported architecture

The README notes that prebuilt wheels existed for macOS, Linux x86_64, and Windows. Other architectures may require building from source and may need Rust plus `setuptools_rust` before `pip install snips-nlu`. Treat this as a host-level build prerequisite and avoid launching a long source build without user approval.

## Quick readiness decision

| Observation | Interpretation | Next action |
|---|---|---|
| `import snips_nlu` fails | Package/dependency/Python mismatch. | Use Python 3.8 for this old release; reinstall base package. |
| `python -m snips_nlu --help` works but `snips-nlu` is missing | Console script is not on PATH. | Use `python -m snips_nlu` or fix environment PATH. |
| `version` is not `0.20.2` | Skill may not match installed behavior. | Check changelog or refresh the repo skill for the installed version. |
| `model-version` differs from a persisted engine's `nlu_engine.json` | Model compatibility risk. | See `sub-skills/engine-api/references/configuration-and-persistence.md`. |
| Resource check fails for a language | Training/parsing may fail. | Run `python -m snips_nlu download <language>` or link compatible resources. |
