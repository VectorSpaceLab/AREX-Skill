# DeepFilterNet export and evaluation troubleshooting

Use this guide to diagnose ONNX export, export-directory validation, model summary, benchmark evaluation, and DNSMOS failures. If the symptom is basic model loading or enhancement, route to [python-enhancement](../../python-enhancement/SKILL.md). If the symptom is data generation or HDF5 training data, route to [training-data](../../training-data/SKILL.md).

## 1. Export dependency failures

| Symptom | Likely cause | Action | Stop condition |
|---|---|---|---|
| `ModuleNotFoundError: No module named 'onnx'` | Export module imports `onnx` before parsing or running export. | Install `onnx` in the active package environment, then retry. | Stop if dependencies cannot be installed; do not claim export support. |
| `ModuleNotFoundError: No module named 'onnxruntime'` | Default export check uses ONNX Runtime to run exported graphs. DNSMOS also uses ONNX Runtime. | Install `onnxruntime` or run export with `--no-check` only if parity checking is intentionally deferred. | Stop if user requested verified parity and ONNX Runtime is unavailable. |
| `Failed to import monkeytype. Please install it via $ pip install MonkeyType` | Export entry point explicitly requires MonkeyType before model loading. | Install `MonkeyType` in the same environment. | Stop until present; `--no-check` does not bypass this import. |
| `ModuleNotFoundError: No module named 'onnxsim'` or simplification failure | `--simplify` requires `onnxsim`; graph simplification can fail model checks. | Retry without `--simplify`, or install/fix `onnxsim`. The exporter keeps the unsimplified model if simplification check fails. | Stop if the deployment consumer specifically requires simplified graphs. |
| ONNX opset/runtime incompatibility | Chosen `--opset` is unsupported by the deployment consumer or runtime. | Use the consumer's supported opset. Parser default is `12`; `14` is a common explicit choice when supported. | Stop if target runtime cannot load any exported opset. |

Recommended export dependency install shape when the user approves package changes:

```bash
python -m pip install onnx onnxruntime MonkeyType
python -m pip install onnxsim  # only for --simplify
```

## 2. Model checkpoint or config failures

| Symptom | Likely cause | Action |
|---|---|---|
| `config.ini` not found | The model directory is incomplete or the model selector resolved to the wrong location. | Confirm the model directory contains `config.ini` and a checkpoint. If model selection itself is unclear, route to [python-enhancement](../../python-enhancement/SKILL.md). |
| Checkpoint not found for `--epoch best` or `--epoch latest` | Requested epoch selector is not available in the model directory. | Retry with the correct `--epoch` value or choose a valid model directory. |
| Export attempts a network download | A pretrained model name was used and the model is not cached. | If network is not allowed, stop and ask for a local model directory. |
| Export writes files to an unexpected directory | The positional `export_dir` is the ONNX target; inherited `--output-dir` is not the export target. | Re-run with the intended positional export directory. |

## 3. Export allclose warnings and numerical parity

During checked export, each component is run through ONNX Runtime and compared with PyTorch outputs. Warnings such as `Elements not close for <name>` mean an output exceeded the tolerance used by the exporter.

Actions:

1. Do not ignore the warning for a release/deployment artifact unless the user accepts the numerical risk.
2. Re-run without `--simplify` to separate simplification effects from base export effects.
3. Keep `--no-check` off for strict parity validation.
4. Validate the resulting directory with:

```bash
python scripts/check_export_artifacts.py /path/to/export-dir --check-npz
```

5. If ONNX Runtime is available, create a small consumer-side parity test using the generated NPZ files: feed `*_input.npz` arrays to the matching ONNX component and compare with `*_output.npz` arrays using tight tolerances.

Stop if parity is a requirement and warnings remain unexplained.

## 4. Missing or incomplete export artifacts

Run:

```bash
python scripts/check_export_artifacts.py /path/to/export-dir --check-npz --require-tar
```

Interpretation:

- Missing `enc.onnx`, `erb_dec.onnx`, `df_dec.onnx`, `config.ini`, or `version.txt` means the export directory is not deployment-ready.
- Missing `df_dec.onnx` usually means export stopped before the final component; rerun export after fixing the preceding exception.
- Missing `version.txt` means the final packaging step did not complete; do not publish the directory as a completed export.
- Missing NPZ files only matters for debug/reference validation, but if `--check-npz` was requested they are required.
- A tar archive is expected for convenient distribution. Require it only when packaging is part of the task.

The validator intentionally does not import `onnx` and cannot prove graph semantic correctness. It proves file presence, non-empty core artifacts, and optional NPZ readability/keys.

