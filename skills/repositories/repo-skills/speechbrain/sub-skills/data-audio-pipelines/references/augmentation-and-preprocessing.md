# Augmentation and preprocessing components

SpeechBrain has reusable augmentation and processing modules that are commonly configured from HyperPyYAML recipes.

## Time-domain augmentation signatures

```python
speechbrain.augment.time_domain.AddNoise(csv_file=None, csv_keys=None, sorting="random", num_workers=0, snr_low=0, snr_high=0, pad_noise=False, ...)
speechbrain.augment.time_domain.AddReverb(csv_file, sorting="random", num_workers=0, rir_scale_factor=1.0, ...)
speechbrain.augment.time_domain.SpeedPerturb(orig_freq, speeds=[90, 100, 110], device="cpu")
speechbrain.augment.time_domain.DropFreq(drop_freq_low=1e-14, drop_freq_high=1, drop_freq_count_low=1, drop_freq_count_high=3, ...)
speechbrain.augment.time_domain.DropChunk(drop_length_low=100, drop_length_high=1000, drop_count_low=1, drop_count_high=3, ...)
speechbrain.augment.time_domain.DoClip(clip_low=0.5, clip_high=0.5)
```

Use `AddNoise`/`AddReverb` with CSV manifests for noise/RIR files. Validate those paths before training; missing augmentation assets are a common recipe failure.

## Frequency-domain and audio processing

Important processing modules/functions include:

- `STFT`, `ISTFT`, `spectral_magnitude`, `Filterbank`, `DCT`, `Deltas`, `ContextWindow`.
- `InputNormalization`, `GlobalNorm`, `MinLevelNorm`, dynamic-range compression.
- Signal helpers such as `normalize`, `rescale`, `convolve1d`, `reverberate`, `overlap_and_add`, `resynthesize`.
- Multi-microphone helpers such as covariance, delay-sum, MVDR, GEV, GCC-PHAT, SRP-PHAT, MUSIC, and steering utilities.
- Vocal features such as autocorrelation, periodic features, spectral features, GNE, jitter, shimmer, and harmonicity.

## HyperPyYAML augmentation pattern

```yaml
add_noise: !new:speechbrain.augment.time_domain.AddNoise
    csv_file: !ref <noise_csv>
    snr_low: 0
    snr_high: 15
    clean_sample_rate: 16000
    noise_sample_rate: 16000
```

Then in Python:

```python
wavs_noisy = hparams["add_noise"](wavs, wav_lens)
```

## Validation before training

- Confirm every CSV manifest path exists after replacements.
- Confirm all audio files can be opened with `audio_io.info`.
- Confirm sample rates match `clean_sample_rate`, `noise_sample_rate`, or model assumptions.
- Run one batch through augmentation before launching full training.
- Use deterministic or fixed seeds when comparing expected augmented outputs.

## Beamforming and multi-channel notes

Multi-microphone processing expects careful channel dimensions and array geometry. Before using beamforming modules, write a tiny shape probe that prints input/output shapes and validates sample rate, channel count, and time alignment. Do not silently squeeze a channel dimension.

## Vocal feature notes

Vocal features are useful for pathology or interpretable voice analysis. Synthetic tone tests can validate expected ranges for fundamental frequency, harmonicity, jitter, shimmer, spectral centroid/spread, and GNE before applying the functions to noisy real recordings.
