# Model registry and adapter decisions

This reference is the runtime decision layer for SimpleTuner model families, flavours, and adapter formats. It is self-contained; do not follow source-repository documentation links or run source-repository scripts from here.

## Operating contract

- Treat model selection as configuration planning until the user explicitly approves downloads, training, checkpoint rewrites, or adapter exports.
- Prefer registry metadata inspection over model class imports. The registry metadata records family id, display name, class name, prediction type, and valid flavour choices.
- Use the bundled [registry inspector](../scripts/inspect_model_registry.py) for read-only installed-package metadata checks. It reads `model_metadata.json` and does not import each model class by default.
- Ask for missing `model_family` and `model_flavour` only when the requested workflow depends on architecture-specific behavior. Otherwise inspect the installed registry and present compatible options.

## Registry facts to preserve

The verified package snapshot exposed 41 model families through lazy registry metadata. Prediction-type distribution was:

| prediction type | practical meaning | count |
|---|---|---:|
| `flow_matching` | Modern flow/DiT-style models; eligible for flow features when the family implements the needed hooks. | 33 |
| `epsilon` | Diffusion/UNet-style noise-prediction families; some flow-only features require Diff2Flow bridging. | 6 |
| `sample` | Sample-prediction family; treat flow-only methods as unsupported unless a family guide says otherwise. | 1 |
| `autoregressive_next_token` | Autoregressive audio/token workflow; do not assume diffusion adapter behavior. | 1 |

Minimal registry inspection:

```bash
python skills/disco/simple-tuner/sub-skills/model-and-adapter-tooling/scripts/inspect_model_registry.py --format markdown
```

Filter one family without importing its model class:

```bash
python skills/disco/simple-tuner/sub-skills/model-and-adapter-tooling/scripts/inspect_model_registry.py --family flux2 --format json
```

## Model-family selection workflow

1. Identify the modality and output form: image, edit/reference-image, video/I2V, audio/music, or validation/evaluation only.
2. Inspect the installed registry for the family id and valid flavours.
3. Cross-check feature compatibility before recommending an adapter or experimental method:
   - PEFT LoRA and LyCORIS are broadly available but still family-dependent.
   - ControlNet is only meaningful for families with ControlNet support and conditioning datasets.
   - Flow distillation, TREAD, TwinFlow, Self-Flow, CREPA, and LayerSync require both a compatible prediction type and family hooks.
4. Keep license/commercial-use questions separate from technical support. If commercial deployment is requested, require the user to review the chosen model-weight license before producing public/published artifacts.

## Common family/flavour anchors

| intent | likely `model_family` / flavour route | adapter/tooling notes |
|---|---|---|
| High-quality image LoRA | `flux` (`dev`, `krea`, `schnell`, `kontext`, `fluxbooru`, `libreflux`) | Flow matching; Flux can use standard LoRA, LyCORIS, sliders, ControlNet on supported flavours, and several experimental regularizers. Kontext is reference-conditioned and routes dataset pairing to `data-and-config`. |
| Large current Flux route | `flux2` (`dev`, `klein-9b`, `klein-4b`) | Klein uses bundled Qwen3 text encoder and ignores guidance-embedding options; LyCORIS target module names differ from generic Attention/FeedForward names. |
| Fast accessible image LoRA | `z_image` (`turbo`, related turbo flavours) | Turbo expects an assistant LoRA; SimpleTuner can auto-fill it unless disabled. Good candidate for slider LoRA and TREAD experiments. |
| Broad Diffusers compatibility | `sdxl`, `sd3`, `pixart`, `sana`, `qwen_image` | Choose by model license, resource budget, and downstream loader compatibility. SDXL is epsilon/UNet-style; SD3/PixArt/Sana/Qwen are flow/transformer routes. |
| Video LoRA | `wan`, `ltxvideo`, `ltxvideo2`, `hunyuanvideo`, `kandinsky5_video`, `sanavideo`, `longcat_video`, `cosmos` | Check frame count/resolution, I2V support, and CREPA/TREAD/Prompt2Effect support separately. |
| Audio/music | `ace_step`, `minimax_music`, `heartmula` | Do not assume image/video LoRA conversion targets; inspect family metadata and docs first. |
| Prompt-conditioned LoRA generator | Prompt2Effect-supported families: `ltxvideo2`, `wan` I2V, `hunyuanvideo` | Requires existing effect LoRAs, a manifest, target preparation, hypernetwork training, then generation. |

## Adapter decision table

