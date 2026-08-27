# Model runtime troubleshooting

Use this guide after a capability probe, cache plan, loader call, or export step fails. Keep reports PHI-free: include model ids, artifact formats, revisions, hashes, dependency versions, and synthetic parity outcomes; exclude raw clinical text, tokens from real notes, access tokens, and private machine paths.

## Quick triage order

1. Run the bundled capability probe without model loading:
   ```bash
   python scripts/backend_capability_probe.py --json
   ```
2. Confirm the requested model is known to the registry or is an explicit local artifact directory.
3. Confirm the requested runtime format exists (`pytorch`, `mlx-*`, `onnx`, `onnx-int8`, `ort-android`, `coreml`, `transformersjs`, etc.).
4. Confirm the model license and gated-access terms are acceptable.
5. Confirm cache state before setting offline mode for PHI workflows.
6. Validate tokenizer/span parity before using exported or quantized artifacts.

## Offline cache misses

Symptoms:

- `OPENMED_OFFLINE` or `local_only=True` is active and the loader reports that a model is not in the local cache.
- A local directory was expected, but tokenizer/config/weight files are missing.
- A mobile app reports `MISSING` rather than `READY` for a model entry.

Actions:

- Do **not** disable offline mode during PHI processing to make the error go away.
- On a connected preparation machine, prefetch the approved model revision and allowed artifact files, then transfer or mount the cache for the offline runtime.
- Keep cache variables consistent: `HF_HOME`, `HF_HUB_CACHE`, and OpenMed `cache_dir` should point to the same prepared storage during prefetch and execution.
- For local directories, ensure `config.json`, tokenizer assets, label metadata, and at least one runtime weight/graph file are colocated.
- For Android/Swift/browser, expose the model only after checksum/integrity checks succeed; partial downloads must not be treated as ready.

## Missing optional extras

Symptoms:

- `MissingOptionalDependencyError` names a backend.
- `backend_capability_probe.py` lists missing modules for `hf`, `mlx`, `onnx`, `onnx-runtime`, `coreml`, or `openvino`.
- A backend import works on one machine but not in a deployment image.

Actions:

- Install only the extra required by the chosen path:
  - Hugging Face/Torch loading: `pip install "openmed[hf]"`
  - Python MLX and MLX-LM: `pip install "openmed[mlx]"`
  - CoreML export: `pip install "openmed[coreml]"`
  - ONNX conversion: `pip install "openmed[onnx]"`
  - ONNX inference only: `pip install "openmed[onnx-runtime]"`
  - OpenVINO export/inference: `pip install "openmed[openvino]"`
- If a deployment forbids heavyweight packages, select an already exported ONNX/CoreML/MLX artifact instead of installing conversion tooling.
- Re-run the probe after installation; treat missing optional backends as okay unless the user's selected target requires them.

## Backend auto-selection surprises

Symptoms:

- A task expected MLX, but Hugging Face/Torch was selected.
- ONNX Runtime was expected, but the loader uses HF/Torch.
- A CPU fallback invalidates latency or privacy claims.

Actions:

- Set `OpenMedConfig(backend="mlx")`, `backend="hf"`, or `backend="onnx"` explicitly when target runtime matters.
- Probe platform and dependencies first. MLX requires Apple Silicon; ONNX requires an exported artifact and ONNX Runtime dependencies.
- Record the selected backend, device, provider, and artifact format in the run evidence.

## CUDA failures

Symptoms:

- `torch.cuda.is_available()` is false despite visible NVIDIA hardware.
- Out-of-memory during model load.
- Attention implementation errors on a DeBERTa/BERT-family model.

Actions:

- Verify the Torch wheel includes CUDA support and is compatible with the installed driver.
- Select a specific device (`cuda:0`, `cuda:1`) and check available memory before loading.
- Prefer a smaller tier, ONNX INT8, or CPU fallback if GPU memory is insufficient.
- If attention selection fails, set a conservative attention backend such as eager execution through `OPENMED_TORCH_ATTENTION_BACKEND=eager` or the corresponding config field.
- Do not claim GPU validation from hardware visibility alone; record a Python-level CUDA probe.

## MPS, MLX, and Apple Neural Engine issues

Symptoms:

- MLX is unavailable on Linux or Intel macOS.
- iOS Simulator fails a Swift MLX path.
- CoreML package runs on CPU instead of ANE.
- watchOS/visionOS refuses a model.

Actions:

- Use MLX only on Apple Silicon macOS or real iPhone/iPad devices. Route other hosts to HF/Torch, ONNX, or CoreML.
- Use CoreML for iOS Simulator, watchOS, visionOS, and older Apple OS fallbacks.
- For constrained platforms, require Nano-tier, INT8, resident-memory limits, and bounded sequence lengths before loading.
- For ANE claims, require compute-unit selection plus residency/performance evidence from Apple tooling; a `.mlpackage` file is not enough.

## ONNX Runtime and OpenVINO issues

Symptoms:

