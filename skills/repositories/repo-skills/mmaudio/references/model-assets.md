# Model Assets

Read this when selecting MMAudio variants, checking required checkpoint files,
or diagnosing weight downloads and sample-rate mismatches.

## Runtime asset layout

MMAudio expects relative asset paths at runtime. In a checkout or working
directory used to run the project commands, use this shape:

```text
ext_weights/
  best_netG.pt
  synchformer_state_dict.pth
  v1-16.pth
  v1-44.pth
weights/
  mmaudio_small_16k.pth
  mmaudio_small_44k.pth
  mmaudio_medium_44k.pth
  mmaudio_large_44k.pth
  mmaudio_large_44k_v2.pth
```

For the recommended default `large_44k_v2`, the minimal set is:

```text
ext_weights/
  synchformer_state_dict.pth
  v1-44.pth
weights/
  mmaudio_large_44k_v2.pth
```

The 16 kHz route also requires `ext_weights/best_netG.pt`.

## Variant table

| Variant | Flow checkpoint | VAE | Vocoder | Sample rate | Notes |
| --- | --- | --- | --- | ---: | --- |
| `small_16k` | `weights/mmaudio_small_16k.pth` | `ext_weights/v1-16.pth` | `ext_weights/best_netG.pt` | 16000 | Smallest 16 kHz model. |
| `small_44k` | `weights/mmaudio_small_44k.pth` | `ext_weights/v1-44.pth` | 44.1 kHz stack internal/default | 44100 | Smaller high-rate model. |
| `medium_44k` | `weights/mmaudio_medium_44k.pth` | `ext_weights/v1-44.pth` | 44.1 kHz stack internal/default | 44100 | Larger than small. |
| `large_44k` | `weights/mmaudio_large_44k.pth` | `ext_weights/v1-44.pth` | 44.1 kHz stack internal/default | 44100 | Heavy high-rate model. |
| `large_44k_v2` | `weights/mmaudio_large_44k_v2.pth` | `ext_weights/v1-44.pth` | 44.1 kHz stack internal/default | 44100 | Recommended default for generalization. |

Every variant also uses `ext_weights/synchformer_state_dict.pth` for visual
synchronization conditioning.

## Download and checksum behavior

`ModelConfig.download_if_needed()` checks the known filename, downloads the
asset if absent or if the MD5 does not match, and raises `ValueError` for an
unknown filename. Known MD5 values distilled from the source are:

| File | MD5 |
| --- | --- |
| `mmaudio_small_16k.pth` | `af93cde404179f58e3919ac085b8033b` |
| `mmaudio_small_44k.pth` | `babd74c884783d13701ea2820a5f5b6d` |
| `mmaudio_medium_44k.pth` | `5a56b6665e45a1e65ada534defa903d0` |
| `mmaudio_large_44k.pth` | `fed96c325a6785b85ce75ae1aafd2673` |
| `mmaudio_large_44k_v2.pth` | `01ad4464f049b2d7efdaa4c1a59b8dfe` |
| `v1-16.pth` | `69f56803f59a549a1a507c93859fd4d7` |
| `best_netG.pt` | `eeaf372a38a9c31c362120aba2dde292` |
| `v1-44.pth` | `fab020275fa44c6589820ce025191600` |
| `synchformer_state_dict.pth` | `5b2f5594b0730f70e41e549b7c94390c` |

Downloads are large: the flow checkpoints range from hundreds of MB to several
GB, VAEs are hundreds of MB to over 1 GB, and Synchformer is roughly 907 MB.
Ask before launching a command if network use, cache location, or download
quota matters.

## Sequence facts tied to model mode

| Mode | Nominal duration | Audio samples | Latent seq len | CLIP seq len | Sync seq len |
| --- | ---: | ---: | ---: | ---: | ---: |
| `16k` | 8.0 s | 128000 | 250 | 64 | 192 |
| `44k` | 8.0 s | 353280 | 345 | 64 | 192 |

For non-8-second inference, update `seq_cfg.duration` and call
`net.update_seq_lengths(seq_cfg.latent_seq_len, seq_cfg.clip_seq_len,
seq_cfg.sync_seq_len)` before generation.

## License and data cautions

- Code is MIT-licensed.
- Checkpoints are CC-BY-NC 4.0 according to the repository documentation, so do
  not assume commercial-use suitability.
- Training datasets named by the project have their own licenses. This skill
  does not grant rights to redistributed AudioSet, Freesound, VGGSound,
  AudioCaps, WavCaps, or Clotho data.
