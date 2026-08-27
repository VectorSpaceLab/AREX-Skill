# Captioning and Preprocessing

This reference explains the safe planning flow for LTX dataset preparation: split scenes if needed, caption a small spot-check first, validate the manifest, and only then draft the full preprocessing command.

## Safe sequence

1. Inspect the dataset shape with `validate_dataset_manifest.py`.
2. If the input is a long or noisy video collection, draft a scene-splitting command with `build_scene_split_command.py`.
3. If captions are missing, choose a captioning backend and review a 3-sample spot check before any full pass.
4. Draft the preprocessing command with `build_preprocess_command.py`.
5. Inspect cached outputs with `inspect_precomputed_latents.py` before reusing them.

## Captioning backends

- `qwen_omni`: local vLLM server backend.
- `gemini_flash`: remote API backend.

The generated skill does not auto-run caption servers or hide credential requirements. Use the backend only after the user approves the network or API surface.

## Preprocessing planner notes

The bundled preprocessing-command helper validates:

- unified versus split checkpoint layout
- `video` / `audio` / `reference_video` / `reference_audio` / mask columns
- resolution-bucket syntax and the default VAE-aligned frame rule
- batch-size warnings for mixed image+video datasets
- reference scale-factor compatibility
- stale-output warnings when `--overwrite` is absent

The helper prints a command string and errors/warnings; it does not run preprocessing.

## Bundled execution helpers

After command review and explicit approval, the generated skill provides local runnable scripts that implement the preprocessing flow inside the skill tree:

- `scripts/process_dataset.py`: the bundled preprocessing entry point that orchestrates caption, video, audio, reference, and mask processing.
- `scripts/process_videos.py`: the bundled media-latent helper used by the preprocessing entry point.
- `scripts/process_captions.py`: the bundled caption-embedding helper used by the preprocessing entry point.
- `scripts/decode_latents.py`: the bundled latent decoder used for verification or spot checks.
- `scripts/split_scenes.py`: the bundled scene-splitting entry point.

Use the builders first, then run these helpers only after the user approves the data mutation.

## Mixed image and video datasets

When a manifest contains both image and video samples:

- include an `F=1` bucket for images
- include one or more `F>1` buckets for videos
- use training batch size 1 later

The helper surfaces this as a warning so the user can see the training consequence early.

## Split versus unified model layout

Choose the layout before drafting the command:

- **Unified**: one checkpoint file plus a Gemma directory.
- **Split**: transformer, packed text encoder, video VAE, audio VAE, and optional duration head.

If the dataset includes audio or reference audio, the split layout should include the audio VAE path.

## When to spot-check or stop

Stop before any heavy preprocess when:

- the manifest is missing a required role
- the selected bucket list does not fit the media mix
- the model/Gemma layout is inconsistent
- the dataset was already precomputed with a different model version or trigger token
- reference/mask paths are not ready yet

## Helper scripts to use next

- `scripts/validate_dataset_manifest.py`
- `scripts/build_scene_split_command.py`
- `scripts/build_preprocess_command.py`
- `scripts/inspect_precomputed_latents.py`
