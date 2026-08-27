# Installation Troubleshooting

## Import and optional dependency failures

| Error or warning | Meaning | Action |
| --- | --- | --- |
| `ModuleNotFoundError: typeguard` | Base package dependencies are incomplete. | Reinstall base ESPnet in a clean environment; run `python -m pip check`. |
| `ModuleNotFoundError: pyworld` | TTS/SVS code imported pitch extraction without TTS deps. | Install `.[tts]` or narrow the workflow if TTS/SVS is not needed. |
| Missing `jaconv`, `jamo`, `pypinyin`, or G2P package | Language/frontend processing dependency is absent. | Install TTS or the specific language frontend dependency. |
| `No module named flash_attn` | Optional FlashAttention kernel is unavailable. | Non-fatal for many configs; install only if the config requires it and torch/CUDA wheels are compatible. |
| Missing `k2` | k2 decoding/rescoring path is unavailable. | Install only for k2-specific ASR/UASR workflows. |
| Missing `s3prl`, `whisper`, `longformer`, `kenlm`, `fairseq`, `phonemizer` | Specialized component/config dependency missing. | Confirm the selected config uses that component before installing. |

## Host tool failures

- `sox`, `ffmpeg`, `flac`: audio conversion and command-pipe entries.
- `sph2pipe`: NIST Sphere files.
- `spm_train`/`spm_encode`/`spm_decode`: SentencePiece tokenization.
- `sclite`, `PESQ`, `BeamformIt`: scoring and beamforming.
- `cmake`: build-time dependency for some compiled packages.

Run the environment checker with the matching executable group. Missing host tools do not invalidate a package-only ASR inference task unless the chosen workflow uses them.

## Environment conflict policy

- Run `python -m pip check` after installs.
- Do not repair a user-owned environment without permission if upgrades could break unrelated work.
- Prefer a fresh minimal environment when compiled packages or CUDA wheels conflict.
- Keep broad extras (`all`, `dev`, `test`, `doc`) out of ordinary package/inference installs.

## CUDA policy

If CUDA is required, check torch's CUDA runtime first. A valid GPU check includes `torch.cuda.is_available()`, device count, CUDA version, and a tiny tensor allocation. Distributed/NCCL and full recipe training still require separate evidence.
