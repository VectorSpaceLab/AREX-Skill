# Asset Troubleshooting

Use this guide before loading model weights when a model, VAE, extra network, embedding, or upscaler is missing or suspicious.

## Missing Checkpoint

Signals:

- Startup or reload reports `No checkpoints found`.
- `GET /sdapi/v1/sd-models` returns an empty list.
- UI falls back to a different checkpoint and logs `Checkpoint ... not found; loading fallback ...`.

Triage:

1. Confirm the intended launch path policy: `--models-dir` replaces the default `models` root, while `--ckpt-dir` adds a checkpoint directory and `--ckpt` adds one explicit file.
2. Put regular checkpoints in `models/Stable-diffusion` or the directory passed to `--ckpt-dir`.
3. Use `.safetensors` or `.ckpt`; do not name a regular checkpoint `*.vae.ckpt` or `*.vae.safetensors` because those are blacklisted from checkpoint discovery.
4. If an adjacent YAML config is required, place `checkpoint_basename.yaml` beside the checkpoint.
5. Refresh with `POST /sdapi/v1/refresh-checkpoints`, then verify `GET /sdapi/v1/sd-models` includes the expected `title` or `model_name`.
6. If a default SD 1.5 download is unwanted, launch with `--no-download-sd-model` and provide a local checkpoint.

## Wrong Data or Models Directory

Signals:

- Assets exist on disk but all list endpoints are empty.
- Placeholder directories under a different root are being populated.

Triage:

1. Resolve `--data-dir` first; default model root is `--data-dir/models`.
2. If `--models-dir` is set, ignore `--data-dir/models` for model assets and use `--models-dir/<asset-subdir>` instead.
3. Remember that `--embeddings-dir` defaults under `--data-dir`, not under `models`.
4. Check specialized overrides: `--ckpt-dir`, `--vae-dir`, `--hypernetwork-dir`, `--lora-dir`, `--lyco-dir-backcompat`, and the upscaler model-path flags.
5. Run `scripts/validate_asset_layout.py --data-dir <data> --models-dir <models> --json` with the same path policy to catch misplaced files without importing WebUI.

## VAE Not Discovered or Wrong VAE Loaded

Signals:

- `GET /sdapi/v1/sd-vae` omits the VAE.
- Logs say `Couldn't find VAE named ...; using None instead`.
- A checkpoint-specific VAE does not apply.

Triage:

1. Place general VAEs in `models/VAE` or the directory passed to `--vae-dir` with `.safetensors`, `.ckpt`, or `.pt` suffix.
2. Place checkpoint-adjacent VAEs as `checkpoint_basename.vae.safetensors`, `checkpoint_basename.vae.ckpt`, or `checkpoint_basename.vae.pt` beside the checkpoint or under `--ckpt-dir`.
3. Refresh with `POST /sdapi/v1/refresh-vae` and inspect `GET /sdapi/v1/sd-vae`.
4. Check whether `--vae-path` is set; it overrides settings and metadata.
5. Check checkpoint user metadata key `vae`; `Automatic` allows automatic resolution, `None` disables an external VAE, and any other value must match a discovered VAE filename.
6. If global VAE override settings are enabled, the global `sd_vae` setting can win over per-model preferences.

## Unsafe Pickle or Safetensors Choice

- Prefer `.safetensors` for checkpoints, VAEs, and Lora because metadata can be read without executing pickle deserialization.
- `.ckpt`, `.pt`, `.bin`, and some image-embedded embeddings may require PyTorch or custom deserialization paths at runtime.
- Do not launch with `--disable-safe-unpickle` unless the asset source is trusted and the security tradeoff is accepted by the operator.
- If an asset from an untrusted source is only available as `.ckpt` or `.pt`, convert or replace it rather than weakening unpickle checks.

## Hash Mismatch or Slow Hashing

Signals:

- A checkpoint title lacks the expected short SHA-256.
- Lora infotext hash does not map back to a local file.
- Startup or checkpoint switch spends time calculating hashes.

Triage:

1. Confirm whether `--no-hashing` is set; it improves load performance but weakens checkpoint identity in UI/API fields.
2. For checkpoints, compare full SHA-256 from `GET /sdapi/v1/sd-models` when available, not the legacy 8-character partial hash.
3. For Lora, refresh loras and compare `/sdapi/v1/loras` metadata plus `Lora hashes` infotext.
4. If a file was overwritten in place, refresh the relevant list and clear stale expectations about old titles/hashes.
5. Treat a hash mismatch as a different asset until provenance is re-established.

