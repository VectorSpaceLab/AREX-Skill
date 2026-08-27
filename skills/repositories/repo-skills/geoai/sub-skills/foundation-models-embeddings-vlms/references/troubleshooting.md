# Troubleshooting

This sub-skill is designed to stay safe by default. Most failures here are naming, optional-dependency, device, or cache issues rather than data corruption.

## Fast diagnosis table

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| `Unknown model` or `KeyError` for a foundation model | A Hugging Face repo ID or human-readable name was used where GeoAI expects a registry key | Normalize to the lower-case GeoAI key and re-check with `scripts/list_geoai_models.py --query <text>` or `list_foundation_models()`. |
| `ImportError: terratorch` | TerraTorch optional extra is missing | If the user only needs metadata, stay on `list_foundation_models()` / `get_foundation_model_info()`. If they need backbone loading, install the TerraTorch extra outside this skill. |
| `load_foundation_model` raises `NotImplementedError` | The registry entry is not TerraTorch-backed | Do not force-load it. Use metadata only, or hand off to a workflow that uses a different module. |
| Prithvi download fails or tries to fetch files | No cached config/checkpoint was provided | Use local `config_path` and `checkpoint_path` when available. Otherwise explain that `load_prithvi_model()` downloads from Hugging Face. |
| DINOv3 load fails | Missing or wrong `weights_path`, or the user expects offline use | Pass a local weight file, or make it explicit that the default loader may fetch weights. `DINOV3_LOCATION` only changes the source location, not the need for weights. |
| Moondream or BLIP model access is slow/fails | Model download, cache, or band selection problem | Pick the smallest suitable model, provide a cache path if needed, and choose RGB-like bands explicitly for multispectral rasters. |
| vLLM calls fail immediately | Base URL or server mode mismatch | Confirm the server is up, the base URL ends with `/v1`, and the correct `offline` mode is selected. |
| `offline=True` fails for vLLM | `vllm` package is missing or local memory is insufficient | Use server mode if possible; otherwise report the missing optional dependency. |
| TESSERA functions fail with missing package errors | `geotessera` is not installed | Treat TESSERA as optional. Use registry/dataset guidance, or route the user to a different workflow until the dependency is available. |
| AlphaEarth / Google satellite download is rejected | Invalid year or band selection | Valid years are 2017-2025; bands are `A00`-`A63`. Use registry metadata or existing embeddings instead of downloading if possible. |
| Captioning downloads a spaCy model | `en_core_web_sm` is missing and `auto_download=True` | Set `auto_download=False` when you want a no-network path, or use `extract_features_from_caption()` on an existing caption only. |

## Name normalization cheat sheet

| Input | Preferred GeoAI form | Notes |
| --- | --- | --- |
| `ibm-nasa-geospatial/Prithvi-EO-2.0-300M` | `prithvi-eo-2.0-300m` | Use the registry key for metadata; use `Prithvi-EO-2.0-300M(-TL)` for the Prithvi loader. |
| `Prithvi-EO-2.0-300M-TL` | Prithvi loader model name | Not a registry key. |
| `g-astruc/UniverSat` | `universat` | Registry key and model-family name are different layers. |
| `vikhyatk/moondream2` | Moondream model ID | Safe default Moondream model. |
| `Qwen/Qwen2-VL-7B-Instruct` | vLLM model ID | Use with `VLLMGeo` or the `vllm_*` wrappers. |
| `google_satellite` | Embedding dataset key | GeoAI key for AlphaEarth/Google satellite embeddings. |
| `tessera` | Embedding dataset key / workflow family | Use `tessera_*` for GeoTessera-backed operations. |

## Optional dependency map

| Capability | Optional dependency | What to do if missing |
| --- | --- | --- |
| TerraTorch-backed foundation model loading | `terratorch` | Keep to registry metadata or install the extra outside this skill. |
| TorchGeo embedding datasets | `torchgeo` | Use the registry metadata only, or work from existing arrays/files. |
| TESSERA access | `geotessera` | Treat TESSERA as unavailable; do not attempt a fallback download from this skill. |
| vLLM offline mode | `vllm` | Use server mode instead, or report the package requirement. |
| Caption feature extraction | `spacy` + `en_core_web_sm` | Use caption-only paths or disable auto-download. |
| BLIP captioning | `transformers` | Route to another model family or report the missing dependency. |
| GPU acceleration | CUDA/MPS/CPU device selection | Use `get_device()` or an explicit `device=` argument. CPU is fine for registry, clustering, and export tasks. |

## Existing-embedding no-download path

If the user already has embeddings and wants clustering, a classifier baseline, or GeoTIFF export, stay on the embedding-array path:

1. Load or receive the embeddings array.
2. Use `cluster_embeddings()` to group samples.
3. Use `train_embedding_classifier()` for a lightweight baseline.
4. Use `compare_embeddings()` or `embedding_similarity()` for lookup/change-style comparisons.
5. Use `embedding_to_geotiff()` to export dense features.

This avoids model downloads entirely.

## Route boundary reminders

- If the task is **training or fine-tuning**, hand it off to the training sub-skill.
- If the task is **segmentation/detection outputs**, hand it off to the inference sub-skill.
- If the task is **download/tiling/prep**, hand it off to the geospatial-data-pipelines sub-skill.

## High-friction cases to flag early

- A user supplies a Prithvi Hugging Face repo ID and expects it to work as a GeoAI registry key.
- A user asks for vLLM detection but has no running server and no local `vllm` install.
- A user asks for TESSERA coverage without `geotessera` installed.
- A user wants Moondream on a 4- or 6-band raster and did not specify which bands should be used as RGB.
