# Audio I/O and DSP

## Verified Helpers

- `mlx_audio.audio_io.read(file, always_2d=False, dtype='float64', sample_rate=None, nchannels=None)`
- `mlx_audio.audio_io.write(file, data, samplerate, format=None)`
- `mlx_audio.utils.audio_volume_normalize(audio, coeff=0.2)`
- `mlx_audio.utils.trim_silence(audio, top_db=20, frame_length=2048, hop_length=512)`
- `mlx_audio.utils.resample_audio(audio, orig_sample_rate, sample_rate, axis=-1)`
- `mlx_audio.utils.random_select_audio_segment(audio, length)`
- `mlx_audio.utils.load_audio(...)`

## Practical Behavior

- `read(...)` can resample and downmix while reading.
- `write(...)` is the common output path for generated or enhanced audio.
- WAV is the safest no-network test fixture.
- Non-WAV formats often depend on ffmpeg.
- `sounddevice` playback depends on PortAudio.

## When to Use These Helpers

- Before voice cloning, trim or normalize noisy reference audio.
- Before VAD or realtime turn detection, confirm the sample rate and channel layout.
- Before enhancement/separation, make sure the input path exists and the file format is supported.