## 5. VoiceBank-DEMAND and DNS2020 metric failures

| Symptom | Likely cause | Action | Stop condition |
|---|---|---|---|
| `ModuleNotFoundError: No module named 'pystoi'` | Evaluation utilities import STOI support. | Install eval dependencies such as `pystoi`, `pesq`, and `scipy`. | Stop if objective metrics were requested and deps are unavailable. |
| `ModuleNotFoundError: No module named 'pesq'` | PESQ/composite metrics are unavailable. | Install `pesq`; some platforms need build tools. | Stop or reduce scope only if the user accepts omitted PESQ/composite metrics. |
| `ModuleNotFoundError: No module named 'scipy'` | Composite metrics require scipy-backed numerical routines. | Install `scipy`. | Stop for full VoiceBank/DNS2020 metric parity. |
| Dataset root assertion failure | Required subdirectories are missing. | Check the layouts in [export-and-evaluation.md](export-and-evaluation.md). | Stop; do not guess clean/noisy pairings. |
| DNS2020 count assertion failure | The script expects exactly 150 pairs for each selected subset. | Verify the benchmark subset and filename convention. | Stop if count/pairing is inconsistent. |
| `--csv-path-noisy` fails or creates no useful file | Noisy baseline metrics were not enabled. | Add `--compute-noisy-metric` for VoiceBank noisy CSVs. | Stop if the user requires noisy baseline CSV and compute time/deps are unavailable. |
| Multiprocessing worker hangs/errors | Metric workers are failing due dependency, platform, or memory issues. | Retry with `--metric-workers 0` or `1` for debugging, then scale up. | Stop if metrics still fail on one worker. |

## 6. DNSMOS failures

| Symptom | Likely cause | Action | Stop condition |
|---|---|---|---|
| `No DNSMOS api key found` | API mode needs `--api-key` or `DNS_AUTH_KEY`. | Ask for credentials or switch to local DNSMOS if local model downloads/cache are available. | Stop if neither credentials nor local models are available. |
| HTTP/network failure while scoring API | DNSMOS API endpoint unavailable, bad key, timeout, or network blocked. | Retry only if transient and permitted. Otherwise report API/network blocker. | Stop when network is unauthorized or repeated API failure persists. |
| Local DNSMOS tries to download ONNX models and fails | First local DNSMOS run downloads model files; network/cache unavailable. | Ask to allow download or preseed the DNSMOS model cache through approved means. | Stop if offline with no preseeded models. |
| `ModuleNotFoundError: No module named 'onnxruntime'` | DNSMOS local models are ONNX Runtime sessions. | Install `onnxruntime` or use API mode with credentials. | Stop if neither local nor API path is viable. |
| `ModuleNotFoundError` for `librosa`, `pandas`, `soundfile`, or `tqdm` | DNSMOS v5 helpers need additional audio/CSV packages. | Install the missing DNSMOS helper dependencies. | Stop for v5 directory/CSV workflows until dependencies are present. |
| Empty DNSMOS directory result | Input directory has no `.wav` clips. | Point to a directory of wav files or generate enhanced wavs first. | Stop if no wav files are provided. |
| DNSMOS noisy CSV missing from noisy-directory script | That script computes enhanced DNSMOS and disables noisy scoring in its current path. | Use enhanced CSV as the valid output; create a separate direct DNSMOS directory run if noisy baselines are required. | Stop if user specifically requires paired enhanced/noisy DNSMOS CSVs and no custom evaluation is allowed. |

## 7. Model summary and plotting failures

| Symptom | Likely cause | Action |
|---|---|---|
| `--type ptflops` fails | `ptflops` missing or unsupported layers. | Use `--type table` or install/debug `ptflops`. |
| Plot scripts fail on a headless system | Missing display/backend or plotting packages. | Use non-interactive matplotlib backend or skip plots. |
| Summary prints unexpected model family | Wrong `--model-base-dir` or epoch. | Confirm model selector and checkpoint through Python enhancement/model loading guidance. |

## 8. Routing reminders

- Basic enhancement command errors, audio loading errors, and model download/cache behavior belong in [python-enhancement](../../python-enhancement/SKILL.md).
- Dataset config, HDF5 generation, HDF5 filtering, and training data mutation belong in [training-data](../../training-data/SKILL.md).
- Rust `deep-filter`, model archive deployment, LADSPA, and PipeWire issues belong in [rust-realtime-deployment](../../rust-realtime-deployment/SKILL.md).
