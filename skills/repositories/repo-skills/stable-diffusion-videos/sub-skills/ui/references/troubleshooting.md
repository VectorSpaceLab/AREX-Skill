# UI troubleshooting

Use this page for Gradio interface and launcher problems.

## Model load happens before the UI appears

The repository examples construct the diffusion pipeline before calling
`Interface(...)`. That can trigger model downloads, CUDA allocation, and VAE or
scheduler construction before the browser UI is available.

Mitigation:

- Run `scripts/launch_interface.py --dry-run` first.
- Confirm model IDs, device, dtype, and scheduler choices.
- Start the launcher with `--run` only when the runtime is ready.

## Gradio version or launch errors

If importing or launching Gradio fails, verify that the active environment has a
compatible Gradio build and that `stable_diffusion_videos.Interface` imports
cleanly. Generic web-service deployment issues are out of scope for this skill;
this route only covers the package's local Gradio interface.

## Browser or port access issues

`Interface.launch(...)` forwards keyword arguments to Gradio. Use the normal
Gradio flags, such as debug mode or host/port options, in the launcher when the
local browser cannot reach the server.

## CUDA or dtype failures in the UI

The simple launcher is GPU-oriented. If you run on MPS, use `float32`. If CUDA is
not available, run the environment check before launching and expect generation
to be slow or unsupported.

## Experimental music-video UI hazards

The richer music-video UI is intentionally not copied as a runnable bundled
script because it can:

- download example audio through `youtube_dl`,
- depend on additional plotting/audio packages,
- assume CUDA at import time,
- generate long videos from user-uploaded audio.

If you only need the audio weights, use the generation sub-skill's
`preview_audio_timesteps.py` helper instead.

## Image tab returns no files

Check that the output directory is writable and that `generate_images(...)`
completed. The tab displays generated image paths, so upstream generation errors
appear as empty or missing gallery output.

## Video tab returns no video

Check the same generation constraints as `pipeline.walk(...)`: matching prompt
and seed counts, valid image sizes, a working video encoder, and enough GPU
memory.
