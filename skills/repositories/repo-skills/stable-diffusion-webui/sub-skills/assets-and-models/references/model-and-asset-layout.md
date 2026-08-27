# Model and Asset Layout

This WebUI checkout treats model assets as user data, not as importable Python package resources. Directory decisions are made from launch flags and then runtime list/refresh functions scan known roots.

## Path Resolution

- `--data-dir`: base for user data; defaults to the WebUI checkout root when not provided.
- `--models-dir`: base for model directories; when set, it replaces `--data-dir/models`.
- `--ckpt`: explicit checkpoint file to add and load if it exists.
- `--ckpt-dir`: extra checkpoint search directory; searched before/default alongside `models/Stable-diffusion`.
- `--vae-dir`: extra VAE directory; searched in addition to `models/VAE` and checkpoint-adjacent VAE files.
- `--vae-path`: exact VAE checkpoint to use; overrides VAE settings and automatic resolution.
- `--embeddings-dir`: textual inversion embedding directory; defaults to `embeddings` under `--data-dir`.
- `--hypernetwork-dir`: hypernetwork directory; defaults to `models/hypernetworks`.
- `--lora-dir`: Lora network directory from the built-in Lora extension; defaults to `models/Lora`.
- `--lyco-dir-backcompat`: legacy LyCORIS network directory; defaults to `models/LyCORIS` and is also scanned by the Lora extension.

## Default Directory Catalog

| Asset | Default directory | Recognized suffixes | Notes |
| --- | --- | --- | --- |
| Checkpoints | `models/Stable-diffusion` | `.safetensors`, `.ckpt` | Files ending `.vae.ckpt` or `.vae.safetensors` are excluded from checkpoint list. |
| Checkpoint config override | beside checkpoint | `.yaml` | A file with the same basename as a checkpoint is used before state-dict guessing. |
| VAE | `models/VAE` | `.safetensors`, `.ckpt`, `.pt` | Also discovers `*.vae.safetensors`, `*.vae.ckpt`, and `*.vae.pt` beside checkpoints. |
| Embeddings | `embeddings` | `.pt`, `.bin`, `.safetensors`, embedded `.png`, `.webp`, `.jxl`, `.avif` | Preview images named `.preview.*` are ignored as embeddings. |
| Hypernetworks | `models/hypernetworks` | `.pt` | A hypothetical `None.pt` is ignored. |
| Lora/LyCORIS | `models/Lora`, `models/LyCORIS` | `.safetensors`, `.ckpt`, `.pt` | Lora, LoCon/LoHA, LoKR, IA3, GLora, OFT, Full, and Norm style modules are recognized by key layout. |
| ESRGAN | `models/ESRGAN` | `.pt`, `.pth` | If no local ESRGAN model is found, a built-in URL can be offered and downloaded on use. |
| RealESRGAN | `models/RealESRGAN` | `.pth` | Built-in RealESRGAN names map to remote `.pth` files and download on use if enabled. |
| DAT | `models/DAT` | `.pt`, `.pth` | Built-in DAT x2/x3/x4 entries can download on use if enabled. |
| HAT | `models/HAT` | `.pt`, `.pth` | Local files are listed; incompatible architecture logs a warning/fallback. |
| GFPGAN | `models/GFPGAN` | `.pth` | Looks for filenames containing `GFPGAN`; can download `GFPGANv1.4.pth`. |
| CodeFormer | `models/Codeformer` | `.pth` | Can download `codeformer-v0.1.0.pth`. |
| VAE approximation | `models/VAE-approx` | `.pt` | Auxiliary approximation weights, not the same as full VAE selection. |

## Checkpoint Discovery and Selection

