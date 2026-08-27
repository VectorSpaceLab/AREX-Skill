# Speech-Enhancement Data Generation

ClearerVoice-Studio includes two speech-enhancement data-generation workflows: additive noisy speech and reverb-plus-noisy speech. Both create new audio files and lists, so treat them as mutating scripts and review configs before running.

## Additive noisy speech

Purpose: create noisy/clean pairs by mixing clean speech with background noise.

Process:

1. Read clean speech paths from a clean list or clean directory.
2. Read noise paths from a noise list or noise directory.
3. Choose an SNR, either random within bounds or from evenly spaced levels.
4. Resample clean/noise to the configured `sampling_rate` if needed.
5. Crop or concatenate speech/noise to satisfy `min_audio_length`, `max_audio_length`, and `silence_length`.
6. Write noisy waveforms under an output root/run/suffix tree and write matching clean targets; optionally write the isolated noise waveform.
7. Write a generated wav list containing output filenames.

Key config fields:

```ini
[noisy_speech]
test: False
sampling_rate: 16000
audioformat: *.wav
min_audio_length: 3
max_audio_length: 25
silence_length: 0.1
total_hours: 0.02
snr_lower: 0
snr_upper: 15
random_snr: True
total_snrlevels: 2
speech_dir: None
noise_dir: None
clean_list: data_scp/speech.scp
noise_list: data_scp/noise.scp
suffix: noisy_16kHz_utt_
out_audio_root: generated/output_noisy_speech
save_noise: False
```

Use `test: True` only for deterministic/debug-style generation where filenames include source names. For real train generation, keep a unique output root or run number.

## Reverb plus noisy speech

Purpose: create reverberant speech, an early-reverberation target, and then add noise.

Process:

1. Generate room impulse responses (RIRs) for random room dimensions, source locations, microphone locations, and reverberation times.
2. Convolve clean speech with each RIR to create reverb speech.
3. Trim the RIR to a short early-reverb duration to create a target signal that stays aligned with the reverberant input better than the original dry clean signal.
4. Add background noise to the reverberant speech using the noise config.
5. Write noisy, target, optional noise, RIR, and intermediate reverb directories under the output run tree.

Main launcher fields to review:

```bash
output_path=generated/data
run_num=0
num_RIRs=10
sample_rate=48000
```

Important step-specific fields:

- `output_RIR_dir` for generated RIR wav files and their list.
- `speech_scp` for clean speech input list.
- `num_wavs_per_RIR` for how many clean utterances are convolved with each RIR.
- `target_rt` for how much early reverberation is retained in the target.
- `output_reverb_dir` and `output_reverb_noisy_dir` for intermediate and final outputs.
- `noise_list`, SNR bounds, and `save_noise` in the config file used by the noise-addition step.

## Safe workflow before generation

1. Copy the generation config and source lists to a run-specific working directory or commit-friendly location.
2. Use `scripts/make_scp_list.py` to produce clean/noise lists from local directories; review the dry-run output before writing.
3. Set a new `run_num` or output directory to avoid mixing old and new generated files.
4. Estimate output size from `total_hours`, `sample_rate`, `total_snrlevels`, and `num_RIRs`.
5. Confirm the desired target sample rate matches the downstream SE network.
6. Run a tiny dry/demo generation only after the user approves mutation; then inspect a few output files and list rows before scaling up.

## Turning generated data into SE training lists

Additive-noise generation writes parallel `noisy/` and `target/` folders. Create a two-column training `.scp` where each row pairs the generated noisy file and its matching target file:

```text
generated/output_noisy_speech/run0/noisy/utt001.wav generated/output_noisy_speech/run0/target/utt001.wav
generated/output_noisy_speech/run0/noisy/utt002.wav generated/output_noisy_speech/run0/target/utt002.wav
```

For reverb-noisy generation, use the final reverb-noisy output tree and pair `noisy/` with `target/` files from that same run.

The bundled `make_scp_list.py` writes one-column lists only. Use it to inventory a single directory, then pair noisy/target filenames with a small task-specific script or spreadsheet if the directory filenames are guaranteed to match.

## Common generation hazards

- Config/list paths are relative to the generation script's current working directory; run from the expected generation directory or use absolute user-owned paths.
- `total_hours` and `num_RIRs` can expand output quickly; start small.
- Reusing `run_num` or `out_audio_root` can interleave outputs from different experiments.
- Reverb generation asserts sample-rate equality in intermediate steps; resample clean speech before reverb generation if needed.
- FFmpeg/libsndfile availability affects compressed or unusual media formats; prefer WAV lists for generation.
- Generation scripts can resample internally, but downstream model choice still controls the correct final sample rate.
