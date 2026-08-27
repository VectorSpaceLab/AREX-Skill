# Embedding, audio, and multimodal workflows

## EmbeddingOD contract

`EmbeddingOD` turns raw data into embeddings and then fits a standard PyOD detector on the embedding matrix.

```python
from pyod.models.embedding import EmbeddingOD

clf = EmbeddingOD(encoder='all-MiniLM-L6-v2', detector='KNN',
                  contamination=0.1, batch_size=32,
                  cache_embeddings=False, reduce_dim=None,
                  standardize=True, random_state=42)
clf.fit(train_items)
scores = clf.decision_function(test_items)
labels = clf.predict(test_items)
proba = clf.predict_proba(test_items)
```

Important details:

- `fit(X)` and `decision_function(X)` expect the raw input format accepted by the encoder: text strings, PIL images, audio clips, local paths, arrays, or a user callable's expected format.
- The encoder must return a 2-D numeric array of shape `(n_samples, n_features)`.
- Embeddings are `nan_to_num` processed, optionally standardized, optionally PCA-reduced, and cast to `float32` before detector fitting/scoring.
- String detector shortcuts include `KNN`, `LOF`, `ECOD`, `COPOD`, `HBOS`, `PCA`, `OCSVM`, `MCD`, `IForest`, `INNE`, `ABOD`, `CBLOF`, `COF`, `SOD`, `LODA`, `AutoEncoder`, `VAE`, `LUNAR`, `DIF`, `GMM`, `KDE`, `LMDD`, and `LOCI`. `DeepSVDD` needs a configured instance because it requires `n_features`.
- The default detector is `LUNAR`, which is torch-backed. If torch is not installed, choose a non-torch detector explicitly, e.g. `detector='KNN'`.

## Encoder options

| Encoder route | Shortcut or class | Extra/backend | Notes |
|---|---|---|---|
| SentenceTransformer text | `all-MiniLM-L6-v2`, `all-mpnet-base-v2`, a SentenceTransformer model id, a local model path, or a pre-instantiated `SentenceTransformer` | `pyod[embedding]` | Local paths are loaded with local-files-only behavior by the SentenceTransformer wrapper. |
| OpenAI text embeddings | `text-embedding-3-small`, `text-embedding-3-large`, or `OpenAIEncoder` | `pyod[openai]` and `OPENAI_API_KEY` | `EmbeddingOD.for_text('best')` uses `text-embedding-3-large`, `LUNAR`, and `cache_embeddings=True`; override detector to avoid torch. |
| HuggingFace text/image | `bert-base-uncased`, `dinov2-small`, `dinov2-base`, `dinov2-large`, `clip-vit-base`, or `HuggingFaceEncoder` | `pyod[huggingface]` | Uses `transformers`, `torch`, and `Pillow`. May need local cache/network unless a local model path is supplied. |
| Custom callable | Any `fn(X) -> ndarray` | Caller-owned | Good for deterministic tests, private encoders, or precomputed embeddings. |
| Audio feature encoder | `audio-mfcc` | `pyod[audio]` | Produces deterministic handcrafted acoustic features with no GPU. |
| MultiModalEncoder early fusion | `pyod.utils.encoders.MultiModalEncoder` | Per-modality extras | Concatenates modality embeddings/features before one detector. Supports `'passthrough'` numeric features. |

## Text presets

```python
from pyod.models.embedding import EmbeddingOD

fast = EmbeddingOD.for_text(quality='fast')       # MiniLM + KNN; no API key
balanced = EmbeddingOD.for_text(quality='balanced')  # mpnet + LUNAR
best = EmbeddingOD.for_text(quality='best')       # OpenAI large + LUNAR + cache
```

- `fast` needs `sentence-transformers` and avoids a torch-backed PyOD detector by using `KNN`; the encoder package may still bring its own torch stack.
- `balanced` needs `sentence-transformers`; because its PyOD detector is `LUNAR`, install/verify torch or override `detector='KNN'`/`'LOF'`.
- `best` needs the OpenAI package, `OPENAI_API_KEY`, and torch if keeping the default `LUNAR` detector. Use `cache_embeddings=True` for paid/API encoders to avoid repeated training encodes.

## Image presets

```python
clf = EmbeddingOD.for_image(quality='fast')      # dinov2-small + KNN
clf = EmbeddingOD.for_image(quality='balanced')  # dinov2-base + LOF
clf = EmbeddingOD.for_image(quality='best')      # dinov2-large + KNN
```

Image presets need `pyod[huggingface]` (`transformers`, `torch`, `Pillow`). They accept image objects compatible with the HuggingFace image processor. For reproducible CPU-only behavior or local model paths, instantiate `HuggingFaceEncoder` yourself and pass it as `encoder`.

## Audio paths

### Fast/balanced audio with EmbeddingOD

`EmbeddingOD.for_audio(...)` uses handcrafted acoustic features followed by a classic detector:

```python
from pyod.models.embedding import EmbeddingOD

clf = EmbeddingOD.for_audio('balanced', contamination=0.1,
                            random_state=42)  # audio-mfcc + KNN
clf.fit(train_clips)
scores = clf.decision_function(test_clips)
```

Input clips may be:

- file paths readable by `librosa`/`soundfile`,
- waveform arrays, mono or multi-channel,
- `(waveform, sample_rate)` tuples, which are resampled to the target sample rate.

The default `AudioFeatureEncoder` creates 74 features per clip: means and standard deviations of 20 MFCCs, 12 chroma bins, and 5 spectral descriptors (centroid, bandwidth, rolloff, zero-crossing rate, RMS). Stereo is averaged to mono, and very short clips are padded enough to produce at least one STFT frame.

Preset detector choices:

- `for_audio('fast')`: `audio-mfcc` + `IForest`.
- `for_audio('balanced')`: `audio-mfcc` + `KNN`.
- `for_audio('best')`: `audio-mfcc` + `LUNAR`; needs torch as well as audio dependencies.

### AudioAE

`AudioAE` is a log-mel reconstruction autoencoder for clip-level audio anomaly detection:

```python
from pyod.models.audio_ae import AudioAE

clf = AudioAE(n_mels=64, context=5, epoch_num=5,
              batch_size=256, random_state=0, verbose=0)
clf.fit(train_clips)
scores = clf.decision_function(test_clips)
```

It requires `pyod[torch,audio]`. Each clip is converted to overlapping log-mel context windows of width `n_mels * context`; a dense PyOD `AutoEncoder` is fit on frame windows; clip score is the mean frame reconstruction error. Train on mostly normal clips.

## MultiModalOD score fusion

`MultiModalOD` fits one detector per modality and fuses scores:

```python
from pyod.models.embedding import EmbeddingOD, MultiModalOD
from pyod.models.knn import KNN

clf = MultiModalOD(
    modalities={
        'text': EmbeddingOD(encoder=my_text_encoder, detector='KNN'),
        'tabular': KNN(),
    },
    combination='average',          # or 'maximization', 'median'
    standardize_scores=True,
    contamination=0.1,
)
clf.fit({'text': train_texts, 'tabular': X_train})
scores = clf.decision_function({'text': test_texts, 'tabular': X_test})
```

Rules:

- Input must be a dict whose keys match `modalities`.
- Each modality must have the same number of samples during fit.
- At test time, a modality value of `None` means that whole modality is missing; with score standardization enabled, it is imputed as mean score 0. If all modalities are missing, `decision_function` raises `ValueError`.
- Use `standardize_scores=True` unless per-modality score scales are intentionally comparable.
