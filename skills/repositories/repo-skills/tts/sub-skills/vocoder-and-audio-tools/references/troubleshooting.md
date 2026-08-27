# Vocoder and Audio Troubleshooting

Use this workflow-specific troubleshooting guide after checking root-level
install/import guidance when available.

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ImportError` or shared-library errors from `soundfile`, `librosa`, or `torchaudio` | Missing audio backend, incompatible libsndfile, unsupported Python/PyTorch/audio stack | Verify `python -c "import soundfile, librosa, torchaudio"`; install/repair libsndfile through the environment manager; keep Python within the package-supported range; rerun helper `--help` before real audio processing. |
| `soundfile.LibsndfileError`, `EOFError`, or unreadable wav | Corrupt, empty, unsupported, or mislabeled audio file | Probe the file with `soundfile.info`; isolate bad files; convert to PCM wav; rerun resampling on a copy, not in-place. |
| Mel shape mismatch such as expected `80` channels but got another count | TTS config and vocoder config have different `audio.num_mels`, feature files came from another config, or wrong checkpoint/config pair | Run [`../scripts/validate_vocoder_config.py`](../scripts/validate_vocoder_config.py) with `--tts-config`; inspect first feature file shape if `feature_path` is used; regenerate features/stats with the intended audio config. |
| Audio length/frame mismatch during vocoder dataset loading | `seq_len`, `hop_length`, `conv_pad`, or generator upsampling product are inconsistent | Ensure HifiGAN upsampling product matches `audio.hop_length`; keep `seq_len` a sensible multiple of hop length; lower `conv_pad` unless needed. |
| `stats_path` exists but normalization fails | Stats file computed with another config or malformed `.npy` contents | Recompute stats with [`../scripts/compute_audio_stats.py`](../scripts/compute_audio_stats.py); confirm `mel_mean`/`mel_std` length equals `audio.num_mels`; avoid reusing stats across sample rates or mel settings. |
| `stats_path` file not found | Relative path resolved from a different working directory or config copied without stats file | Use an explicit path in the config or place stats next to the config and validate before training; keep the stats artifact with the config/checkpoint. |
| Resampling unexpectedly changed raw data | In-place mode was used, or output directory overlapped the input directory | Prefer [`../scripts/resample_audio_dir.py`](../scripts/resample_audio_dir.py) with `--output-dir`; use `--in-place` only after backup; never set output dir equal to input dir. |
| Output sample rate is still wrong after resampling | Existing files skipped, wrong extension filter, or verification disabled | Pass `--overwrite` for stale outputs; check `--file-ext`; keep verification enabled unless a separate checker will read the outputs. |
| VAD helper refuses to run without acknowledgement | The wrapper is protecting against Torch Hub cache/network side effects | Use `--dry-run` first; pass `--allow-download` only after the user approves model/cache/network access, or pass a local Silero VAD source directory with `--hub-repo`. |
| VAD run downloads repeatedly or is slow | Torch Hub cache miss/refresh, no local model cache, CPU-only VAD, or large directory | Use a local cached/source path where possible; process a tiny subset first; keep `--glob` narrow; avoid `--force-reload` unless deliberately refreshing. |
| VAD output has no speech or `filtered_files.txt` lists many files | Non-speech/noisy files, unsupported sample rate handling, excessive trimming mode, or wrong glob | Check one file manually; prefer leading/trailing trim before `--trim-all-nonspeech`; verify input audio is speech and readable by torchaudio. |
| Vocoder checkpoint loads with wrong architecture errors | Checkpoint/config mismatch, e.g. HifiGAN weights with UnivNet/WaveGrad config, or changed generator parameters | Match checkpoint to its original config; compare `model`, generator/discriminator names, and generator params; do not infer compatibility from registry name alone. |
| Synthesis sounds noisy/robotic despite no shape error | Mel/vocoder training mismatch, stats mismatch, sample-rate mismatch, or vocoder trained on different TTS feature distribution | Prefer the registry default vocoder; compare audio fields and stats; use a vocoder trained on the same TTS model outputs or dataset; route end-user synthesis command construction to the CLI/API sub-skills. |
| Training is extremely slow on CPU | Full vocoder training is compute-heavy | Treat CPU training as debugging only; use GPU if approved; reduce `small_run`, `epochs`, `batch_size`, `seq_len`, and workers for smoke runs. |
| GPU OOM during training | Batch/segment/model too large, too many workers, cache enabled, or mixed precision instability | Lower `batch_size`/`eval_batch_size`, lower `seq_len`, disable `use_cache`, reduce workers, consider gradient accumulation, and avoid changing architecture and precision simultaneously. |
| Feature-path branch asserts wav/feature count mismatch | `feature_path` has missing/extra `.npy` files or stems do not match wav stems | Regenerate features; ensure every wav stem has exactly one feature file; keep the feature tree separate from unrelated `.npy` files. |
| `AudioProcessor` assertion on `win_length` or `min_level_db` | Invalid audio config values | Keep `win_length <= fft_size`; do not set `min_level_db` to `0`; validate config after overrides. |

## Quick diagnostic order

1. Run helper `--help` to confirm the script itself is visible.
2. Run [`../scripts/validate_vocoder_config.py`](../scripts/validate_vocoder_config.py)
   on the vocoder config; add `--tts-config` for pairing issues.
3. Probe one wav with the environment's audio stack.
4. If resampling, run the bundled resampler on a copied tiny subset first.
5. If stats are involved, recompute a bounded stats file and compare mel dims.
6. Only then move to training-module help or a user-approved small training run.
