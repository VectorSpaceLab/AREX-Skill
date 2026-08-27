# LoRA and Quantization

InvokeAI supports multiple LoRA and quantized-weight families. Diagnose format mismatch with metadata and key patterns first; only load full weights when explicitly necessary and safe.

## LoRA Record Families

LoRA records use `type=lora` and a format-specific config. ControlLoRA uses `type=control_lora` and is distinct from ordinary LoRA because it acts as a control adapter.

Supported LoRA-style config families include:

- LyCORIS LoRA for SD1, SD2, SDXL, FLUX, FLUX.2, Z-Image, Qwen Image, and Anima.
- OMI LoRA for SDXL and FLUX.
- Diffusers LoRA for SD1, SD2, SDXL, FLUX, FLUX.2, and Z-Image.
- FLUX ControlLoRA in LyCORIS format.

LoRA configs can include trigger phrases and default LoRA settings. Trigger phrases are metadata; they do not prove compatibility with a base model.

## FLUX LoRA Format Detection

FLUX LoRA conversion utilities distinguish these format values:

| Format value | Typical signal |
| --- | --- |
| `flux.diffusers` | Diffusers-style LoRA keys. |
| `flux.kohya` | Kohya-style prefixes and underscore-separated layer names. |
| `flux.onetrainer` | OneTrainer FLUX layout. |
| `flux.control` | FLUX ControlLoRA state dict. |
| `flux.aitoolkit` | AI Toolkit metadata/key layout. |
| `flux.xlabs` | XLabs FLUX layout. |
| `flux.bfl_peft` | BFL PEFT layout. |
| `flux.onetrainer_bfl` | OneTrainer BFL-specific layout. |

If a LoRA is detected as a supported FLUX format but fails at runtime, check whether it targets transformer, CLIP, T5, ControlLoRA, or mixed components and whether the selected base family and variant match.

## Non-FLUX LoRA Notes

- Anima LoRAs commonly use Kohya-style `lora_unet_` prefixes and may target Qwen3 text encoder layers with text-encoder prefixes.
- Z-Image LoRAs may use diffusers PEFT or Kohya patterns and can target transformer and/or Qwen3 text encoder components.
- Qwen Image LoRA support distinguishes Qwen Image-specific key patterns from generic SD/FLUX assumptions.
- PEFT named-adapter keys are normalized during model-on-disk state-dict loading, so metadata-only key inspection may differ from normalized runtime keys.

## Quantized Formats

InvokeAI model formats include:

- `bnb_quantized_nf4b`: bitsandbytes NF4, used for selected FLUX main model support.
- `bnb_quantized_int8b`: bitsandbytes LLM.int8, used for selected text encoder support.
- `gguf_quantized`: GGUF/GGML quantized weights, used by selected FLUX, FLUX.2, Qwen Image, Z-Image, and Qwen3 encoder configs.

Quantization helpers rely on optional packages and hardware support. Do not assume full bitsandbytes or GGUF runtime support from import metadata alone.

## GGUF Notes

- GGUF loading reads tensors through a GGUF reader and wraps quantized tensors in a `GGMLTensor` that dequantizes for supported operations.
- Torch-compatible GGUF tensor types include unquantized/compatible F32 and F16 paths; quantized types such as Q8_0, Q5, Q4, Q3, and Q2 require dequantization helpers.
- GGUF tensor shape order is normalized when building the state dict.
- Some operations are supported through dispatch wrappers; unsupported tensor operations or dtype casts can fail even when header inspection succeeds.

## Triage Decision Tree

1. Identify record taxonomy: `base`, `type`, `format`, and `variant`.
2. Inspect safe metadata/header information: extension, safetensors metadata, GGUF magic/version, config JSON, or model index JSON.
3. For LoRA safetensors, inspect key prefixes/shapes with the bundled file inspector before loading full tensors.
4. If a LoRA is ordinary patch data, do not test it as a standalone main model.
5. If a quantized file is recognized but runtime fails, check optional package availability, CPU/GPU backend, and whether the selected config supports that quantized family.
6. If no safe metadata resolves the ambiguity, ask whether the user wants a bounded weight-load probe and explain pickle or memory risks.

## Bundled and Excluded Script Decisions

Bundled helpers are safe adaptations rather than direct runtime dependencies on source scripts:

- `classify_model_metadata.py` adapts the model classifier idea to JSON/YAML metadata and config files without loading weights.
- `inspect_model_file.py` adapts key/shape inspection to safetensors headers, GGUF headers, JSON configs, and path warnings without full tensor loads.
- `summarize_model_taxonomy.py` bundles a static taxonomy summary and can optionally inspect live enums/config tags when InvokeAI imports cleanly.

Some repository scripts are intentionally not bundled as runnable helpers:

- `check_classifiers.py` is reference-only because it assumes repository fixtures and classifier regression context.
- `allocate_vram.py` is reference-only because it intentionally consumes hardware memory.
- `remove_orphaned_models.py` is excluded from runtime helpers because deleting or unregistering models is destructive.
- Development regression helpers, release/build helpers, and network/download scripts are excluded because they are not safe default diagnostics.