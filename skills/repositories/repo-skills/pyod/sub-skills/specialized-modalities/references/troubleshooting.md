# Specialized modality troubleshooting

## Time-series symptoms

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Expected 1D or 2D input` | Input has shape such as `(batch, time, channels)` or object dtype. | Convert to a numeric array shaped `(n_timestamps,)` or `(n_timestamps, n_channels)`. |
| `Time series length ... shorter than ... window_size` | Not enough timestamps for the requested detector/window. | Lower `window_size`, collect more timestamps, or use dense `SpectralResidual` for very short series. |
| `Not enough subsequences ... for n_clusters` | `KShape`/`SAND` has fewer windows than clusters. | Reduce `n_clusters`, reduce `window_size`, increase series length, or increase `batch_size` for SAND's initial batch. |
| `MatrixProfile ... does not support decision_function/predict` | Matrix Profile is transductive. | Use `decision_scores_`/`labels_` immediately after `fit()`. For out-of-sample scoring, use `TimeSeriesOD`, `KShape`, `SpectralResidual`, `SAND`, `LSTMAD`, or `AnomalyTransformer`. |
| Channel-count mismatch | Model was fitted on a different number of channels than the new series. | Keep channel ordering/count fixed between fit and scoring, or refit. |
| Torch time-series detector import fails (`No module named 'torch'` or `NameError: name 'nn' is not defined` for `ts_anomaly_transformer`) | The `torch` extra is absent; `ts_anomaly_transformer` defines torch modules at import time. | Install `pip install 'pyod[torch]'` or avoid `LSTMAD`/`AnomalyTransformer`; for core checks use `TimeSeriesOD`, `SpectralResidual`, `MatrixProfile`, `KShape`, or `SAND`. |
| Torch time-series detector is slow or memory-heavy | Default epochs/model width/window count too large. | Use explicit CPU smoke settings: small `window_size`, `epochs`, `d_model`, `n_layers`, and `batch_size`; only scale after shape checks pass. |

## Graph symptoms

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No module named 'torch_geometric'` | `pyod[graph]` not installed or wrong environment active. | Install `pip install 'pyod[graph]'` after selecting the correct torch backend. |
| `edge_index required when X is not a PyG Data object` | Called `fit(X)` with NumPy features but omitted edges. | Call `fit(X, edge_index=edge_index)` or build a PyG `Data` object. |
| `requires node features (data.x)` | Used an attributed detector without `data.x`. | Add `x` with shape `(n_nodes, n_features)` or use `SCAN`, the structure-only detector. |
| Structure-only `Data` has wrong number of scores | `num_nodes` missing, so isolated nodes are invisible. | Use `Data(edge_index=edge_index, num_nodes=n_nodes)` when `x` is absent. |
| `GUIDE requires higher-order structures (triangles)` | Graph has no triangle motifs for GUIDE. | Use `DOMINANT`, `CoLA`, `SCAN`, or another detector; do not force GUIDE on triangle-free graphs. |
| `NotImplementedError` on graph `decision_function` or `predict` | Graph detectors are transductive. | Fit on the graph to be scored and read `decision_scores_`/`labels_` after `fit()`. |

## Embedding and multimodal symptoms

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Encoder backend 'sentence_transformer' requires ...` | Missing `sentence-transformers`. | Install `pip install 'pyod[embedding]'` or pass a callable/precomputed encoder. |
| OpenAI encoder import works but calls fail | Missing/invalid `OPENAI_API_KEY`, quota, network, or rate limit. | Set the credential outside code, use `cache_embeddings=True`, lower batch size, and retry with backoff. Never hard-code the key in skill files. |
| HuggingFace/DINO model download fails | No network, cache miss, private model, or missing token. | Use a local model directory or pre-instantiated model; set `HF_TOKEN`/`HUGGINGFACE_HUB_TOKEN` only when needed for private models. |
| `EmbeddingOD` with no explicit detector fails for missing torch | Default detector is `LUNAR`. | Install `pyod[torch]` or pass `detector='KNN'`, `'LOF'`, `'ECOD'`, `'IForest'`, etc. |
| Encoder returned wrong sample count | Callable/custom encoder produced a matrix with rows not equal to `len(X)`. | Fix the encoder to return `(n_samples, n_features)` and validate with a tiny batch. |
| `MultiModalOD expects a dict` or missing modality key | Fit/scoring input does not match modality names. | Pass a dict with the same keys used in `modalities`; all modalities must be present at fit. |
| `No modalities available in test input` | Every test modality is `None`. | Provide at least one modality. If some modalities are missing, leave only those values as `None`. |
| Multimodal threshold feels miscalibrated when a modality is missing | Missing modality imputation reduces score variance. | Inspect `decision_function()` scores and apply a custom threshold for the missing-modality deployment setting. |

## Audio symptoms

| Symptom | Likely cause | Recovery |
|---|---|---|
| `AudioFeatureEncoder requires 'librosa' and 'soundfile'` | `pyod[audio]` not installed. | Install `pip install 'pyod[audio]'`. For `AudioAE`, install `pip install 'pyod[torch,audio]'`. |
| Empty audio input raises `ValueError` | Audio encoders require at least one clip. | Pass a non-empty list of file paths, waveform arrays, or `(waveform, sample_rate)` tuples. |
| Stereo/multichannel results differ from expected | PyOD averages multi-channel waveforms to mono. | Preprocess audio yourself if channel-specific anomaly detection is required. |
| Very short clip behaves oddly | Short clips are padded to produce at least one frame/window. | Use longer clips or aggregate clips into consistent durations before fitting. |
| `AudioAE` training unstable on few clips | Frame windows or clip count too small for an autoencoder. | Start with `EmbeddingOD.for_audio('fast'/'balanced')`; if using `AudioAE`, reduce `batch_size`/epochs and train on mostly normal clips. |

## Optional-extra install symptoms

| Symptom | Likely cause | Recovery |
|---|---|---|
| Installed `pyod[pytorch]` but torch still missing | `pytorch` is not a valid PyOD extra; pip only warned. | Install `pip install 'pyod[torch]'`. |
| GPU expected but model runs on CPU | Torch build or class device auto-selection differs from expectation; no accelerator was verified. | Probe torch and device availability, install the correct torch variant, and pass explicit `device='cuda'` only after verification. |
| Torch import succeeds but training crashes on tiny data | Batch size can exceed usable samples; some loaders drop incomplete batches. | Lower `batch_size` below `n_samples`, use fewer epochs, and check for finite numeric input. |
| Need a safe diagnosis without installing anything | Environment status unknown. | Run `scripts/modality_backend_probe.py --format text`; it imports/probes only and gives install hints. |
