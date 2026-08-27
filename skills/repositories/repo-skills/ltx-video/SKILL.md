---
name: ltx-video
description: "Routes LTX-Video local inference, model/config selection, and
  direct pipeline/component diagnostics."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LTX-Video

Use this root skill to route repository-backed LTX-Video tasks. It is self-contained: use the bundled references and scripts rather than depending on an LTX-Video source checkout.

## Start safely

1. For local generation, install the package and inference extras in a Python 3.10+ environment:

   ```bash
   python -m pip install -e ".[inference]"
   ```

   When working only from this skill bundle, install a compatible published/local `ltx-video` package instead of using `-e`.
2. From this skill directory, run the no-download environment preflight:

   ```bash
   python scripts/check_ltx_video_env.py
   python scripts/check_ltx_video_env.py --deep-imports --json
   ```

   Add `--require-package` or `--require-cuda` only when that capability is a hard requirement. The checker never downloads checkpoints or runs generation.
3. Read [cross-cutting troubleshooting](references/troubleshooting.md) before changing dependencies or attempting a heavy checkpoint run.

## Route by intent

- Use [local-inference](sub-skills/local-inference/SKILL.md) for `inference.py` commands, `InferenceConfig`, text/image/video conditioning, prompt enhancement, output handling, and safe command construction.
- Use [model-configs](sub-skills/model-configs/SKILL.md) for choosing or validating 2B/13B, dev/distilled, FP8/bfloat16, base/multi-scale YAML configurations and checkpoint/upscaler fields.
- Use [pipeline-components](sub-skills/pipeline-components/SKILL.md) for direct `LTXVideoPipeline`/`LTXMultiScalePipeline` calls, `ConditioningItem`, schedulers, VAE/transformer loading, tensor-shape contracts, and no-download component diagnostics.

### Common boundary cases

- A request to choose a YAML and then generate routes first to **model-configs**, then to **local-inference**.
- A failing CLI/config-path/media-output request stays in **local-inference**; a failure inside a direct scheduler, VAE, transformer, latent, or pipeline call routes to **pipeline-components**.
- FP8 configuration choice belongs to **model-configs**; optional Q8/FP8 kernel import failures also use the root [troubleshooting reference](references/troubleshooting.md).

## Root references

- [Repository provenance](references/repo-provenance.md) records the source snapshot, evidence paths, and refresh rule.
- [Routing metadata](references/repo-routing-metadata.json) provides the machine-readable scenario and entry-point map.
- [Troubleshooting](references/troubleshooting.md) covers installation, imports, devices, downloads, media extras, and optional FP8 support.
- [Development and tests](references/development-and-tests.md) separates safe checks from network-, checkpoint-, and hardware-heavy verification.
- [`scripts/check_ltx_video_env.py`](scripts/check_ltx_video_env.py) performs a safe environment/backend preflight.

## Operating rules

1. Inspect and validate a command or config before starting generation; model, text-encoder, prompt-enhancer, and spatial-upscaler downloads can be large.
2. Do not treat CPU/component/config checks as proof of full checkpoint generation quality or GPU performance.
3. Prefer bfloat16 configurations unless compatible FP8/Q8 hardware and external kernels are explicitly available.
4. Keep dimensions and conditioning rules with the local-inference guidance, model-family semantics with model-configs, and direct tensor/component contracts with pipeline-components.
5. State when a check was skipped because CUDA, model cache, network access, optional media packages, or FP8 kernels were unavailable.

## Non-goals

This skill does not cover LTX-2, ComfyUI workflow editing, LTX-Video-Trainer, generic Diffusers usage, LoRA training, hosted APIs, or external control repositories. Route those requests to their own project documentation or skill; do not infer their behavior from this LTX-Video checkout.
