# API reference

## Purpose

Read this when you need the verified public classes, functions, and method signatures used by the repo's workflows.

## Verified signatures

### `utils`

- `get_hparams(init=True)`
- `get_hparams_from_file(config_path)`
- `get_hparams_from_dir(model_dir)`
- `load_checkpoint(checkpoint_path, model, optimizer=None)`
- `save_checkpoint(model, optimizer, learning_rate, iteration, checkpoint_path)`
- `load_filepaths_and_text(filename, split="|")`

### `text`

- `text_to_sequence(text, cleaner_names)`
- `cleaned_text_to_sequence(cleaned_text)`
- `sequence_to_text(sequence)`
- `cleaners.basic_cleaners(text)`
- `cleaners.transliteration_cleaners(text)`
- `cleaners.english_cleaners(text)`
- `cleaners.english_cleaners2(text)`

### `data_utils`

- `TextAudioLoader(audiopaths_and_text, hparams)`
- `TextAudioSpeakerLoader(audiopaths_sid_text, hparams)`
- `TextAudioCollate(return_ids=False)`
- `TextAudioSpeakerCollate(return_ids=False)`
- `DistributedBucketSampler(dataset, batch_size, boundaries, num_replicas=None, rank=None, shuffle=True)`

### `models`

- `SynthesizerTrn(n_vocab, spec_channels, segment_size, inter_channels, hidden_channels, filter_channels, n_heads, n_layers, kernel_size, p_dropout, resblock, resblock_kernel_sizes, resblock_dilation_sizes, upsample_rates, upsample_initial_channel, upsample_kernel_sizes, n_speakers=0, gin_channels=0, use_sdp=True, **kwargs)`
- `MultiPeriodDiscriminator(use_spectral_norm=False)`

### Important methods

- `SynthesizerTrn.forward(x, x_lengths, y, y_lengths, sid=None)`
- `SynthesizerTrn.infer(x, x_lengths, sid=None, noise_scale=1, length_scale=1, noise_scale_w=1.0, max_len=None)`
- `SynthesizerTrn.voice_conversion(y, y_lengths, sid_src, sid_tgt)`

## Shape notes

- `x` is token ids with shape `[batch, text_length]`.
- `y` in the model forward path is the linear spectrogram, not raw waveform.
- `spec_channels` is `513` for the provided configs because `filter_length = 1024`.
- `segment_size` passed to the model is `32` frames for the provided configs.
- `infer()` returns the generated audio tensor, the alignment, the output mask, and latent intermediates.

## Verified behavior

- `basic_cleaners` and `transliteration_cleaners` import and run without `espeak`.
- `english_cleaners2` requires `espeak` and fails clearly when the binary is missing.
- `models` imports only after `monotonic_align` is built correctly.
