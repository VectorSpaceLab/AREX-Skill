# Conversion and extraction

This reference distills SimpleTuner adapter extraction, LoRA format conversion, model-component extraction, and sharded safetensors merge behavior. It does not authorize checkpoint mutation by itself.

## Side-effect gate

Stop for explicit user approval before any action that can:

- download model weights or Hugging Face files;
- read large local checkpoints for conversion or extraction;
- write, overwrite, merge, split, or upload model files;
- create Prompt2Effect targets, train a hypernetwork, or generate a new LoRA artifact.

When approval is missing, provide a dry-run/preflight plan only.

## Bundled helper scripts

| helper | default safety | use |
|---|---|---|
| [inspect_model_registry.py](../scripts/inspect_model_registry.py) | Read-only; no heavy model-class imports by default. | Inspect installed `model_metadata.json` as JSON or Markdown. |
| [merge_safetensors_shards.py](../scripts/merge_safetensors_shards.py) | Dry-run by default; no writes unless `--no-dry-run` is passed and the output is allowed. | Preflight and merge sharded `.safetensors` into one file while checking duplicate tensor keys. |

Registry inspection examples:

```bash
python skills/disco/simple-tuner/sub-skills/model-and-adapter-tooling/scripts/inspect_model_registry.py --format json
python skills/disco/simple-tuner/sub-skills/model-and-adapter-tooling/scripts/inspect_model_registry.py --family wan --format markdown
```

Safetensors merge dry-run:

```bash
python skills/disco/simple-tuner/sub-skills/model-and-adapter-tooling/scripts/merge_safetensors_shards.py \
  --src-dir PATH/TO/SHARDS \
  --dst-file PATH/TO/MERGED.safetensors \
  --pattern 'diffusion_pytorch_model-*.safetensors' \
  --dry-run --json
```

Approved write:

```bash
python skills/disco/simple-tuner/sub-skills/model-and-adapter-tooling/scripts/merge_safetensors_shards.py \
  --src-dir PATH/TO/SHARDS \
  --dst-file PATH/TO/MERGED.safetensors \
  --pattern 'diffusion_pytorch_model-*.safetensors' \
  --no-dry-run
```

Add `--overwrite` only when the user explicitly approves replacing an existing output file. The helper blocks using an input shard as the output path.

## Adapter extraction behavior distilled

SimpleTuner's PEFT and LyCORIS extraction scripts approximate the weight delta between a base component and a target component using SVD. Treat them as checkpoint-writing conversion tools, not as lossless model exports.

Common extraction inputs:

- `base_model`: local `.safetensors`, local Diffusers component/pipeline folder, or a Hugging Face repo id.
- `target_model`: same allowed forms as base.
- `output`: `.safetensors` file path or output directory.
- `--rank`: required extraction rank.
- `--alpha`: defaults to `rank` when omitted.
- `--component-subfolder`: defaults to `transformer`; use `none` for direct component folders.
- `--base-subfolder` and `--target-subfolder`: override the shared component subfolder.
- `--target-modules`: `default` means `to_q,to_k,to_v,to_out.0`; `all-linear` means every linear tensor; comma-separated suffixes are accepted.
- `--include` / `--exclude`: regex filters.
- `--device`: SVD device such as `cpu`, `cuda`, or `mps`.
- `--dtype`: output dtype among float32/float16/bfloat16 spellings.
- `--skip-mismatched`: skip shape mismatches instead of failing.
- `--min-delta-norm`: ignore nearly unchanged tensors.

PEFT extraction output shape:

```text
<component-prefix>.<module>.lora_A.weight
<component-prefix>.<module>.lora_B.weight
<component-prefix>.<module>.alpha
```

LyCORIS extraction output shape:

```text
<lycoris-prefix>_<module_with_underscores>.lora_down.weight
<lycoris-prefix>_<module_with_underscores>.lora_up.weight
<lycoris-prefix>_<module_with_underscores>.alpha
```

LyCORIS extraction records a `lycoris_config` metadata object and validates that the generated state dict is recognizable by LyCORIS. If LyCORIS is not installed, validation fails instead of silently producing an unverified adapter.

Extraction checks before recommending a run:

1. Confirm base and target are the same architecture/component and compatible tensor shapes.
2. Choose component subfolder and prefix based on the family (`transformer` for many DiT/video families; `unet` for many SD/SDXL routes).
3. Choose target modules deliberately. The default attention projection set is not always sufficient for concept, style, or slider behavior.
4. Make the user approve any remote downloads and output path.
5. After extraction, inspect keys and metadata, then test-load the adapter in the intended consumer before publishing.