| adapter or mode | SimpleTuner config shape | Use when | Watch for |
|---|---|---|---|
| Standard PEFT LoRA | `model_type: "lora"`, `lora_type: "standard"` or omitted | Default low-rank fine-tune and easiest continuation in SimpleTuner/Diffusers. | Target modules and rank/alpha must match the family and downstream consumer. |
| LyCORIS / LoKr | `model_type: "lora"`, `lora_type: "lycoris"`, `lycoris_config: "...json"` | User needs LyCORIS algorithms such as LoKr, T-LoRA, or model-specific presets. | The config is a separate JSON; generic target names are not always valid. |
| Full-rank training | Non-LoRA model type | User explicitly needs full model updates and has backend resources. | Many full-rank routes require distributed/offload planning; route launch details to `training-workflows`. |
| ControlNet LoRA/full ControlNet | `controlnet: true` plus `model_type: "lora"` for adapter route | Conditioning should drive composition or structure. | Conditioning data pairing and auto conditioning generation belong to `data-and-config`; training is side-effectful. |
| Slider LoRA | `slider_lora_target: true`; data backends carry positive/negative/neutral `slider_strength` | Concept sliders or contrastive adapters. | Keep equal-ish positive/negative buckets; route dataloader validation to `data-and-config`. |
| Assistant LoRA | Family-specific assistant fields or automatic defaults | Distilled/turbo families that need helper adapters during training. | Disabling assistant LoRA can reduce quality; SDNQ quantization may need assistant loading deferred until after quantization. |
| Prompt2Effect generated LoRA | Prompt2Effect prepare/train/generate workflow | User wants a prompt to synthesize a PEFT LoRA after training a hypernetwork from existing LoRAs. | Not WebUI-integrated; tied to one family/base/schema/rank. |

## LoRA format choices

SimpleTuner distinguishes the adapter format from the training method.

| format | keys and consumer | Choose when |
|---|---|---|
| Diffusers/PEFT | `lora_A`, `lora_B`, `lora.down`, `lora.up`, optional `.alpha`; usually under `transformer.`, `unet.`, `text_encoder.`, or family component prefixes. | Continuing training in SimpleTuner/Diffusers or extracting adapters from weight deltas. |
| ComfyUI-style | Diffusion-model-prefixed keys such as `diffusion_model.*` or Kohya-style SD/SDXL names, with `.alpha` entries. | The user explicitly needs ComfyUI/Kohya-compatible LoRA artifacts. |

Practical rules:

- Detect before converting. A state dict with `diffusion_model.` or `model.diffusion_model.` prefixes is likely ComfyUI-style; PEFT/Diffusers keys are the default when no ComfyUI marker is present.
- Preserve or synthesize alpha values correctly. Mixed-rank LoRAs need per-module alpha patterns; uniform-rank LoRAs can usually keep a global rank/alpha scale.
- Choose the target prefix based on model family. A Flux/Flux2 transformer route is not the same as an SDXL UNet route.
- Do not promise ComfyUI export for every family. Conversion coverage is implementation-specific.

## LyCORIS specifics

Minimal LyCORIS training config:

```json
{
  "model_type": "lora",
  "lora_type": "lycoris",
  "lycoris_config": "config/lycoris_config.json",
  "validation_lycoris_strength": 1.0
}
```

Typical LoKr-like LyCORIS config shape:

```json
{
  "algo": "lokr",
  "multiplier": 1.0,
  "linear_dim": 10000,
  "linear_alpha": 1,
  "factor": 10,
  "apply_preset": {
    "target_module": ["Attention", "FeedForward"]
  }
}
```

Flux.2/Klein target modules use custom class names rather than only generic `Attention` and `FeedForward`:

```json
{
  "apply_preset": {
    "target_module": [
      "Flux2Attention",
      "Flux2FeedForward",
      "Flux2ParallelSelfAttention"
    ]
  }
}
```

Warnings:

- On SDXL, training FeedForward modules with LyCORIS can destabilize loss; if loss becomes `NaN`, train only attention blocks and disable risky attention-kernel combinations.
- T-LoRA is a LyCORIS algorithm (`algo: "tlora"`) with timestep-dependent rank masking. Keep video use experimental.

## ControlNet, CaptionFlow, and sliders

- ControlNet changes both model config and dataset semantics. Set `controlnet: true`, use `model_type: "lora"` for ControlNet LoRA, and ensure image datasets point to conditioning datasets. Conditioning generation and schema validation are owned by `data-and-config`.
- CaptionFlow is an optional captioning workflow exposed through SimpleTuner's UI and job queue. It can start local caption orchestrator/worker jobs and write captions/JSONL exports, so it is not a read-only action.
- Slider LoRA targeting changes adapter placement and sampling. Set `slider_lora_target: true`; put positive, negative, and optional neutral samples in data backends using `slider_strength` values.

## Evidence provenance

Distilled from evidence named `documentation/QUICKSTART.md`, `documentation/quickstart/*.md`, `documentation/LYCORIS.md`, `documentation/CONTROLNET.md`, `documentation/CAPTIONFLOW.md`, `documentation/SLIDER_LORA.md`, `simpletuner/helpers/models/model_metadata.json`, `simpletuner/helpers/models/registry.py`, `simpletuner/helpers/training/lora_format.py`, `tests/test_lora_format.py`, and adapter extraction tests.