- `load_onnx_model(..., variant="int8")` cannot find `model_int8.onnx`.
- ONNX Runtime provider falls back unexpectedly.
- OpenVINO cannot compile a graph for GPU/NPU.
- Dynamic axes or logits output validation fails.

Actions:

- Check `openmed-onnx.json` and artifact filenames. Use the manifest artifact paths instead of deriving filenames by convention.
- For ONNX Runtime, list available providers and pass only providers supported by the host.
- For Android/mobile, generate or include the ORT Mobile model and operator config when minimal builds need them; otherwise document a dependency-only skip.
- For OpenVINO, select a requested device but record fallback. If no devices are reported, do not guess.
- Re-run export validation with synthetic inputs when changing opset, optimization, fp16, WebGPU, or INT8 settings.

## Tokenizer and span parity drift

Symptoms:

- Python and mobile/browser outputs use the same labels but shifted boundaries.
- A browser or Android decoder drops spaces, accents, RTL text, or multilingual graphemes.
- Fast and slow tokenizers produce different offsets.

Actions:

- Ship and use the same tokenizer assets as the Python reference: `tokenizer.json`, tokenizer config, special tokens, and vocabulary/merge files as applicable.
- Compare token IDs, character offsets, decoded span labels, and span boundaries exactly on synthetic cases.
- Keep the aggregation strategy and tie-breaking rules the same across runtimes.
- Fail closed on offset drift for PHI/PII workflows. A one-character boundary error can leak identifiers or redact the wrong substring.
- Do not include real span text in parity fixtures; store labels, offsets, hashes, and synthetic input markers.

## Quantized recall deltas

Symptoms:

- INT4/INT8 artifacts are smaller but lose direct-identifier recall.
- A recall-delta report exists but marks `certified: false`.
- Quantized output passes smoke tests but misses rare labels.

Actions:

- Reject over-budget quantized artifacts even when files were written successfully.
- Inspect per-label recall deltas, not only aggregate F1.
- For privacy runtimes, prioritize direct identifiers, dates, IDs, phone-like tokens, multilingual names, and critical leakage cases.
- Require parent-vs-candidate evaluation on the same synthetic or approved eval fixture set.
- Record quantization bits, group size, precision, calibration data description, label deltas, limit, and certification status.

## Model license and data-term blockers

Symptoms:

- A model is gated, private, DUA-restricted, source-available, GPL-tainted, or has unclear redistribution rights.
- A Hub token is required.
- A terminology/model bundle would embed restricted clinical vocabularies or datasets.

Actions:

- Stop until the user confirms they have rights to use and cache the model.
- Use user-supplied credentials only; never hard-code or serialize tokens.
- Do not bundle restricted terminology or DUA datasets into runtime artifacts.
- Prefer permissive-license models for generated draft/speculative artifacts and app-distributed bundles.
- Include license id, source repo id, revision, and access notes in PHI-free deployment evidence.

## Android toolchain and runtime blockers

Symptoms:

- Gradle cannot resolve the OpenMedKit dependency or ONNX Runtime Mobile.
- The model catalog does not list a desired artifact.
- The app sees a partial cache, ABI mismatch, or tokenizer exception.

Actions:

- Verify Gradle/JDK, min SDK, ABI packaging, and dependency repositories.
- Use catalog filters for `onnx`, `onnx-int8`, or `ort-android` formats; do not pass an MLX artifact to the Android ONNX runtime.
- Check `ModelCache.isAvailable(entry)` before loading from a directory.
- Ensure inference reads from app-local storage and does not need network permission.
- Validate tokenizer parity with synthetic cases before release.

## Swift / OpenMedKit blockers

Symptoms:

- MLX path fails in simulator.
- A Swift app cannot locate `id2label.json` or tokenizer assets.
- watchOS/visionOS rejects a full-size model.

Actions:

- Use real Apple Silicon hardware for Swift MLX validation; use CoreML for simulator workflows.
- Bundle or cache `openmed-mlx.json`, `config.json`, `id2label.json`, tokenizer assets, and weight files for MLX artifacts.
- For CoreML, bundle `.mlpackage`/`.mlmodelc` plus labels and tokenizer metadata.
- Enforce constrained-platform metadata before opening the model: Nano tier, INT8 precision, resident RAM ceiling, and sequence length ceiling.

## Browser blockers

Symptoms:

- WebGPU is absent or disabled.
- Threaded WASM fails because `SharedArrayBuffer` is unavailable.
- The loader rejects `https://`, CDN, `blob:`, or `data:` asset URLs.
- Transformers.js bundle validation reports missing files.

Actions:

- Use local/static model paths for PHI-processing assets.
- Provide COOP/COEP headers when threaded WASM is required; otherwise accept single-threaded WASM fallback.
- Include `config.json`, tokenizer assets, `transformersjs-contract.json`, and `onnx/model.onnx` or `onnx/model_quantized.onnx` as expected by the chosen loader.
- Do not use browser runtime logs or analytics to capture raw input, output spans, token strings, or cache paths.
