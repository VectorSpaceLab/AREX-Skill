# Cross-cutting troubleshooting

Use this page to choose the nearest detailed troubleshooting path. For launch/config issues, continue in `../sub-skills/setup/references/troubleshooting.md`. For upload/API/client issues, continue in `../sub-skills/transcription/references/troubleshooting.md`.

## Quick symptom routing

| Symptom | Most likely area | First action |
| --- | --- | --- |
| App does not start or immediately exits | setup/runtime | Run the bundled `scripts/check-runtime.py --repo-root <checkout>` helper and inspect dependency plus ffmpeg status. |
| Browser opens but upload conversion fails | ffmpeg/input media | Confirm both `ffmpeg` and `ffprobe` are on PATH and the media format is supported. |
| First transcription tries to download a model | model placement | Pre-place the selected model folder or allow network access for first use. |
| CUDA selected but app crashes or falls back | backend/runtime | Run `../sub-skills/setup/scripts/check-cuda.py`; verify driver, CUDA runtime, cuDNN, CTranslate2, and VRAM. |
| Large model stalls or machine runs out of memory | model/backend sizing | Use a smaller model, reduce beam/search settings, switch to CPU only if GPU is unstable, or avoid `large-v3` on low-memory hosts. |
| API returns unexpected shape | endpoint/format | Check `../sub-skills/transcription/references/api-reference.md`; `/api` and `/v1/audio/transcriptions` wrap results differently. |
| Empty transcription result | input/model/language | Verify the audio actually contains speech, language/model choices match, and response format parsing is correct. |

## Common non-fatal signals

- Update checks may fail offline without preventing local transcription.
- Some runtime warnings from optional libraries can be non-fatal if transcription still completes; capture the exact warning before changing dependencies.
- The app may create temporary WAV files and model folders while running; those are runtime artifacts, not skill files.

## Backend warnings

The app has both CPU and optional CUDA paths. A successful CPU import does not prove CUDA transcription. When CUDA matters, check all of these:

1. NVIDIA driver and visible GPU.
2. CUDA-capable torch import.
3. cuDNN availability.
4. CTranslate2 CUDA device visibility.
5. Enough VRAM for the selected model.

The generated inspection environment proved the optional CUDA stack on the build host, but future machines may differ.

## Configuration surprises

`set.ini` contains some keys that do not affect every path equally. In the observed source, `cuda_com_type` is parsed but not passed into `WhisperModel`, and the browser worker does not pass the temperature setting while the API helper does. If a setting seems ignored, check `../sub-skills/setup/references/configuration.md` before assuming user error.
