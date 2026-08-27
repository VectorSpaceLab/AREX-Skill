# API reference

All wrapper classes below inherit `DiffusionModel`, so `forward(...)` routes to the diffusion loss path and `sample(...)` routes to the sampler path.

## DiffusionUpsampler

**Signature**

```py
DiffusionUpsampler(in_channels: int, upsample_factor: int, net_t: Callable, **kwargs)
```

**Verified behavior**

- Builds the inner net as `AppendChannelsPlugin(net_t, channels=in_channels)`.
- `upsample_factor` is used by both `downsample(...)` and `upsample(...)`.
- `forward(x, *args, **kwargs)` expects a high-rate waveform tensor shaped `[batch, channels, high_len]`.
  - It creates a low-rate proxy with `downsample(x, factor=upsample_factor)` and then reupsamples it back to the high-rate length.
  - The proxy is passed to the net as `append_channels=...`.
- `sample(downsampled, generator=None, **kwargs)` expects a low-rate waveform shaped `[batch, channels, low_len]`.
  - It upsamples the conditioning waveform, adds noise with the same shape, and returns a high-rate waveform.

**Shape notes**

- For tiny smoke cases, choose lengths divisible by `upsample_factor`.
- The utility resampler rounds target length to an integer, so exact ratios are safest for sanity checks.

## DiffusionVocoder

**Signature**

```py
DiffusionVocoder(
    net_t: Callable,
    mel_channels: int,
    mel_n_fft: int,
    mel_hop_length: Optional[int] = None,
    mel_win_length: Optional[int] = None,
    in_channels: int = 1,
    **kwargs,
)
```

**Verified behavior**

- The top-level constructor accepts `mel_`-prefixed kwargs and strips the prefix before passing them to `MelSpectrogram`.
- Required `mel_` kwargs include `mel_sample_rate`; optional keys include `mel_normalize` and `mel_normalize_log`.
- `mel_hop_length` defaults to `mel_n_fft // 4`.
- `mel_win_length` defaults to `mel_n_fft`.
- The inner net is wrapped as `AppendChannelsPlugin(net_t, channels=1)` and the diffusion core runs on one-channel wave tensors after packing channels.
- `forward(x, *args, **kwargs)` expects waveform input shaped `[batch, channels, time]`.
  - Internally it converts the waveform to mel spectrograms, flattens them to the diffusion time axis, and conditions the net with `append_channels=...`.
- `sample(spectrogram, generator=None, **kwargs)` expects mel input shaped `[batch, channels, mel_channels, mel_frames]`.
  - It converts the mel tensor to the flattened diffusion conditioning shape and returns waveform output shaped `[batch, channels, time]`.
- The public `in_channels` argument is accepted but the implementation batches channels internally and uses one diffusion channel per packed waveform channel.

**Shape notes**

- The mel tensor should use the layout `[batch, channels, mel_channels, frames]`.
- Keep mel fixture sizes small but coherent; unrealistic tiny settings may trigger torchaudio filterbank warnings.

## DiffusionAE

**Signature**

```py
DiffusionAE(
    in_channels: int,
    channels: Sequence[int],
    encoder: EncoderBase,
    inject_depth: int,
    latent_factor: Optional[int] = None,
    adapter: Optional[AdapterBase] = None,
    **kwargs,
)
```

**Verified behavior**

- Builds `context_channels = [0] * len(channels)` and sets `context_channels[inject_depth] = encoder.out_channels`.
- `latent_factor` defaults to `encoder.downsample_factor`.
- If an adapter is provided, it is frozen with `requires_grad_(False)` and used as a pre/post transform around the diffusion branch.
- `forward(x, with_info=False, **kwargs)`:
  - calls `encode(x, with_info=True)` and expects the encoder to return `(latent, info)` when info is requested;
  - passes `channels=[None] * inject_depth + [latent]` to the diffusion model;
  - returns `loss` or `(loss, info)`.
- `encode(*args, **kwargs)` delegates to the encoder.
- `decode(latent, generator=None, **kwargs)`:
  - infers a noise length from `closest_power_2(latent.shape[2] * latent_factor)`;
  - samples conditioned on the latent channels;
  - applies `adapter.decode(...)` if an adapter is present.

**Shape notes**

- `inject_depth` must be a valid index into `channels`.
- The latent channel count must match `encoder.out_channels`.
- The latent time length and `latent_factor` together control the sampled waveform length estimate.

## EncoderBase

**Signature**

```py
class EncoderBase(nn.Module, ABC):
    def __init__(self):
        super().__init__()
        self.out_channels = None
        self.downsample_factor = None
```

**Notes**

- This is the public contract for diffusion autoencoder encoders.
- The implementation only needs the `out_channels` and `downsample_factor` fields, but a concrete encoder should also provide `forward(x, with_info=False)`.
- When `with_info=True`, return `(latent, info)` if downstream callers expect metadata.

## AdapterBase

Import this helper from `audio_diffusion_pytorch.models`; it is not re-exported at the package root in this version.

**Signature**

```py
class AdapterBase(nn.Module, ABC):
    def encode(self, x: Tensor) -> Tensor: ...
    def decode(self, x: Tensor) -> Tensor: ...
```

**Notes**

- Use this for waveform-side preprocessing or postprocessing around `DiffusionAE`.
- The adapter should preserve batch/time alignment and tensor shape so the diffusion branch can sample and decode safely.
- The wrapper freezes the adapter by default.

## MelSpectrogram

**Signature**

```py
MelSpectrogram(
    n_fft: int,
    hop_length: int,
    win_length: int,
    sample_rate: int,
    n_mel_channels: int,
    center: bool = False,
    normalize: bool = False,
    normalize_log: bool = False,
)
```

**Notes**

- Accepts waveform input with arbitrary leading dimensions and a final time axis.
- Returns mel tensors with the same leading dimensions and layout `[..., n_mel_channels, frames]`.
- Reflect pads by `(n_fft - hop_length) // 2` before the STFT.
- `normalize=True` applies power-style normalization; `normalize_log=True` applies log compression after clamping.

## LTPlugin

**Signature**

```py
LTPlugin(net_t: Callable, num_filters: int, window_length: int, stride: int) -> Callable[..., nn.Module]
```

**Notes**

- Wraps a net with learned analysis and synthesis transforms.
- The inner net sees `in_channels * num_filters` input channels and emits `out_channels * num_filters` channels.
- Useful when a wrapper needs a learned front/back transform around the diffusion model, but it is not required for basic upsampler, vocoder, or autoencoder use.

## AppendChannelsPlugin

Import this helper from `audio_diffusion_pytorch.components`; it is used internally by wrapper classes and is not re-exported at the package root in this version.

**Signature**

```py
AppendChannelsPlugin(net_t: Callable, channels: int)
```

**Notes**

- Returns a net factory whose forward path requires `append_channels=...`.
- Concatenates `append_channels` on channel dimension 1 before calling the wrapped net.
- Used internally by `DiffusionUpsampler` and `DiffusionVocoder`.
- When used manually, `append_channels` must match the batch size, time length, device, and dtype of the base tensor.
