# Audio I/O and DSP

This package centralizes common audio handling in `mlx_audio.audio_io` and `mlx_audio.utils`.

## Verified Audio I/O

- `read(file, always_2d=False, dtype='float64', sample_rate=None, nchannels=None)`
- `write(file, data, samplerate, format=None)`

The reader can:

- load from a path or file-like object
- return mono or stereo arrays
- resample to a requested sample rate
- downmix to a requested channel count

The writer can:

- write WAV and ffmpeg-backed container formats
- save to a path or file-like object

## Common Helper Functions

- `audio_volume_normalize(audio, coeff=0.2)`
- `trim_silence(audio, top_db=20, frame_length=2048, hop_length=512)`
- `resample_audio(audio, orig_sample_rate, sample_rate, axis=-1)`
- `random_select_audio_segment(audio, length)`
- `load_audio(...)` in `mlx_audio.utils`

## Practical Notes

- WAV is the safest fixture format for tests.
- Non-WAV containers usually depend on ffmpeg.
- `sounddevice` playback depends on PortAudio.
- `audio` arrays are commonly shaped as either 1-D mono or 2-D multi-channel data depending on the loader arguments.
- Use resampling and silence trimming before voice cloning, VAD, or forced-alignment workflows when a reference clip is noisy or misaligned.
