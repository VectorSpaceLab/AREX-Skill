---
name: model-configs
description: "Guides LTX-Video model YAML selection, config validation, FP8 and
  multi-scale options, and checkpoint-related troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LTX-Video model configs

Use this sub-skill when a future agent must choose, inspect, validate, or safely adapt an LTX-Video YAML pipeline config. Trigger phrases include: "which LTX config", `ltxv-13b-0.9.8-distilled.yaml`, "FP8 config", "multi-scale", "spatial upscaler missing", `sampler: from_checkpoint`, "guidance scale", `prompt_enhancement_words_threshold`, and `checkpoint_path`.

## Boundaries and routes

- This sub-skill covers YAML config selection, field semantics, safe validation, FP8/multi-scale warnings, checkpoint/upscaler fields, and config-related troubleshooting.
- If the user wants to actually run generation or build a `scripts/run_ltx_inference.py`/checkout `inference.py` command, route to sibling sub-skill `../local-inference/SKILL.md`.
- If the user wants direct Python class/API internals (`LTXVideoPipeline`, `LTXMultiScalePipeline`, schedulers, VAE, transformer, `SkipLayerStrategy`), route to sibling sub-skill `../pipeline-components/SKILL.md`.
- External ComfyUI workflows and Diffusers documentation are not bundled source for this skill. Mention them only as external boundaries when the user is asking for those ecosystems.

## Fast choice map

1. **Best default for modern local script use:** `ltxv-13b-0.9.8-distilled.yaml` if the user can afford a 13B checkpoint and wants faster iterations than 13B dev.
2. **Highest quality in this catalog:** `ltxv-13b-0.9.8-dev.yaml`; warn about higher VRAM/runtime and multi-scale upscaler needs.
3. **Lightest modern option:** `ltxv-2b-0.9.8-distilled.yaml`; choose for limited VRAM or quick experiments, with quality below 13B.
4. **FP8 options:** `*-fp8.yaml` only when the user explicitly has compatible hardware and external Q8/FP8 kernels installed; otherwise choose the bfloat16 counterpart.
5. **Legacy base 2B options:** `ltxv-2b-0.9.yaml`, `ltxv-2b-0.9.1.yaml`, `ltxv-2b-0.9.5.yaml`, and `ltxv-2b-0.9.6-dev.yaml` are base bfloat16 configs with 40 denoising steps and CFG/STG. `ltxv-2b-0.9.6-distilled.yaml` is the fast legacy base distilled option with 8 steps and no CFG/STG requirement.

For the full catalog, use `references/model-config-catalog.md`.

## Operating procedure

1. **Extract constraints.** Ask or infer: target family (2B vs 13B), quality/speed priority, dev vs distilled preference, memory limits, FP8/Q8-kernel availability, whether multi-scale is acceptable, and whether remote model downloads are allowed.
2. **Pick a catalog entry.** Use `references/model-config-catalog.md`; do not require the original YAML files just to choose among bundled configs.
3. **Inspect or validate safely.** Run the bundled inspector on a config file before any generation:

   ```bash
   python scripts/inspect_ltxv_config.py --config PATH/TO/config.yaml
   python scripts/inspect_ltxv_config.py --config PATH/TO/config.yaml --json
   ```

   The inspector parses YAML and reports required-key errors, base vs multi-scale classification, FP8 warnings, checkpoint/upscaler download expectations, sampler/STG checks, and prompt-enhancement fields. It does **not** import LTX-Video, download models, or run inference.
4. **Explain consequences.** Always mention heavy first-run downloads for checkpoint/text-encoder/prompt-enhancer/upscaler fields, and mention that multi-scale generation runs a low-resolution first pass plus an upscaled second pass.
5. **Route execution.** Once a config is selected, send actual inference work to `../local-inference/SKILL.md` rather than constructing generation commands here.

## Required runtime references

- `references/model-config-catalog.md` — compact catalog of the 11 parsed source configs.
- `references/configuration.md` — field semantics, how `infer` consumes configs, required keys by pipeline type, and safe adaptation checklist.
- `references/troubleshooting.md` — config-specific failure modes and fixes.
- `scripts/inspect_ltxv_config.py` — safe standalone config inspector.

## Answer shape for future agents

For a config-selection or validation answer, include:

- recommended config name and why it matches the user's constraints;
- family/flavor/pipeline/precision summary;
- checkpoint and upscaler fields that may trigger downloads;
- FP8/Q8-kernel and multi-scale caveats when relevant;
- one safe preflight command with `scripts/inspect_ltxv_config.py`;
- route to `../local-inference/SKILL.md` if the user wants to run it.
