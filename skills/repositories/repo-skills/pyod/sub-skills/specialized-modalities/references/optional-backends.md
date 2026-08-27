# Optional backends and neural detector decisions

## Valid PyOD extras for this sub-skill

Quote extras in shells that expand brackets, e.g. `pip install 'pyod[torch,graph]'`.

| Extra | Installs | Enables here | Common failure symptom |
|---|---|---|---|
| `torch` | `torch>=2.0` | Torch-backed tabular/neural detectors, `LSTMAD`, `AnomalyTransformer`, `AudioAE`'s inner autoencoder, and `EmbeddingOD` when the detector is `LUNAR`, `DIF`, `AutoEncoder`, or `VAE` | `ModuleNotFoundError: No module named 'torch'` or a torch-backed detector import fails. |
| `graph` | `torch>=2.0`, `torch_geometric>=2.0` | Graph detectors `DOMINANT`, `CoLA`, `CONAD`, `AnomalyDAE`, `GUIDE`, `Radar`, `ANOMALOUS`, `SCAN` | `No module named 'torch_geometric'`. |
| `embedding` | `sentence-transformers>=5.0.0` | SentenceTransformer text encoders such as `all-MiniLM-L6-v2` and `all-mpnet-base-v2` | `Encoder backend 'sentence_transformer' requires ...`. |
| `openai` | `openai>=1.0` | OpenAI embedding encoders, including `text-embedding-3-*` presets | Package import succeeds but API calls fail without `OPENAI_API_KEY`. |
| `huggingface` | `transformers>=4.25.1`, `torch>=2.0`, `Pillow` | DINOv2/CLIP image encoders and HuggingFace text encoders | `No module named 'transformers'`, image processor errors, or model download/cache failures. |
| `audio` | `librosa>=0.10`, `soundfile` | `audio-mfcc`, `EmbeddingOD.for_audio`, and audio file/waveform feature extraction | `AudioFeatureEncoder requires 'librosa' and 'soundfile'`. |
| `all` | Every optional package | Full optional stack | Large install; may pull unwanted backend variants. Prefer targeted extras. |

A common mistake is `pyod[pytorch]`; pip treats an unknown extra as a warning and still installs PyOD core. The valid extra name is `torch`.

## Torch/neural detector notes

Torch-backed detectors are useful when tabular or embedding features need a learned representation, but they are not the default recommendation for very small data. Prefer simple classic detectors unless the user has enough samples and a reason for representation learning.

Representative torch-backed classes and caveats:

| Class | Import | Main requirements/caveats |
|---|---|---|
| `AutoEncoder` | `pyod.models.auto_encoder.AutoEncoder` | Inherits `BaseDeepLearningDetector`; reduce `batch_size` below sample count because the base loader drops the last incomplete batch. |
| `VAE` | `pyod.models.vae.VAE` | Similar base contract; `epoch_num`, encoder/decoder widths, `latent_dim`, `beta`, `capacity`; watch small batches and non-finite inputs. |
| `DeepSVDD` | `pyod.models.deep_svdd.DeepSVDD` | Requires `n_features` in the constructor; center validation is strict. |
| `DIF` | `pyod.models.dif.DIF` | Deep representation ensemble plus isolation forests; can be expensive with large `n_ensemble`/`n_estimators`. |
| `LUNAR` | `pyod.models.lunar.LUNAR` | Default detector for `EmbeddingOD`; needs torch even when the encoder does not. Use `n_epochs` small for smoke tests. |
| `DevNet` | `pyod.models.devnet.DevNet` | Supervised/semi-supervised deviation network; `fit(X, y)` requires labels with known outliers. Do not use as unsupervised drop-in. |
| `AE1SVM`, `ALAD`, `AnoGAN`, `SO_GAAL`, `MO_GAAL` | respective `pyod.models.*` modules | Older/deeper neural detectors; start with tiny epochs and explicit data validation. |
| `LSTMAD` | `pyod.models.ts_lstm.LSTMAD` | Time-series only; source implementation trains on CPU; needs at least `window_size + 10` timestamps. |
| `AnomalyTransformer` | `pyod.models.ts_anomaly_transformer.AnomalyTransformer` | Time-series only; set `device='cpu'` unless GPU was probed; `d_model` must be divisible by `n_heads`. |
| `AudioAE` | `pyod.models.audio_ae.AudioAE` | Needs both `torch` and `audio`; scores clips after log-mel window reconstruction. |

Small-data checklist for neural detectors:

- Ensure `n_samples > batch_size`, or lower `batch_size`.
- Use low epochs and small hidden dimensions for smoke checks.
- Set `random_state` where supported.
- Explicitly set `device='cpu'` for classes exposing a device parameter when no accelerator has been verified.
- Do not rely on contamination thresholds from tiny training sets; inspect raw `decision_scores_` rankings.

## Device and accelerator policy

- Core CPU time-series detectors do not require torch or GPU.
- PyOD's minimum verified environment for this skill was CPU/base only; optional GPU behavior is not a standing claim.
- If CUDA/ROCm/MPS matters, first install the correct PyTorch build for that accelerator, then install the PyOD extra. A later `pip install 'pyod[torch]'` normally leaves an already-satisfied torch package in place.
- Some classes auto-select devices (`BaseDeepLearningDetector` chooses CUDA if `torch.cuda.is_available()`, `AnomalyTransformer(device='auto')`, `HuggingFaceEncoder(device=None)`). Set an explicit CPU device when reproducibility or CPU-only validation matters.

## Credentials and model/cache access

| Backend | Credential/cache consideration |
|---|---|
| OpenAI | Real embedding calls require `OPENAI_API_KEY`. Do not print the key; only report whether it is present. Use `cache_embeddings=True` for training encodes to reduce API cost. |
| HuggingFace/SentenceTransformer | Public remote model ids may download weights. For air-gapped or deterministic runs, pass a local model directory or a pre-instantiated model object. Private/gated models may require `HF_TOKEN` or `HUGGINGFACE_HUB_TOKEN`. |
| Audio | File paths must be readable by `librosa`/`soundfile`; arrays and `(waveform, sample_rate)` tuples avoid file I/O. |

## Backend probe

Run the bundled probe before choosing install advice:

```bash
python scripts/modality_backend_probe.py --format text
python scripts/modality_backend_probe.py --require graph --require torch
python scripts/modality_backend_probe.py --require openai --require-credentials
```

The probe performs import/spec checks only. It does not download models, call APIs, train detectors, or start servers.