## Lora or LyCORIS Not Appearing

Signals:

- File exists but no card appears in the Lora tab.
- `GET /sdapi/v1/loras` is missing the file.
- Prompt tag produces `Lora not found`.

Triage:

1. Place files under `--lora-dir` or `--lyco-dir-backcompat` using `.safetensors`, `.ckpt`, or `.pt` suffix.
2. Refresh with `POST /sdapi/v1/refresh-loras` or the Lora tab refresh button.
3. Use the filename stem in `<lora:filename_stem:1>` if alias behavior is uncertain.
4. Check for alias collisions or forbidden aliases; colliding aliases can force filename lookup behavior.
5. If the API lists the file but the card is hidden, check SD1/SD2/SDXL filtering, unknown-version hiding, and whether a compatible checkpoint is loaded.
6. For LyCORIS-style files, use either `<lora:name:weight>` or the registered `<lyco:name:weight>` alias.

## Incompatible Lora, LoCon, LoHA, LoKR, or OFT

Signals:

- Generation comments include `Networks with errors`.
- Console/debug logs mention layer shape errors or `Could not find a module type`.
- Output ignores the requested network despite discovery.

Triage:

1. Check metadata-derived SD version against the loaded base checkpoint family.
2. Prefer a Lora trained for the same SD major family and architecture: SD1, SD2, or SDXL.
3. Try filename-stem prompt syntax to avoid alias mismatch: `<lora:stem:0.7>`.
4. Lower strength to isolate over-application artifacts from true incompatibility.
5. If the file is a newer LyCORIS/OFT variant, verify that its key layout is among the built-in supported module types; otherwise route to extension implementation work rather than asset placement.

## Embedding Missing or Skipped

Signals:

- `GET /sdapi/v1/embeddings` shows the token under `skipped`.
- The token inserts in prompt but has no effect.

Triage:

1. Place embeddings under `--embeddings-dir` and refresh with `POST /sdapi/v1/refresh-embeddings`.
2. Use `.pt`, `.bin`, `.safetensors`, or an image format with embedded `sd-ti-embedding` data.
3. Check the `shape`, `sd_checkpoint`, and `sd_checkpoint_name` fields from the embeddings endpoint.
4. A skipped embedding usually means its vector shape does not match the currently loaded model family.

## Hypernetwork Missing

Signals:

- `GET /sdapi/v1/hypernetworks` omits the file.
- `<hypernet:name:weight>` has no effect.

Triage:

1. Place `.pt` hypernetworks under `--hypernetwork-dir`.
2. Avoid the basename `None` because `None.pt` is intentionally ignored.
3. Reload/refresh hypernetworks through the UI or by triggering the same runtime refresh path used by the WebUI.
4. Confirm the prompt uses the filename stem: `<hypernet:stem:1.0>`.

## Upscaler Fallback or Missing Weights

Signals:

- Upscale operation returns the original image or only basic resize.
- Logs say `Unable to load ESRGAN model`, `Unable to load RealESRGAN model`, `DAT data missing`, `No GFPGAN model found`, or `No codeformer model found`.

Triage:

1. Check `GET /sdapi/v1/upscalers` for the selected upscaler name and `model_path`.
2. Put local ESRGAN/HAT/DAT files as `.pt` or `.pth`; RealESRGAN/GFPGAN/CodeFormer use `.pth`.
3. Use specialized path flags for face restoration and upscalers when the model root is nonstandard: `--gfpgan-models-path`, `--codeformer-models-path`, `--esrgan-models-path`, `--bsrgan-models-path`, `--realesrgan-models-path`, and `--dat-models-path`.
4. Built-in RealESRGAN, DAT, ESRGAN, GFPGAN, and CodeFormer entries may download weights on first use; if the environment is offline, place the expected local `.pth` file instead.
5. Architecture warnings from Spandrel mean the file was found but does not match the selected upscaler family; select a compatible model or move it to the correct family directory.

## Refresh Expectations

- Refresh endpoints rescan disk state; they do not validate tensor compatibility by loading every model.
- List endpoints can expose paths and metadata for discovered assets even when later activation/load will fail.
- After changing launch path flags, restart WebUI; refresh endpoints cannot change startup path policy.
- After overwriting files in place, refresh the relevant list and retry with the filename stem rather than stale title/hash aliases.
