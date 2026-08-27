# FunClip root troubleshooting

Use this root guide for cross-cutting failures before routing to a focused
sub-skill.

## Install/import fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for `videoclipper`, `utils`, or `llm` during programmatic imports | FunClip source files use top-level imports and are intended to run as scripts from a checkout. | For programmatic checks, add `<checkout>/funclip` to `sys.path`, or run the script entry points (`python funclip/launch.py`, `python funclip/videoclipper.py`). |
| Gradio app returns HTTP 500 on startup | Fresh install pulled incompatible Starlette 1.x with Gradio 4. | Reinstall `requirements.txt` and confirm `starlette<1.0`. |
| Fun-ASR-Nano/SenseVoice subtitles or clipping boundaries look empty | `funasr` is older than the compatibility floor. | Install or upgrade to `funasr>=1.3.29`, then rerun recognition. |
| Root smoke helper fails on imports | Missing base runtime dependencies. | Run `python -m pip install -r requirements.txt`, then rerun `scripts/check_environment.py --repo-root <checkout>`. |

## Model/cache and hardware uncertainty

The deterministic skill scripts do not prove real ASR inference. If a real run
hangs or fails on model loading:

1. Confirm the selected model family in [clip-workflows](../sub-skills/clip-workflows/SKILL.md).
2. Confirm the target environment has network access or a pre-populated model cache.
3. Confirm CPU/GPU memory is sufficient for the model.
4. Prefer Paraformer for precise transcript-text clipping when timestamp fidelity matters.

## Media, subtitle, and system-binary failures

- If video recognition fails immediately, confirm the video has an audio stream.
- If the CLI rejects a file, convert to one of the supported audio/video suffixes
  in the clip workflow reference.
- If `Clip+Subtitles` fails but ordinary clipping works, check ffmpeg,
  ImageMagick, and font availability. Run the root helper with `--check-binaries`
  to report `ffmpeg`, `convert`, and `magick` availability.
- If output directories fail, create nested parent directories before running
  stage 1 or stage 2.

## LLM provider failures

Route to [llm-providers](../sub-skills/llm-providers/SKILL.md) when the error is
about a model prefix, provider SDK, API key, base URL, prompt format, Pegasus
video input, or timestamp parsing. Use the provider route smoke script before a
live retry when the failure appears local.

## Release and maintainer failures

Route to [release-packaging](../sub-skills/release-packaging/SKILL.md) when the
problem is about `VERSION`, release notes, source archives, `SHA256SUMS`, GitHub
release workflows, issue templates, PR templates, or maintainer validation
commands.

Do not publish or mutate a live GitHub release unless the user explicitly
authorizes maintainer credentials and publication.

## Which smoke check first?

| Need | Command from generated skill root |
| --- | --- |
| Install/import/model-selection/launch policy | `python scripts/check_environment.py --repo-root <checkout> --check-binaries` |
| Text matching, no-match behavior, speaker match helper, PCM conversion | `python sub-skills/clip-workflows/scripts/clip_cli_smoke.py --repo-root <checkout>` |
| AtlasCloud/MiniMax prefix stripping and Pegasus timestamp normalization | `python sub-skills/llm-providers/scripts/provider_route_smoke.py --repo-root <checkout>` |
| Release builder help or archive creation | `python sub-skills/release-packaging/scripts/build_release_assets.py --help` |
