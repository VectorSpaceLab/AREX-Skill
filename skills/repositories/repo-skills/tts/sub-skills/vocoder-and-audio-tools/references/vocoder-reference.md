# Vocoder Reference

This reference distills the vocoder surfaces in Coqui TTS 0.22.0 for future
agents that need to validate, pair, or train vocoders without depending on the
source checkout.

## What a Coqui vocoder consumes

A vocoder maps acoustic features, usually mel spectrogram frames, into waveform
samples. Compatibility is determined by the feature contract, not just by a
similar language or dataset name. Before pairing a TTS model and a vocoder,
compare at least:

- `audio.sample_rate`
- `audio.num_mels`
- `audio.hop_length`
- `audio.win_length` and `audio.fft_size`
- `audio.mel_fmin` and `audio.mel_fmax`
- amplitude-to-dB and normalization settings (`do_amp_to_db_mel`, `signal_norm`, `stats_path`)
- vocoder architecture fields such as `model`, `generator_model`, and `discriminator_model`

Use [`../scripts/validate_vocoder_config.py`](../scripts/validate_vocoder_config.py)
with `--tts-config` for the first-line mel-contract comparison.

## Released vocoder registry grammar

The model registry groups released vocoders as:

```text
vocoder_models/<language-or-universal>/<dataset>/<vocoder-name>
```

The inspected package registry contained 17 vocoder entries. Representative
names include:

| Registry name | Typical use |
| --- | --- |
| `vocoder_models/en/ljspeech/hifigan_v2` | default for several LJSpeech English TTS models |
| `vocoder_models/en/ljspeech/univnet` | paired with an LJSpeech phoneme Tacotron-DDC model in the registry |
| `vocoder_models/en/ljspeech/multiband-melgan` | paired with some LJSpeech TTS models |
| `vocoder_models/universal/libri-tts/fullband-melgan` | universal fallback used by some non-English Tacotron-DDC entries |
| `vocoder_models/nl/mai/parallel-wavegan` | Dutch MAI registry vocoder |
| `vocoder_models/de/thorsten/hifigan_v1` | Thorsten German HifiGAN registry vocoder |

When a released TTS model has a `default_vocoder`, prefer that default unless
the user explicitly asks for a custom pairing. For a custom pairing, require a
config comparison and explain that speech quality can degrade even when shapes
match because training data, normalization, and mel statistics may differ.

## Config classes and model selectors

Vocoder configs are Coqpit dataclasses. The public package imports config
classes from `TTS.vocoder.configs`.

| Config class | `model` value | Generator/discriminator notes | Typical caveat |
| --- | --- | --- | --- |
| `HifiganConfig` | `hifigan` | `hifigan_generator` + `hifigan_discriminator` | mel shape and L1 spectrogram parameters must match training features |
| `MelganConfig` | `melgan` | `melgan_generator` + multiscale discriminator | GAN training can be unstable; match upsampling to hop length |
| `MultibandMelganConfig` | `multiband_melgan` | multiband generator plus PQMF-related losses | subband settings affect waveform reconstruction |
| `FullbandMelganConfig` | `fullband_melgan` | fullband MelGAN-style generator | registry names can differ from class spelling |
| `ParallelWaveganConfig` | `parallel_wavegan` | parallel WaveGAN generator/discriminator | longer segments and STFT losses are expensive |
| `UnivnetConfig` | `univnet` | UnivNet generator/discriminator | generator conditioning channels follow `audio.num_mels` |
| `WavegradConfig` | `wavegrad` | diffusion-style `wavegrad` generator | inference noise schedule and tuning are model-specific |
| `WavernnConfig` | `wavernn` | autoregressive WaveRNN | often uses precomputed mel/quantized features |
| `BaseVocoderConfig` / `BaseGANVocoderConfig` | base templates | shared fields for raw wav data, feature paths, GAN losses, optimizers | not usually a final training config by itself |

Shared vocoder fields that future agents should check before training:

- `data_path`: directory scanned recursively for wav files.
- `feature_path`: optional directory of precomputed `.npy` features; stems and counts must align with wav files.
- `eval_split_size`: number of wavs/features held out for evaluation.
- `seq_len`: waveform segment length; for segmental GAN datasets, feature frames are roughly `seq_len // hop_length` plus convolution padding.
- `pad_short` and `conv_pad`: extra waveform/feature padding used by vocoder datasets.
- `use_cache`: can speed repeated feature access but may cause RAM OOM on large data.
- `use_noise_augment`: may be useful for GAN training but changes feature/audio equality checks.

## `setup_model` behavior

`TTS.vocoder.models.setup_model(config)` creates a vocoder model from a config:

1. If both `discriminator_model` and `generator_model` exist, it constructs a
   GAN wrapper.
2. Otherwise it imports a model module from the lower-cased `config.model`.
3. `wavernn`, `gan`, and `wavegrad` have special class-name handling.
4. Other names are converted from snake case to CamelCase and initialized from
   `init_from_config(config)`.

This is useful for a no-training config sanity check, but it may allocate a
large torch module. Keep model instantiation optional. The bundled validator
therefore loads configs by default and only calls `setup_model` when the user
passes `--instantiate-model`.

## HifiGAN defaults to preserve

`HifiganConfig` defaults to:

- `model="hifigan"`
- `generator_model="hifigan_generator"`
- `discriminator_model="hifigan_discriminator"`
- generator upsampling factors `[8, 8, 2, 2]`, whose product is `256`
- default `audio.hop_length=256`, `audio.sample_rate=22050`, and `audio.num_mels=80`
- `l1_spec_loss_params` with `sample_rate=22050`, `n_fft=1024`, `hop_length=256`, `win_length=1024`, and `n_mels=80`

If `audio.hop_length` changes, check that the generator upsampling product still
matches the hop length. If `audio.num_mels` changes, check generator conditioning
channels and any feature files.

## Checkpoint/config compatibility checklist

Before using a vocoder checkpoint:

1. Match the checkpoint with the config that produced it; do not pair a HifiGAN
   checkpoint with a UnivNet or WaveGrad config.
2. Check `model`, `generator_model`, and `discriminator_model`.
3. Compare mel contract fields against the producing TTS model or precomputed
   feature directory.
4. If `stats_path` is used, confirm the stats file was computed with the same
   audio fields and has a mel mean/std length equal to `audio.num_mels`.
5. Confirm the checkpoint is restored for inference/fine-tuning using the
   package API or training module that owns the workflow. This sub-skill does
   not own end-user synthesis commands; route those to the CLI/API sub-skills.