## LoRA format conversion rules

SimpleTuner's LoRA format helpers support detection, rank/alpha inference, and selected Diffusers/PEFT to ComfyUI-style conversions.

| operation | distilled behavior |
|---|---|
| Normalize requested format | Unrecognized or empty values default to Diffusers/PEFT; `comfyui` selects ComfyUI. |
| Detect format | Prefixes like `diffusion_model.` or `model.diffusion_model.` indicate ComfyUI-style; plain PEFT spellings default to Diffusers. |
| Infer ranks | Down weights infer rank from first dimension; up weights infer rank from second dimension; conflicting ranks for one module are errors. |
| Infer alphas | Explicit `.alpha` or `.lora_alpha` values win. Mixed-rank LoRAs without alpha entries synthesize alpha per module equal to rank. |
| ComfyUI to Diffusers | Converts ComfyUI LoRA A/B names to Diffusers down/up names and returns alpha metadata. |
| Diffusers to ComfyUI | Converts family component prefixes to diffusion-model-style or SD/SDXL Kohya-style keys where supported and emits `.alpha` tensors. |

Practical guidance:

- Keep Diffusers/PEFT format when the next consumer is SimpleTuner or Diffusers training/inference.
- Convert to ComfyUI only when the user names ComfyUI/Kohya as the consumer.
- Do not mix Flux/Flux2 transformer key rules with SD/SDXL UNet key rules.
- Preserve rank/alpha metadata; missing alpha entries change effective adapter strength.

## Model and checkpoint conversion map

The following source-script behaviors were distilled as operating knowledge. They are not bundled runtime commands and should not be invoked from the source tree by a Researcher.

| conversion family | distilled use | risk |
|---|---|---|
| Flux original checkpoints to Diffusers components | Converts Flux transformer or VAE checkpoint keys into Diffusers naming and writes a Diffusers output component. | Can download large checkpoints and writes model files; dtype and selected component matter. |
| SD / SDXL Diffusers pipeline to original checkpoint | Converts UNet, VAE, and text encoder weights only; does not convert optimizer state or full training state. | Brittle mapping tied to known architectures; writing checkpoint artifacts requires approval. |
| Cosmos3 reasoner/generator extraction | Splits Cosmos3 reasoner versus generator keys and writes standalone SimpleTuner components. | Large sharded checkpoint I/O; validates selected key patterns and avoids local-path metadata. |
| Ideogram text projection extraction | Extracts selected projection keys, including remote range reads when needed. | Network and partial remote reads; output component must be validated. |
| SDNQ options extraction | Inspects installed SDNQ optimizer classes and writes an options JSON for maintainers. | Maintainer metadata update, not a user runtime conversion. |

Use these rows to plan user-approved conversion work or to explain why a source script is reference-only.

## Sharded safetensors merge behavior

The bundled merge helper adapts the safe part of SimpleTuner's shard merge utility:

- discovers shards in sorted order from `--src-dir` and `--pattern`;
- inspects tensor keys without loading full tensors during dry-run;
- fails on duplicate tensor keys across shards;
- refuses to use an input shard as the output file;
- refuses to overwrite unless `--overwrite` is passed;
- writes only when `--no-dry-run` is passed;
- writes through a temporary sibling file before moving into place.

Use this helper for single-directory shard merges such as transformer shard consolidation. It does not merge optimizer states, non-safetensors formats, or nested model repositories.

## Post-conversion validation checklist

After any approved conversion/extraction/merge:

1. Inspect the output with a safe reader and confirm key count, duplicate-free keys, and expected prefix families.
2. Confirm output size is plausible for the selected component and dtype.
3. For LoRAs, verify rank/alpha metadata and key spelling for the intended loader.
4. For converted model components, do a lightweight config/shape load before training.
5. Do not publish or upload artifacts until the user approves the exact artifact and any license/credential implications.

## Evidence provenance

Distilled from evidence named `scripts/merge_safetensors.py`, `scripts/extract_adapter_common.py`, `scripts/extract_peft_lora.py`, `scripts/extract_lycoris_adapter.py`, `scripts/extract_model_metadata.py`, `scripts/extract_cosmos3_generator.py`, `scripts/extract_cosmos3_reasoner.py`, `scripts/extract_ideogram_text_projection.py`, `scripts/extract_sdnq_options.py`, `scripts/format_conversion/*.py`, `simpletuner/helpers/training/lora_format.py`, `tests/test_extract_adapter_scripts.py`, `tests/test_extract_model_metadata.py`, and `tests/test_lora_format.py`.
