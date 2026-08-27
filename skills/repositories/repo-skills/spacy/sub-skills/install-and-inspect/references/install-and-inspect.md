# Install and inspect spaCy

## When to read this

Use this reference to select an installation method and run no-download checks for the `spacy` distribution/import package, the `spacy.__version__` runtime fact, a blank English pipeline, the `python -m spacy` CLI, and an already-installed trained pipeline package or path.

## Verified package facts for this skill snapshot

| Fact | Value / rule |
| --- | --- |
| Distribution name | `spacy` |
| Import name | `spacy` |
| Source snapshot version | `3.8.15` from `spacy.__version__` / package metadata |
| Python support from package metadata | `>=3.9,<3.15` |
| Preferred CLI invocation | `python -m spacy` |
| Console entry point | `spacy = spacy.cli:setup_cli`; if the shell entry point is missing, use `python -m spacy` |
| Base smoke verified during construction | `import spacy`, `spacy.blank("en")`, blank English tokenization, `python -m spacy --help`, `python -m spacy info --silent` |
| Optional stacks | CUDA/CuPy, Apple acceleration, transformers, lookups, and `ja`/`ko`/`th` tokenizer extras are optional and were not verified for this generated skill |

The README install summary in this checkout still mentions an older Python range. For installation decisions, prefer the current packaging metadata range above.

## Installation choices

### Pip wheel install

Use this for most runtime environments.

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -U spacy
python -m spacy info --silent
```

Pin versions when reproducibility matters:

```bash
python -m pip install "spacy==3.8.15"
python -m pip check
```

### Conda install

Use conda-forge when the rest of the project is conda-managed.

```bash
conda create -n spacy-env -c conda-forge python=3.11 spacy
conda run -n spacy-env python -m spacy info --silent
```

If the project already has an environment, install into that environment instead of creating a second one:

```bash
conda install -c conda-forge spacy
python -m spacy info --silent
```

### Source / editable install

Use this only when working from a spaCy source checkout or when testing local modifications. Building from source requires compiler support, Python headers, Cython build requirements, and compatible compiled dependencies.

```bash
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install --no-build-isolation --editable .
python -m pip check
python -m spacy info --silent
```

For a source checkout with optional extras, quote the requirement so shells do not expand brackets:

```bash
python -m pip install --no-build-isolation --editable ".[lookups]"
python -m pip install --no-build-isolation --editable ".[cuda12x]"
```

Only install optional extras that the user explicitly needs. Do not install all extras to prove base spaCy.

## No-download import and blank-pipeline smoke

Run this after installation. It uses only the base package and a blank English tokenizer.

```bash
python - <<'PY'
import sys
import spacy

print("python", sys.version.split()[0])
print("spacy", spacy.__version__)
assert (3, 9) <= sys.version_info[:2] < (3, 15), "unsupported Python for this spaCy snapshot"

nlp = spacy.blank("en")
doc = nlp("Hello, spaCy!")
assert [t.text for t in doc] == ["Hello", ",", "spaCy", "!"]
print("blank_en_ok", nlp.lang, nlp.pipe_names, [t.text for t in doc])
PY
```

Expected signal: the script prints a spaCy version, `blank_en_ok en`, and tokenization `['Hello', ',', 'spaCy', '!']`. A blank pipeline usually has no trainable components until you add them; that is not an install failure.

## CLI entry-point checks

Prefer module invocation because it targets the active Python interpreter.

```bash
python -m spacy --help
python -m spacy info --silent
```

`python -m spacy --help` proves that the CLI registry loads. Installed-package inspection for this snapshot observed these top-level command groups/names: `download`, `apply`, `assemble`, `convert`, `evaluate`, `find-function`, `find-threshold`, `info`, `package`, `pretrain`, `train`, `validate`, `project`, `debug`, `benchmark`, and `init`.

Route command depth as follows:

| Command surface | Owner |
| --- | --- |
| `--help`, `info`, `validate`, `download` for model-install diagnostics | This sub-skill |
| `init`, `debug`, `convert`, `train`, `pretrain`, `evaluate`, `package`, `assemble`, `apply`, `find-function`, `find-threshold`, `benchmark` | `training-and-cli` |
| `project ...` | `project-workflows` |
| CLI errors caused by custom factories/components | `pipeline-components` plus `training-and-cli` if config-driven |

## `python -m spacy validate`

Use `validate` after upgrading spaCy or after installing trained pipeline packages. It scans installed pipeline packages and returns non-zero when incompatible packages are found.

```bash
python -m spacy validate
```

Important caveats:

- `validate` is about trained pipeline package compatibility, not whether the base `spacy` import works.
- The command may need network access to load the spaCy/model compatibility table. If the environment is offline, use `python -m spacy info --silent` and direct package metadata checks for base health.
- A `validate` failure can coexist with a healthy base package; update or reinstall the affected pipeline packages rather than rebuilding spaCy immediately.

## Loading a trained pipeline only when it exists

`spacy.blank("en")` creates a blank English pipeline and never downloads a model. `spacy.load("en_core_web_sm")` loads an installed trained pipeline package or a local pipeline directory and fails if that package/path is absent.

Safe check for an installed model package:

```bash
python - <<'PY'
import importlib.util
import spacy

model = "en_core_web_sm"
if importlib.util.find_spec(model) is None:
    raise SystemExit(f"{model!r} is not installed; base spaCy can still be healthy")

nlp = spacy.load(model)
doc = nlp("This is a sentence.")
print(model, nlp.pipe_names, len(doc))
PY
```

Safe check for a local pipeline directory path supplied by the user:

```bash
python - <<'PY'
from pathlib import Path
import spacy

model_path = Path("replace-with-pipeline-directory")
if not model_path.exists():
    raise SystemExit("pipeline directory does not exist")

nlp = spacy.load(model_path)
print(nlp.meta.get("name"), nlp.pipe_names)
PY
```

Do not treat a missing `en_core_web_sm` package as a base spaCy install failure. Install the model only when the workflow actually needs pretrained components:

```bash
python -m spacy download en_core_web_sm
python -m spacy validate
```

For automated production builds, prefer a pinned pipeline package dependency or a wheel/tarball URL managed by the project rather than relying on interactive download behavior.

## Bundled healthcheck helper

From any directory, run the bundled helper with the active Python interpreter:

```bash
python scripts/spacy_healthcheck.py
python scripts/spacy_healthcheck.py --json
python scripts/spacy_healthcheck.py --model en_core_web_sm
python scripts/spacy_healthcheck.py --prefer-gpu
```

Use stricter gates only when the user explicitly requires them:

```bash
python scripts/spacy_healthcheck.py --model en_core_web_sm --require-model
python scripts/spacy_healthcheck.py --require-gpu --gpu-id 0
python scripts/spacy_healthcheck.py --run-validate
```

The helper does not download models, install packages, run training, mutate project files, or require the original source checkout.

## Native candidates owned by this sub-skill

- `install-import-blank-pipeline`: safe CPU import/version/blank tokenizer check.
- `cli-help-info`: safe CLI registry and `info --silent` check.
- `optional-cuda-probe`: optional only; no CPU substitute for true CUDA claims.
- `optional-apple-probe`: optional only; no CPU substitute for Apple acceleration claims.
