# Conditioning workflows

The README examples are shape recipes, not pretrained checkpoints. The repository does not ship verified weights, so these workflows assume fresh initialization or caller-provided local weights.

## Shared setup notes

- Use `../generation` for base UNet, diffusion, text, or inpainting decisions.
- For tiny tests, choose `resnet_groups=1` or channel counts divisible by 8.
- Prefer short even lengths so the resampler and the wrapper shapes stay aligned.

## 1) Diffusion upsampling

**Goal:** condition a high-rate waveform diffusion model on a lower-rate waveform.

**Training path**

```py
hi = torch.randn(batch, channels, high_len)
loss = upsampler(hi)
```

- `hi` is the target high-rate waveform.
- The wrapper internally downsamples and then reupsamples the input to build the conditioning channels.
- The diffusion net receives `append_channels=...` from the reupsampled proxy.

**Sampling path**

```py
lo = torch.randn(batch, channels, low_len)
hi_hat = upsampler.sample(lo, num_steps=2)
```

- `lo` is the lower-rate waveform.
- The returned tensor is the higher-rate waveform.
- For exact smoke checks, keep `high_len = low_len * upsample_factor`.

## 2) Diffusion vocoding

**Goal:** condition waveform diffusion on mel spectrograms.

**Training path**

```py
wave = torch.randn(batch, channels, time)
loss = vocoder(wave)
```

- `DiffusionVocoder` converts the waveform to mel internally.
- Pass `mel_sample_rate=...` and other mel settings with the `mel_` prefix.
- The mel tensor is flattened into the diffusion conditioning path through `append_channels`.

**Sampling path**

```py
mel = torch.randn(batch, channels, mel_channels, frames)
wave_hat = vocoder.sample(mel, num_steps=2)
```

- `mel` must follow `[batch, channels, mel_channels, frames]`.
- The returned tensor is waveform-shaped `[batch, channels, time]`.

**Mel constructor recipe**

- `mel_n_fft` controls the STFT size.
- `mel_hop_length` defaults to `mel_n_fft // 4`.
- `mel_win_length` defaults to `mel_n_fft`.
- `mel_normalize` and `mel_normalize_log` are optional mel-side transforms.

## 3) Diffusion autoencoding

**Goal:** encode audio into a latent and decode by diffusion conditioned on that latent.

**Minimal local encoder contract**

```py
class TinyEncoder(EncoderBase):
    def __init__(self):
        super().__init__()
        self.out_channels = 2
        self.downsample_factor = 2

    def forward(self, x, with_info=False):
        latent = torch.cat([x[..., ::2], x[..., 1::2]], dim=1)
        info = {
            "input_shape": list(x.shape),
            "latent_shape": list(latent.shape),
        }
        return (latent, info) if with_info else latent
```

**Training path**

```py
loss, info = autoencoder(wave, with_info=True)
```

- `with_info=True` returns `(loss, info)`.
- The encoder output is injected into the diffusion model at `inject_depth`.
- `latent_factor` defaults to the encoder downsample factor.
- `adapter.encode(x)` runs before the diffusion loss if an adapter is supplied.

**Encoding and decoding**

```py
latent = autoencoder.encode(wave)
wave_hat = autoencoder.decode(latent, num_steps=2)
```

- `encode(...)` delegates to the encoder.
- `decode(...)` builds a noise tensor using the latent length and `latent_factor`, then samples the conditioned diffusion model.
- `adapter.decode(...)` runs after sampling if an adapter is supplied.

**Custom loss handoff**

- Pass `loss_fn=...` to `DiffusionAE(...)` to override the default diffusion loss.
- If available, `auraloss.freq.MultiResolutionSTFTLoss()` is a compatible custom spectral loss.
- If available, `audio_encoders_pytorch` can provide richer encoders, but it is not required for the bundled smoke or the default workflow.

## 4) Optional external encoder path

If the environment already has an external encoder package, you can replace the local dummy encoder with that encoder and keep the same wrapper contract:

- the encoder must expose `out_channels` and `downsample_factor`;
- `forward(..., with_info=True)` should return `(latent, info)` if callers rely on info;
- `inject_depth` must still align with the `channels` list;
- `adapter` remains optional and shape-preserving.

This keeps the wrapper workflow stable even when the encoder implementation changes.
