# Extra Networks and Lora

Extra networks are prompt-addressable model modifiers. This WebUI registers built-in hypernetworks and the bundled Lora extension as extra networks; textual inversion embeddings use their token names directly through the embedding database.

## Prompt Syntax

| Asset | Prompt form | Notes |
| --- | --- | --- |
| Lora/LyCORIS | `<lora:name:weight>` | `name` may be filename stem or alias, depending on settings and alias collisions. |
| Lora with separate strengths | `<lora:name:te:unet>` | `te` controls text encoder strength; `unet` defaults to `te` if omitted. |
| Lora with dynamic dimension | `<lora:name:te:unet:dyn>` | `dyn` can also be named as `dyn=value`. |
| Lora named args | `<lora:name:te=0.7:unet=0.9:dyn=16>` | Named values override positional values. |
| LyCORIS alias | `<lyco:name:weight>` | `lyco` is an alias registered to the same Lora extra-network handler. |
| Hypernetwork | `<hypernet:name:weight>` | The UI inserts the default multiplier when clicking a hypernetwork card. |
| Textual inversion | `embedding_token` | The extra networks UI inserts the embedding name directly into prompt or negative prompt. |

## Discovery Rules

- Lora directory defaults to `models/Lora`; legacy LyCORIS directory defaults to `models/LyCORIS`.
- `--lora-dir` and `--lyco-dir-backcompat` control the scanned directories.
- Lora/LyCORIS scanning accepts `.pt`, `.ckpt`, and `.safetensors` recursively.
- Hypernetwork scanning accepts `.pt` recursively under `--hypernetwork-dir` and ignores a file named `None.pt`.
- Textual inversion scans each configured embedding directory recursively and accepts `.pt`, `.bin`, `.safetensors`, and images with embedded TI payloads; plain preview images are ignored.
- Extra networks UI preview files are sidecar images next to asset basenames or embedded safetensors cover images when metadata includes them.

## Lora Module Styles

The built-in Lora extension attempts multiple module types against the keys inside the network file:

- Standard LoRA layers.
- Hada/LoHA-style LyCORIS layers.
- LoKR-style LyCORIS layers.
- IA3, GLora, Full, Norm, and OFT/COFT variants.
- Bundled textual inversion embeddings stored under `bundle_emb` keys.

A file may be discovered but still fail at activation when its keys do not match the loaded base model architecture, when no module type accepts its weights, or when layer shapes are incompatible.

## Names, Aliases, and Hashes

- The primary network name is the filename stem.
- Safetensors metadata key `ss_output_name` can provide an alias.
- If an alias collides with another alias or a forbidden alias, WebUI falls back to filename behavior for disambiguation.
- Forbidden aliases include `none` and `Addams`.
- Lora hashes are the first 12 characters of metadata or cached SHA-derived hash values; when enabled, generated infotext records `Lora hashes`.
- When pasting infotext, WebUI can use recorded Lora hashes to replace ambiguous prompt aliases with the currently known alias for the matching file.

## Version Filtering

- Lora safetensors metadata can detect SDXL when `ss_base_model_version` starts with `sdxl_`.
- Metadata key `ss_v2=True` marks SD2.
- Other metadata-bearing files default to SD1; files with no metadata are `Unknown`.
- The UI can hide incompatible SD1/SD2/SDXL networks unless `Always show all networks on the Lora page` is enabled.
- A network that appears in `/sdapi/v1/loras` but not in the extra networks card grid is often filtered by current checkpoint family, unknown-version hiding, missing refresh, or an alias/name collision.

## Lora Activation Behavior

- WebUI parses all prompt extra-network tags before processing and activates registered networks in prompt order.
- Lora settings can add one selected network to every prompt even when the prompt does not explicitly mention it.
- Multiple Loras are supported; the loaded-network cache is bounded by the `lora_in_memory_limit` setting.
- If a requested Lora cannot be found, WebUI adds a `Lora not found` comment and can optionally print to console or show a Gradio warning.
- If a Lora loads but some target layers fail during application, generation comments can include `Networks with errors` and debug logs name the failing layer.

## User Metadata Sidecars

Sidecar metadata is JSON stored beside the asset basename. Useful keys include:

- `description`: visible card description.
- `activation text`: prompt text appended when clicking a Lora card.
- `preferred weight`: card-inserted Lora strength.
- `negative text`: negative prompt text inserted from the Lora card.
- `sd version`: manual SD1/SD2/SDXL classification override.
- `notes`: operator notes for the card.
- `vae`: checkpoint-card preferred VAE value, using `Automatic`, `None`, or a discovered VAE filename.

## API Touchpoints

- `GET /sdapi/v1/loras` lists discovered Lora records with name, alias, path, and safetensors metadata.
- `POST /sdapi/v1/refresh-loras` re-runs Lora/LyCORIS scanning.
- `GET /sdapi/v1/hypernetworks` lists hypernetwork names and paths.
- `GET /sdapi/v1/embeddings` separates loaded embeddings from skipped embeddings; skipped usually means a shape mismatch for the loaded checkpoint.
- `POST /sdapi/v1/refresh-embeddings` reloads embeddings after adding or removing files.
