# CLI Reference

## Purpose

Read this when constructing an InfiniteYou-FLUX command or checking whether a user-provided command uses the right option names. The bundled helper mirrors the repository's local inference surface and adds a self-contained runtime, no-download preflight controls, and explicit download authorization.

## Bundled helper modes

Use `scripts/run_infinite_you_flux.py` from this sub-skill.

| Mode | Flags | Side effects | Use when |
| --- | --- | --- | --- |
| Plan only | `--dry-run` | Adds/checks the bundled runtime path; no heavy imports, no model loads, no downloads, no writes. | You need to show or review the normalized generation plan. |
| Preflight | `--check-only` | Imports dependencies and the bundled runtime if available; checks input paths/CUDA/local model hints; no generation or downloads. | You need to diagnose setup before a heavy run. |
| Full generation | neither flag | Imports the bundled pipeline, uses CUDA, and writes a PNG. It refuses non-local/incomplete model paths unless `--allow-downloads` is set. | The user has model access, CUDA, and wants actual output. |

## Core options

The helper accepts hyphenated names and common underscore aliases. Prefer the hyphenated spelling in new instructions.

| Option | Default | Meaning |
| --- | --- | --- |
| `--implementation-root`, `--repo-root` | unset | Optional override root containing `pipelines/` for refresh/debug comparisons. Omit for normal self-contained use of the bundled runtime. |
| `--id-image` | unset | Identity image with a clear face; required for preflight and generation. |
| `--control-image` | unset | Optional face image used for five-keypoint control guidance. |
| `--out-results-dir` | `./results` | Directory where generated PNGs are saved. |
| `--prompt` | `A man, portrait, cinematic` | Text prompt. Include gender/person descriptors when the result should align that way. |
| `--base-model-path` | `./models/FLUX.1-dev` | Local FLUX base model directory by default. Remote repo ids require `--allow-downloads` and license/authentication readiness. |
| `--model-dir` | `./models/InfiniteYou` | Local InfiniteYou model tree by default. Remote/fallback behavior requires `--allow-downloads`. |
| `--allow-downloads` | off | Explicitly permit upstream model download/fallback behavior during full generation. Never needed for dry-run/check-only. |
| `--infu-flux-version` | `v1.0` | Only `v1.0` is supported by this repository snapshot. |
| `--model-version` | `aes_stage2` | `aes_stage2` or `sim_stage1`. |
| `--cuda-device` | `0` | CUDA device index. |
| `--seed` | `0` | `0` requests a random seed; nonzero values make a run repeatable if the same runtime state is used. |
| `--width`, `--height` | `864`, `1152` | Output/control canvas size used by the wrapper. |
| `--guidance-scale` | `3.5` | Text guidance scale. The README typo `guideance_scale` is not the actual flag. |
| `--num-steps` | `30` | Denoising steps. Fewer steps may reduce latency. |
| `--infusenet-conditioning-scale` | `1.0` | Strength of identity InfuseNet residual conditioning. |
| `--infusenet-guidance-start` | `0.0` | Fraction of denoising process where InfuseNet begins. |
| `--infusenet-guidance-end` | `1.0` | Fraction where InfuseNet stops. |
| `--enable-realism-lora` | off | Load optional Realism LoRA if present. |
| `--enable-anti-blur-lora` | off | Load optional Anti-blur LoRA if present. |
| `--quantize-8bit` | off | Quantize selected modules with optimum-quanto. |
| `--cpu-offload` | off | Stage models between CPU and CUDA to reduce peak VRAM. This still requires CUDA. |
| `--json` | off | JSON output for dry-run/check-only diagnostics. |

## Model version decision

| Version | Best when | Trade-off |
| --- | --- | --- |
| `aes_stage2` | Default; stronger text-image alignment and aesthetics after supervised fine-tuning. | May be slightly less identity-similarity focused. |
| `sim_stage1` | User prioritizes identity similarity. | If identity adherence is too strong or prompt alignment weakens, try `--infusenet-guidance-start 0.1` or a slightly lower conditioning scale. |

## Memory flags

Documented peak VRAM from the repository README:

| Setting | Approximate peak VRAM |
| --- | --- |
| no memory flags | 43 GB |
| `--cpu-offload` | 30 GB |
| `--quantize-8bit` | 24 GB |
| both flags | 16 GB |

These are CUDA memory reductions, not CPU execution modes. If CUDA is unavailable, the generation path needs code changes.

## Output behavior

The bundled helper saves a PNG to `--out-results-dir`. The filename includes a numeric index, the identity-image stem, a sanitized prompt prefix, and the seed. Check that the output directory exists or that its parent can be created before a full run.

## Command examples

No-download preflight using local models:

```bash
python scripts/run_infinite_you_flux.py --check-only \
  --id-image path/to/id.jpg \
  --prompt "A person, portrait, cinematic" \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev
```

Low-memory default-style run:

```bash
python scripts/run_infinite_you_flux.py \
  --id-image path/to/id.jpg \
  --prompt "A person, portrait, cinematic" \
  --out-results-dir path/to/results \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev \
  --cpu-offload --quantize-8bit
```

Higher identity-similarity run:

```bash
python scripts/run_infinite_you_flux.py \
  --id-image path/to/id.jpg \
  --prompt "A person, portrait, cinematic" \
  --model-version sim_stage1 \
  --infusenet-guidance-start 0.1 \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev \
  --cpu-offload --quantize-8bit
```

Control-image run:

```bash
python scripts/run_infinite_you_flux.py \
  --id-image path/to/id.jpg \
  --control-image path/to/control-face.jpg \
  --prompt "A person, cinematic portrait" \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev \
  --cpu-offload --quantize-8bit
```

Explicit remote-download run only after approval:

```bash
python scripts/run_infinite_you_flux.py \
  --id-image path/to/id.jpg \
  --prompt "A person, portrait, cinematic" \
  --model-dir ByteDance/InfiniteYou \
  --base-model-path black-forest-labs/FLUX.1-dev \
  --allow-downloads \
  --cpu-offload --quantize-8bit
```
