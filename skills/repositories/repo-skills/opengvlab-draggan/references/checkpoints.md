# Checkpoints and cache

## Purpose

Read this when you need to understand which checkpoint names the demo exposes, where they are cached, or how the package resolves missing weights.

## Cache location

`draggan.utils.get_path()` stores checkpoints under the cache root defined by `DRAGGAN_HOME`.
If the variable is unset, the default cache root is `~/draggan/checkpoints-pkl`.

The helper will try to download a missing file automatically from the Hugging Face mirror referenced in the source package.
The low-level model loader also has a default remote `afhqdog.pkl` URL in case you call it directly.

## UI checkpoint catalog

The browser demo exposes these checkpoint families:

| Path | Size | Notes |
| --- | ---: | --- |
| `stylegan2/stylegan2-ffhq-config-f.pkl` | 1024 | StyleGAN2 baseline portrait model |
| `stylegan2/stylegan2-cat-config-f.pkl` | 256 | Smaller cat model |
| `stylegan2/stylegan2-church-config-f.pkl` | 256 | Smaller church model |
| `stylegan2/stylegan2-horse-config-f.pkl` | 256 | Smaller horse model |
| `ada/ffhq.pkl` | 1024 | StyleGAN2-ADA face model |
| `ada/afhqcat.pkl` | 512 | Default UI checkpoint |
| `ada/afhqdog.pkl` | 512 | Dog checkpoint |
| `ada/afhqwild.pkl` | 512 | Wild checkpoint |
| `ada/brecahad.pkl` | 512 | BreCaHAD checkpoint |
| `ada/metfaces.pkl` | 512 | MetFaces checkpoint |
| `human/stylegan_human_v2_512.pkl` | 512 | Human checkpoint |
| `human/stylegan_human_v2_1024.pkl` | 1024 | Larger human checkpoint |
| `self_distill/bicycles_256_pytorch.pkl` | 256 | Self-distilled bicycle model |
| `self_distill/dogs_1024_pytorch.pkl` | 1024 | Self-distilled dog model |
| `self_distill/elephants_512_pytorch.pkl` | 512 | Self-distilled elephant model |
| `self_distill/giraffes_512_pytorch.pkl` | 512 | Self-distilled giraffe model |
| `self_distill/horses_256_pytorch.pkl` | 256 | Self-distilled horse model |
| `self_distill/lions_512_pytorch.pkl` | 512 | Self-distilled lion model |
| `self_distill/parrots_512_pytorch.pkl` | 512 | Self-distilled parrot model |

## Practical notes

- The browser demo defaults to `ada/afhqcat.pkl`.
- The low-level `load_model()` helper defaults to the remote `afhqdog.pkl` URL unless you pass a path or checkpoint name explicitly.
- If the first launch is slow, it is usually downloading a checkpoint into the cache root above.
- If you need to pre-stage a model, place the file under the cache root using the same relative path shown in the table.
