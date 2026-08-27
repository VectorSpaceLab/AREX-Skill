# Audio and Music Troubleshooting

## Purpose

Use this page when the audio or music demo fails before producing a waveform.

## OpenAI / structure-caption problems

**Symptoms**
- The audio demo cannot build a structure caption.
- The helper complains about an API key, proxy, or upstream service.

**Likely cause**
- `n2s_openai.py` still contains the placeholder key or an invalid `base_url`.

**Recovery**
- Set the API key and proxy values locally before retrying.
- Treat the structure-caption step as an external dependency, not an internal model bug.

## Checkpoint-folder problems

**Symptoms**
- The demo cannot find `audio_generation`, `music_generation`, `maa2`, `bigvnat`, or `CLAP` assets.
- The Gradio app starts but fails on the first generation request.

**Likely cause**
- The checkpoint tree does not match the README layout or the config still points at placeholder paths.

**Recovery**
- Run `scripts/check_audio_music_inputs.py` to validate the config and checkpoint tree.
- Update the config paths and shell wrapper before relaunching.

## Dependency problems

**Symptoms**
- Missing `soundfile`, `omegaconf`, `torchdyn`, `pytorch_lightning`, or `torchlibrosa` imports.
- `ModuleNotFoundError: No module named 'flash_attn'` while importing `demo_audio.py` or `demo_music.py`.
- FlashAttention or Apex-related errors in the model stack.

**Likely cause**
- The audio/music extras were not installed, or the CUDA stack is incomplete.

**Recovery**
- Install the audio/music dependencies before attempting to use the demo.
- Install a CUDA-compatible `flash-attn` build before launching the demo modules.
- If Apex is present, ensure it is a full CUDA+C++ build; a Python-only build is known to fail.

## Sample-rate mismatch

**Symptoms**
- The demo rejects the selected sample rate or produces unexpected output settings.

**Likely cause**
- The run was started with a rate other than the documented 16000 Hz value.

**Recovery**
- Keep the sample rate aligned with the branch's documented value unless you are deliberately testing a modified config.