- Checkpoint list refresh scans `models/Stable-diffusion`, `--ckpt-dir` when provided, and the explicit `--ckpt` file if it exists.
- If no checkpoint is found and `--no-download-sd-model` is not set, the default SD 1.5 safetensors URL can be downloaded into the checkpoint model directory.
- Checkpoint identifiers include title, model name, filename-derived names, legacy 8-character partial hash, SHA-256, and short SHA-256 when available.
- The list endpoint returns `title`, `model_name`, short `hash`, full `sha256`, `filename`, and adjacent `config` when found.
- If a configured checkpoint name is missing but at least one checkpoint exists, WebUI falls back to the first registered checkpoint and logs the fallback.
- If no checkpoints exist, WebUI reports every searched file/directory and instructs the operator to place a `.ckpt` or `.safetensors` file there.

## VAE Resolution Order

1. `--vae-path` wins and bypasses VAE settings.
2. If settings are configured to let global VAE override per-model preferences, `sd_vae` setting is tried before metadata/near-checkpoint matching.
3. Checkpoint user metadata key `vae` can specify `Automatic`, `None`, or a discovered VAE filename.
4. Near-checkpoint VAE files are selected when their basename starts with the checkpoint basename.
5. The `sd_vae` setting is used if it names an entry in the refreshed VAE list.
6. `None` means use the checkpoint/base VAE; an unresolved non-automatic VAE setting logs that it could not find the named VAE.

## Refresh and List Endpoints

Enable the WebUI API at launch before using these endpoints.

| Operation | Method/path | Result |
| --- | --- | --- |
| List checkpoints | `GET /sdapi/v1/sd-models` | Registered checkpoint records with hashes and adjacent config. |
| Refresh checkpoints | `POST /sdapi/v1/refresh-checkpoints` | Re-runs checkpoint discovery. |
| List VAEs | `GET /sdapi/v1/sd-vae` | `model_name` and `filename` for each discovered VAE. |
| Refresh VAEs | `POST /sdapi/v1/refresh-vae` | Re-runs VAE discovery. |
| List Loras | `GET /sdapi/v1/loras` | `name`, `alias`, `path`, and safetensors metadata. |
| Refresh Loras | `POST /sdapi/v1/refresh-loras` | Re-runs Lora/LyCORIS discovery. |
| List embeddings | `GET /sdapi/v1/embeddings` | Loaded and skipped embedding maps with shape/checkpoint metadata. |
| Refresh embeddings | `POST /sdapi/v1/refresh-embeddings` | Reloads textual inversion embeddings. |
| List hypernetworks | `GET /sdapi/v1/hypernetworks` | Hypernetwork `name` and `path`. |
| List upscalers | `GET /sdapi/v1/upscalers` | Upscaler `name`, `model_name`, `model_path`, and `scale`. |
| List RealESRGAN models | `GET /sdapi/v1/realesrgan-models` | RealESRGAN `name`, `path`, and `scale`. |

## Hashes and Metadata

- Checkpoint `.safetensors` metadata is read without loading tensors; `modelspec.thumbnail` is removed from the public metadata object.
- Checkpoints keep a legacy 8-character partial hash and a cached full SHA-256 when available; short titles use the first 10 SHA-256 characters.
- `--no-hashing` disables SHA-256 hashing for checkpoints to improve loading performance, at the cost of weaker identity and shorter UI/API hash fields.
- Lora safetensors metadata can define `ss_output_name` as an alias, `ss_base_model_version` for SDXL detection, `ss_v2` for SD2 detection, and hash fields used in infotext.
- Extra-network user metadata is stored beside the asset as JSON and can provide descriptions, activation text, preferred weights, negative text, SD version, notes, or checkpoint-preferred VAE.

## Optional Downloads

- Checkpoint autodownload is only for the default SD 1.5 fallback and can be disabled with `--no-download-sd-model`.
- CLIP autodownload can be disabled with `--do-not-download-clip` when a checkpoint omits CLIP.
- GFPGAN, CodeFormer, ESRGAN, RealESRGAN, and DAT model modules may download configured `.pth` files on first use when no local file satisfies the selected entry.
- A layout validator should not fetch any URLs or import WebUI modules; use it only to confirm expected folders and suffixes before runtime refresh/load.
