# GFPGAN Inference Model Selection

## Purpose

Read this when choosing a GFPGAN model version, checkpoint filename, architecture, or background upsampler setting.

## Version Map

| Version | Architecture | Channel multiplier | Typical checkpoint | Best use | Watch for |
| --- | --- | ---: | --- | --- | --- |
| `1` | `original` | `1` | `GFPGANv1.pth` | Paper-model reproduction or users explicitly asking for the original model. | May require BasicSR JIT/custom-extension setup. Can colorize/change faces more strongly. |
| `1.2` | `clean` | `2` | `GFPGANCleanv1-NoCE-C2.pth` | Sharper clean-model outputs; sometimes a makeup-like effect. | The FAQ notes v1.2 clean fine-tuning should be done via its bilinear source model then converted. |
| `1.3` | `clean` | `2` | `GFPGANv1.3.pth` | General default with more natural restoration, especially for very low-quality or relatively high-quality inputs. | Can be less sharp and may slightly alter identity. |
| `1.4` | `clean` | `2` | `GFPGANv1.4.pth` | Later public demo default with more detail and improved identity behavior. | Same clean-model dependency profile; verify checkpoint availability. |
| `RestoreFormer` | `RestoreFormer` | `2` | `RestoreFormer.pth` | Alternative face-restoration architecture exposed by the repo inference script. | Treat as a distinct model family; do not assume GFPGAN clean architecture internals. |

## Clean vs Original

- Clean models avoid the custom CUDA extension path used by the original StyleGAN2/BasicSR stack.
- Original/paper-model usage should be explicit because it has a different install story and may need `BASICSR_JIT=True` or compiled BasicSR extensions.
- For production inference where the user did not ask for the paper model, prefer clean models.

## Background Upsampler

`GFPGANer` accepts `bg_upsampler=None` or an external upsampler object. The repo inference script optionally uses Real-ESRGAN for non-face regions when CUDA is available.

Use no background upsampler when:

- The user only cares about restored faces.
- The environment is CPU-only.
- The user wants a minimal dependency environment.
- The task is a smoke check or validation case.

Use Real-ESRGAN only when:

- The user explicitly wants whole-image/background enhancement.
- `realesrgan` is installed.
- CUDA or acceptable CPU runtime is available.
- The user accepts any model download/checkpoint requirements for Real-ESRGAN.

## Weight Parameter

The repo CLI exposes `-w/--weight`, passed to `GFPGANer.enhance(..., weight=...)`. Keep the default `0.5` unless the user asks to tune restoration strength or identity/detail tradeoffs.

## Repeated Restoration

The README notes v1.3 can support repeated restorations for some low-quality inputs. Treat that as a task-specific experiment, not a guaranteed quality improvement.
