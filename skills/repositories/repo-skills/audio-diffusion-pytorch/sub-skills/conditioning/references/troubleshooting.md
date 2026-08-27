# Conditioning troubleshooting

The repository ships no pretrained weights. When a user asks to sample immediately, treat that as a shape-and-contract request unless they also provide a local checkpoint.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `DiffusionVocoder` complains about `sample_rate` or mel construction | `mel_sample_rate` was omitted or not passed with the `mel_` prefix | Pass `mel_sample_rate=...` and keep all mel-specific kwargs under the `mel_` namespace, because the wrapper strips that prefix before calling `MelSpectrogram`. |
| Torchaudio emits mel filterbank warnings on tiny fixtures | The mel/STFT fixture is unrealistically small | Treat the warning as fixture noise, not a package failure. Use small but consistent shapes for smoke checks, or silence the warning locally if needed. |
| `UNetV0` fails on group normalization with tiny channels | Default `resnet_groups=8` does not divide the chosen channel widths | Use `resnet_groups=1` for tiny smokes, or choose channel widths divisible by 8. |
| `EncoderBase` or `DiffusionAE` errors about missing fields | The encoder does not define `out_channels` and `downsample_factor` | Implement both fields on the encoder object. The public contract is those attributes plus a usable `forward(...)`. |
| `with_info=True` does not unpack cleanly | The encoder returns only a latent tensor | Return `(latent, info)` when info is requested. The autoencoder wrapper expects that tuple shape. |
| `DiffusionAE` injects at the wrong depth or shape | `inject_depth` is out of range, or `encoder.out_channels` does not match the latent channel count | Keep `inject_depth < len(channels)` and align the latent channel count with `encoder.out_channels`. Adjust the encoder or `latent_factor` if the latent time length does not line up. |
| `DiffusionAE.decode(...)` returns an unexpected length | `closest_power_2(latent_len * latent_factor)` rounded the target noise length | Use even latent lengths and a clean `latent_factor`, or override `latent_factor` explicitly. |
| `AdapterBase` wrappers change the waveform shape | The adapter modifies batch, channel, or time dimensions | Keep adapters shape-preserving. They should only transform content before and after the diffusion branch. |
| `AppendChannelsPlugin` shape mismatch | The appended conditioning tensor does not match the base tensor batch/time shape | Ensure the appended tensor has the same batch size, time length, device, and dtype as the base waveform or spectrogram tensor. |
| `upsampler.sample(...)` or `DiffusionUpsampler.forward(...)` produces an awkward length | The low-rate length was not aligned to `upsample_factor` | Prefer lengths divisible by the factor for smoke tests; the utility resampler rounds target length. |
| `audio_encoders_pytorch` or `auraloss` import fails | Optional packages are not installed | Do not make them required for the skill. Use the bundled local dummy encoder and default loss path for smoke tests. |
| A large example becomes slow or memory-heavy | The README lengths are illustrative and much larger than smoke fixtures | Shrink the tensor sizes first. Only scale up intentionally once the local contract is confirmed. |

## Fast recovery checklist

1. Confirm the wrapper you need: upsampler, vocoder, or autoencoder.
2. Check the prefix or shape contract in `references/api-reference.md`.
3. Use the bundled smoke script with tiny even lengths.
4. If the task still wants immediate sampling, ask for a local checkpoint instead of assuming pretrained weights exist.
