# Cross-Cutting Troubleshooting

## When to read

Read this when LTP cannot install, import, load a model, use CUDA, run optional training, or build Rust/C bindings. Then follow the troubleshooting reference inside the nearest sub-skill.

## Install/import failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'ltp'` | The high-level package is not installed in the active Python environment. | Run `python -m pip install ltp ltp-core ltp-extension`, then `python scripts/check_ltp_install.py --json`. |
| `ModuleNotFoundError: No module named 'ltp_core'` | `ltp-core` missing or installed into a different Python. | Install `ltp-core` in the same environment and verify with the root probe. |
| `ModuleNotFoundError` or shared-library error for `ltp_extension` | Compiled extension wheel missing/incompatible, or failed local Rust build. | Prefer a compatible `ltp-extension` wheel. For source builds, install Rust and maturin intentionally, then rebuild. |
| `pip check` reports broken requirements | Package versions were mixed across package indexes or an editable/source install replaced a dependency. | Recreate a clean environment; install backend dependencies, `ltp-extension`, local `ltp_core`, then local `ltp` in that order. |
| Import succeeds but training imports fail | Training dependencies are optional/broader than inference dependencies. | Use `sub-skills/training-and-data/scripts/build_train_command.py` and install only the needed train dependencies. |

## Model loading and Hugging Face failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `config.json not found` | The model id/path cannot resolve to an LTP model config. | Check the model id spelling or pass a local directory containing `config.json`. |
| Network timeout or proxy error when calling `LTP("LTP/small")` | Hugging Face download is blocked or slow. | Use a pre-downloaded local model path, configure network/proxy outside the code, or pass `local_files_only=True` to force cache-only behavior. |
| Private model access fails | Token missing or wrong. | Pass `token=...` only through the runtime environment; do not commit tokens into scripts. |
| `LTP("LTP/legacy")` cannot find task model files | Legacy config resolved but CWS/POS/NER binary files are missing. | Re-download or point to a complete local legacy model directory; for direct APIs pass explicit model file paths. |

## Pipeline/API misuse

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ValueError: Unsupported tasks` | Requested tasks are not supported by the selected model config, especially legacy models. | Use a neural model for `srl`, `dep`, `sdp`, or `sdpg`; use legacy only for `cws`, `pos`, `ner`. |
| Legacy NER fails or returns poor output | NER needs words and POS tags. | Include tasks `['cws', 'pos', 'ner']` or pass words and POS results explicitly. |
| Output unpacking behaves unexpectedly | `LTPOutput` is a mapping-like dataclass, not a plain tuple. | Use `output.cws`, `output['cws']`, integer indexing, or `output.to_tuple()`. |
| Pretokenized input gives strange tags | `cws` was omitted but raw strings were supplied. | If `cws` is absent from tasks, pass `List[List[str]]` tokenized words. |

## CUDA/backend failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `torch.cuda.is_available()` is false | CPU-only torch, driver/runtime mismatch, or no GPU exposed to the process. | Run `python scripts/check_ltp_install.py --check-cuda`; reinstall a compatible torch build only if GPU is required. |
| CUDA import succeeds but model move fails | Torch/driver/library ABI mismatch or insufficient memory. | Test a tiny CUDA allocation first, then move the model; fall back to CPU if acceleration is optional. |
| User asks to prove GPU behavior | CPU import is not enough. | Run an explicit CUDA smoke and, if needed, a small model inference using a local/cached model. |

## Training/config failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Hydra cannot find a config group | Training is running outside an environment where the config tree is available or an override name is wrong. | Use the training sub-skill command builder and check `references/configuration.md`. |
| Eval exits because `ckpt_path` is missing | `ltp_core.eval` asserts that a checkpoint path is supplied. | Add `ckpt_path=/path/to/checkpoint.ckpt` or use the bundled command builder validation. |
| Data adapter errors | Missing split files, missing vocab files, or wrong BIO/CoNLL-U/SRL format. | Run `sub-skills/training-and-data/scripts/validate_ltp_training_data.py` on a copy of the dataset. |
| Logger prompts for credentials | Optional logger config (`wandb`, `mlflow`, etc.) selected without credentials. | Use no logger or a local CSV/TensorBoard logger unless credentials are intentionally provided. |

## Rust/C build failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `cargo: command not found` | Rust toolchain is absent. | Install Rust intentionally or keep to Python workflows. Use `sub-skills/rust-bindings/scripts/check_rust_layout.py` first. |
| Rust example cannot load model files | `data/legacy-models/*.bin` files are absent. | Provide the legacy model binaries and verify the paths before running examples. |
| `ModelSerde` or `CWSModel` alias missing | Cargo features omitted. | Enable `serialization`; enable `parallel` for rayon-backed parallel prediction. |
| C linker cannot find `ltp` library | `ltp-cffi` was not built or library path is missing. | Build the CFFI crate first, then point the compiler/linker to the generated static or dynamic library. |

## Stop conditions

Stop and ask for user approval before: downloading large model archives, running long training or benchmark jobs, installing/changing system Rust or CUDA toolchains, using private tokens, or starting a service that exposes an API endpoint.
