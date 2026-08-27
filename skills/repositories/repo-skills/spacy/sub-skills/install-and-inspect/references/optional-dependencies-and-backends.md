# Optional dependencies and backends

## When to read this

Use this reference when a task mentions lemmatization lookup tables, transformer pipelines, CUDA/GPU acceleration, Apple acceleration, Japanese/Korean/Thai tokenizer support, or uncertainty about whether an optional backend is installed. These are optional capabilities: base spaCy import, blank English tokenization, and CLI help/info do not require them.

## Verification status for this generated skill

Construction verified the CPU/base package path only. CUDA, Apple/MPS, `transformers`, `lookups`, and `ja`/`ko`/`th` extras were documented from package metadata but were not installed or executed as successful optional-backend proofs. Treat commands here as install/probe patterns, not as claims that the current user environment has those extras.

## Extras map

| Extra | Adds | Install pattern | Probe / expected signal |
| --- | --- | --- | --- |
| `lookups` | `spacy-lookups-data` tables for lemmatization and normalization, useful for blank pipelines or languages without pretrained lookup data | `python -m pip install "spacy[lookups]"` | Import succeeds and lemmatizer initialization no longer complains about missing lookup tables for the selected language |
| `transformers` | `spacy-transformers` integration for transformer-backed components | `python -m pip install "spacy[transformers]"` | `python -c "import spacy_transformers"` succeeds; model downloads/configs are separate workflow concerns |
| `cuda` | Generic CuPy dependency for GPU acceleration | `python -m pip install "spacy[cuda]"` | `spacy.prefer_gpu()` returns `True` only with compatible hardware/runtime |
| `cuda11x` | CuPy wheel for CUDA 11.x runtimes | `python -m pip install "spacy[cuda11x]"` | `python -c "import cupy; print(cupy.cuda.runtime.runtimeGetVersion())"` succeeds |
| `cuda12x` | CuPy wheel for CUDA 12.x runtimes | `python -m pip install "spacy[cuda12x]"` | Same CuPy runtime probe succeeds |
| Older CUDA variants | Historical CuPy wheel names such as `cuda80`, `cuda90`, `cuda91`, `cuda92`, `cuda100`, `cuda101`, `cuda102`, `cuda110`, `cuda111`, `cuda112`, `cuda113`, `cuda114`, `cuda115`, `cuda116`, `cuda117` | `python -m pip install "spacy[cuda117]"` with the matching variant | Only use when the host CUDA driver/runtime requires that exact wheel family |
| `cuda-autodetect` | `cupy-wheel` dependency intended to select an appropriate CuPy wheel | `python -m pip install "spacy[cuda-autodetect]"` | CuPy import and spaCy GPU probe succeed |
| `apple` | `thinc-apple-ops` for Apple acceleration | `python -m pip install "spacy[apple]"` | On a supported Apple host, `spacy.prefer_gpu()` can return `True`; on Linux/Windows it should not be treated as a required gate |
| `ja` | Japanese tokenizer dependencies `sudachipy` and `sudachidict_core` | `python -m pip install "spacy[ja]"` | `spacy.blank("ja")` can initialize the third-party tokenizer stack |
| `ko` | Korean tokenizer dependency `natto-py` | `python -m pip install "spacy[ko]"` | `spacy.blank("ko")` initializes when the native tokenizer dependency is available |
| `th` | Thai tokenizer dependency `pythainlp` | `python -m pip install "spacy[th]"` | `spacy.blank("th")` initializes when `pythainlp` is available |

## Optional GPU probes

Use `prefer_gpu()` when GPU acceleration is nice to have. A `False` return means spaCy will stay on CPU and should not fail a CPU workflow.

```bash
python - <<'PY'
import spacy
print("prefer_gpu", spacy.prefer_gpu(0))
PY
```

Use `require_gpu()` only when the user has made GPU a hard requirement. It raises an exception if a compatible CuPy/GPU stack is unavailable.

```bash
python - <<'PY'
import spacy
try:
    print("require_gpu", spacy.require_gpu(0))
except Exception as e:
    raise SystemExit(f"GPU required but unavailable: {type(e).__name__}: {e}")
PY
```

The bundled healthcheck exposes the same distinction:

```bash
python scripts/spacy_healthcheck.py --prefer-gpu --gpu-id 0
python scripts/spacy_healthcheck.py --require-gpu --gpu-id 0
```

## CUDA/CuPy selection rules

1. Check the user requirement first: if CPU is acceptable, do not install CUDA extras solely for a base spaCy smoke check.
2. If GPU is required, identify the host CUDA runtime/driver family and select the matching spaCy extra (`cuda11x`, `cuda12x`, or an older exact variant when necessary).
3. Install only one CuPy wheel family in an environment unless the user has a specific reason to rebuild the environment.
4. After installation, check both CuPy and spaCy:

```bash
python - <<'PY'
import cupy
import spacy
print("cupy", cupy.__version__)
print("prefer_gpu", spacy.prefer_gpu(0))
PY
```

5. If `prefer_gpu()` is `False` but base import and blank tokenization pass, report an optional backend limitation rather than a failed CPU install.
6. If `require_gpu()` fails, stop or repair the CUDA/CuPy stack before claiming GPU support.

## Apple acceleration rules

`spacy[apple]` is for Apple acceleration through `thinc-apple-ops`. Do not install or verify it on non-Apple hosts as evidence of Apple/MPS support. On Apple Silicon, install the extra in the target environment and run the bundled healthcheck with `--prefer-gpu`; use `--require-gpu` only when the task explicitly requires acceleration.

## Language tokenizer extras

Most blank language classes are available from the base package, but some tokenizers require third-party packages. If a user asks for Japanese, Korean, or Thai tokenization and initialization fails with a missing dependency, install the corresponding extra and rerun the exact tokenizer smoke for that language:

```bash
python -m pip install "spacy[ja]"
python - <<'PY'
import spacy
nlp = spacy.blank("ja")
print([t.text for t in nlp("これはテストです。")])
PY
```

Repeat with `ko` or `th` as needed. Do not install all language extras unless the user needs all of them.

## Transformer stacks

`spacy[transformers]` installs the spaCy transformer integration, but it does not by itself prove that a specific transformer pipeline, model weights, tokenizer files, or internet/cache access is available. After installing the extra, route config/training details to `training-and-cli` and component/factory wiring to `pipeline-components`.

## Lookup tables

Use `spacy[lookups]` or `spacy-lookups-data` when blank pipelines need lemmatizer lookup tables or language normalization tables. If a lemmatizer initializes but returns only base forms or raises missing-table errors, install the lookup extra and reinitialize the pipeline rather than treating the base spaCy package as broken.
