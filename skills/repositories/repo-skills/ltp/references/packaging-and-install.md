# Packaging and Install Reference

## When to read

Read this when installing LTP, debugging imports, working from a source checkout, or deciding which optional dependencies/toolchains are needed before using a sub-skill.

## Distribution split

LTP 4 is split into separate packages:

| Distribution | Import name | Purpose | Notes |
| --- | --- | --- | --- |
| `ltp` | `ltp` | High-level Python interface: `LTP(...)`, `StnSplit`, output wrappers. | Depends on `ltp-core`, `ltp-extension`, and `huggingface_hub`. |
| `ltp-core` | `ltp_core` | Neural model classes, task heads, algorithms, data modules, train/eval entry points. | Requires `torch` and `transformers`; training uses additional optional dependencies. |
| `ltp-extension` | `ltp_extension` | Rust-backed Python extension for sentence splitting, hooks, legacy perceptron CWS/POS/NER, and utility algorithms. | Installed from wheels for ordinary Python use; source builds require Rust and maturin. |
| Rust crate `ltp` | `ltp` in Cargo | Native Rust legacy CWS/POS/NER crate. | Enable `serialization` for `ModelSerde` and type aliases; enable `parallel` for rayon. |
| Rust crate `ltp-cffi` | C library named `ltp` | C ABI over the Rust legacy implementation. | Builds `cdylib` and `staticlib`. |

## Standard Python install

Use a Python version supported by the package and available wheels. Python 3.10 or 3.11 is a conservative choice for compiled ML dependencies.

```bash
python -m pip install torch transformers
python -m pip install ltp ltp-core ltp-extension
python - <<'PY'
from ltp import LTP, StnSplit
print(StnSplit().split('汤姆生病了。他去了医院。'))
print(LTP)
PY
```

If the package index is slow or unavailable, configure your normal trusted index/mirror outside the skill. Do not bake private proxies or credentials into scripts.

## Source-checkout install pattern

For a source checkout, the Python packages live under separate subdirectories. Install the core/interface packages separately and use a wheel for `ltp-extension` unless you intentionally have Rust/maturin ready:

```bash
python -m pip install torch transformers huggingface_hub ltp-extension
python -m pip install -e python/core
python -m pip install -e python/interface --no-deps
```

Build the local `ltp-extension` source only when you need to change the Rust/Python extension:

```bash
python -m pip install maturin
maturin build --release -m python/extension/Cargo.toml --out dist --no-default-features --features="malloc"
```

For CPU-specific optimization, the repository documents adding `-- -C target-cpu=native` to the maturin build. Treat that as a local-build choice; wheels are safer for ordinary package users.

## Optional workflow dependencies

| Workflow | Extra needs | Safe default |
| --- | --- | --- |
| High-level inference | `torch`, `transformers`, `huggingface_hub`, `ltp-extension` | Install standard Python packages; do not load remote models until the user accepts downloads or provides a local model path. |
| Fast legacy CWS/POS/NER | `ltp-extension` and legacy model files | Use `LTP("LTP/legacy")` for high-level loading or direct `CWSModel.load`/`POSModel.load`/`NERModel.load` with local files. |
| Training/evaluation | PyTorch Lightning, torchmetrics, datasets, hydra-core, hydra-colorlog, rich, pyrootutils, and possibly loggers | Use the training sub-skill command builder first; install only the train dependencies you need. |
| FastAPI service wrapper | `fastapi`, `uvicorn`, plus the usual LTP runtime | Keep service dependencies separate from basic inference installs. |
| Rust crate/CFFI | `cargo`, `rustc`, C compiler/linker for CFFI, model binaries | Use the Rust sub-skill static checker before building. |

## Minimal import and backend probe

Run the bundled probe from the skill root:

```bash
python scripts/check_ltp_install.py --json
python scripts/check_ltp_install.py --check-cuda
```

The probe verifies distribution versions, import names, sentence splitting, entity extraction, `ltp_core` CRF instantiation, and optional CUDA visibility. It deliberately avoids Hugging Face downloads, model training, and Rust builds.

## Version and package-name gotchas

- The public branding is **LTP**, but Python imports are lowercase (`ltp`, `ltp_core`, `ltp_extension`).
- The high-level `LTP(...)` factory dispatches to a neural implementation when the model `config.json` has the neural flag and to the legacy implementation otherwise.
- A local model directory must contain `config.json`; missing config produces a file-not-found error before model weights are loaded.
- `ltp_extension` is a compiled extension. Import failures often mean no compatible wheel exists for the Python/platform, a bad local source build, or missing shared library dependencies.
- Training imports may fail even when inference imports work, because training dependencies are intentionally broader.
