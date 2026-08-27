# Distillation and experimental features

This reference covers SimpleTuner distillation routes, experimental regularizers, Prompt2Effect, CaptionFlow-related implications, and evaluation features. It is a planning aid; real training, captioning, model downloads, or checkpoint writes require explicit user approval.

## Universal constraints

- Do not combine SimpleTuner distillation methods with text encoder training. Keep text encoder training disabled for distillation routes.
- Route generic training launch, distributed setup, offload, resume, and backend memory planning to `training-workflows`.
- Route preferred/rejected datasets, reference pairs, masks, eval datasets, caption files, and conditioning layout validation to `data-and-config`.
- Treat DMD, DCM, AnyFlow on-policy, TwinFlow, CREPA/REPA, Prompt2Effect training, CaptionFlow jobs, and large evaluations as expensive/manual unless the user approves runtime and artifacts.
- If a method depends on flow matching, confirm `prediction_type` and family support with the registry and method requirements before recommending it.

## Distillation route table

| route | enablement | use when | hard limits and checks |
|---|---|---|---|
| LCM | `distillation_method: "lcm"` with `distillation_config.lcm` | Few-step SDXL-style consistency distillation; target validation often 4-8 steps with guidance 0. | No text encoder training; quantization can reduce VRAM; example uses SDXL but concepts may generalize only when implemented. |
| DCM | `distillation_method: "dcm"`, `mode: "semantic"` or experimental `fine` | Wan-style few-step distillation where semantic mode is the stable route. | No text encoder training; fine mode is experimental and more memory-sensitive. |
| DMD | `distillation_method: "dmd"` with fake-score/generator settings | Distribution matching distillation from a large teacher to a few-step student. | Memory intensive because fake score needs a second model path; high-quality diverse data is critical; no text encoder training. |
| AnyFlow forward | `distillation_method: "anyflow"`, `anyflow.stage: "forward"` | Flow-matching MeanFlow-style adapter distillation with interval endpoints. | Requires flow-matching family hooks; adapter training requires `lora_dropout=0.0`; no text encoder training. |
| AnyFlow on-policy | `distillation_method: "anyflow"`, `anyflow.stage: "onpolicy"` | Continue a forward-stage AnyFlow adapter with on-policy DMD and discriminator adapter. | Standard PEFT LoRA route; saves discriminator adapter/optimizer; more expensive than forward-only. |
| Flow-DPO | `distillation_method: "flow_dpo"` plus `flow_custom_timesteps` | Low-rank preference training from preferred/rejected paired samples. | Flow-matching model, `model_type: "lora"`, paired `reference_strict` rejected dataset; optional mask conditioning. |
| H3 drift | `distillation_method: "h3_drift"` | MiniMax H3 LoRA/LyCORIS runs that should preserve frozen-base guidance/modality behavior. | MiniMax H3 only; low-rank only; may wrap one non-H3 inner distiller but cannot wrap itself. |
| TwinFlow | `twinflow_enabled: true`; leave `distillation_method` empty/null | Few-step RCGM/self-adversarial flow training with EMA teacher. | Flow-matching by default; diffusion models require Diff2Flow plus explicit allowance; guidance should be 0 for few-step validation. |
| Glance | Two normal LoRA runs with split `flow_custom_timesteps` | Single-image or tiny-sample flow LoRA split into early/late schedule adapters. | Not a true distillation pipeline; requires matching sigma/timestep schedule at inference. |

## AnyFlow details that affect decisions

Forward-stage AnyFlow samples two flow times, sorts them into `t >= r`, mixes diffusion (`r=t`), endpoint (`r=0`), and arbitrary intervals, applies flow shift, and trains MeanFlow-style tangent targets. Guidance fusion uses cached unconditional text embeddings.

Key config fields:

- `stage`: `forward` or `onpolicy`.
- `diffusion_ratio`, `consistency_ratio`: branch fractions.
- `central_difference_epsilon`: interval derivative offset.
- `fuse_guidance_scale`: guidance fused into the student prediction.
- `diffusion_target`: `flow` or `base_prediction` for guidance-distilled bases.
- `meanflow_weight_type`: `beta08` or `uniform`.
- `gate_value`, `deltatime_type`, `loss_weight`: FlowMap conditioning and loss controls.

Important compatibility checks:

- Adapter preparation rejects nonzero `lora_dropout`.
- Removed `target_mode` values are invalid.
- MiniMax H3 guidance-distilled runs should use `fuse_guidance_scale=1.0` and `diffusion_target="base_prediction"` when anchoring diffusion samples to the frozen base prediction.
- Joint MiniMax H3 audio-video AnyFlow is invalid when native dual schedule support is missing; use H3 drift guidance for H3 preservation concerns.

## Flow-DPO details that affect decisions

Flow-DPO compares preferred and rejected latents using adapter-enabled policy predictions and adapter-disabled reference predictions. The rejected side comes from a paired conditioning dataset with `conditioning_type=reference_strict`.

Minimal setup shape:

```json
{
  "model_type": "lora",
  "distillation_method": "flow_dpo",
  "flow_custom_timesteps": "801,694,548,338",
  "flow_timesteps_mode": "round-robin",
  "distillation_config": {
    "flow_dpo": {
      "beta": 1.0,
      "auto_beta": true,
      "norm_type": "sum",
      "anchor_alpha": 0.0
    }
  }
}
```

Use masks only when a mask/segmentation conditioning dataset is present. `anchor_alpha` adds an unmasked global MSE regularizer that constrains whole-frame drift.

## H3 drift details that affect decisions

H3 drift reuses the same MiniMax H3 model twice: adapter-enabled for the normal SFT path, then adapter-disabled under no-grad as the frozen-base reference. It does not allocate a second transformer, but it adds forward-pass cost.

Use H3 drift for MiniMax H3 LoRA/LyCORIS when preserving packed video/audio behavior and guidance-distilled behavior matters. Important fields:

- `loss_weight`: frozen-base drift loss weight; start lower for narrow concepts.
- `sft_loss_weight`: normal H3 SFT loss weight.
- `balance`: `token` or `modality` for video/audio weighting.
- `video_weight`, `audio_weight`: modality weights.
- `inner_distillation_method` and `inner_distillation_config`: optional nested distiller, except recursive H3 drift.

## TwinFlow and Diff2Flow

TwinFlow is enabled with `twinflow_*` flags rather than `distillation_method`. It expects EMA unless the user explicitly accepts a no-EMA teacher fallback. Keep validation guidance at `0.0` and use `twinflow_target_step_count` for target step count.

Diffusion/epsilon/v-pred models require explicit bridging:

```json
{
  "diff2flow_enabled": true,
  "diff2flow_loss": true,
  "twinflow_allow_diff2flow": true
}
```

Diff2Flow changes the loss landscape and is experimental. It pairs naturally with scheduled sampling because both push older diffusion models toward flow/rollout behavior.

## TREAD

TREAD token routing accelerates selected transformer layers by dropping a fraction of tokens and restoring the full sequence with gradient flow. It is training-only.

Basic config shape:

```json
{
  "tread_config": {
    "routes": [
      {"selection_ratio": 0.5, "start_layer_idx": 2, "end_layer_idx": -2}
    ]
  }
}
```

Decision points:

- Higher `selection_ratio` means more tokens dropped, more speed, and more quality/convergence risk.
- Biggest payoff is high-resolution/video attention workloads.
- Conservative LoRA routes start around `selection_ratio` 0.4-0.5 away from first/final layers.
- Masked loss can force tokens to be kept and reduce speedup.
- Supported families are limited; confirm family support before enabling.

## Scheduled sampling and ReflexFlow

Scheduled sampling trains on the model's own short rollouts to reduce exposure bias.

```json
{
  "scheduled_sampling_max_step_offset": 10,
  "scheduled_sampling_probability": 0.5,
  "scheduled_sampling_sampler": "unipc"
}
```

Rules:

- `scheduled_sampling_max_step_offset=0` disables it.
- Extra rollout forwards can slow each training step substantially.
- Ramp probability if the model needs warmup before self-generated inputs.
- Flow-matching models can use ReflexFlow-style additions through scheduled sampling fields.

## Representation and hidden-state regularizers

| feature | config shape | use when | pitfalls |
|---|---|---|---|
| REPA | `crepa_enabled: true`, image DiT block index, `crepa_lambda` | Align image DiT hidden states to frozen vision features. | Needs extra encoder memory; choose a valid block. |
| U-REPA | `urepa_enabled: true`, `urepa_lambda`, `urepa_manifold_weight` | UNet image models such as SDXL/SD1.5/Kolors. | Uses mid-block/manifold behavior; not the same as DiT REPA. |
| Video CREPA | `crepa_enabled: true`, adjacent-frame controls | Reduce flicker/identity drift for supported video families. | Adds VAE/encoder memory; can cause artifacts if too strong too long. |
| LayerSync | `layersync_enabled: true`, student/teacher block, `layersync_lambda` | Cheap self-contained alignment from an earlier layer to a deeper layer. | Requires hidden states and valid block indices; activations increase VRAM. |
| Self-Flow | `use_ema: true`, `crepa_feature_source: "self_flow"`, student/teacher blocks | EMA-teacher internal alignment without an external vision encoder. | Requires EMA; do not combine with TwinFlow; mask ratio must stay bounded. |
| ConvRot / SDNQ Hadamard | `base_model_precision: "int8-sdnq"`, `sdnq_use_hadamard: true` | Large PEFT jobs with int8 frozen base and bf16 adapters. | Validate per model; full fine-tuning needs separate proof. |
| T-LoRA | LyCORIS config `algo: "tlora"` | Timestep-dependent rank masking for limited data. | Requires LyCORIS T-LoRA support; video quality can be subpar. |

## Prompt2Effect

Prompt2Effect is a separate CLI-only workflow that trains a hypernetwork to generate PEFT LoRA weights from effect prompts. It is not part of SimpleTuner's normal image/video denoising trainer and is not WebUI-integrated.

Supported families in the inspected workflow:

- `ltxvideo2`
- `wan` I2V flavours
- `hunyuanvideo`

Workflow phases:

1. Manifest: JSONL records with `id`, `effect_prompt`, and `lora_path` for existing PEFT LoRAs.
2. Prepare: validate all LoRAs share target schema, infer base layers, SVD-canonicalize targets, write `schema.json` and `targets.safetensors`.
3. Train: frozen text encoder encodes effect prompts; hypernetwork predicts LoRA factors; base weights remain CPU by default.
4. Generate: load trained hypernetwork and prompt, emit `pytorch_lora_weights.safetensors` with PEFT keys.

Limits:

- PEFT linear LoRA only; no LyCORIS/convolution/DoRA support in the inspected workflow.
- Tied to one model family, base model, target module schema, and rank.
- Generated LoRAs require normal validation before use or publication.

## CaptionFlow

CaptionFlow is an optional SimpleTuner-integrated captioning workflow exposed through the dataset UI/job queue. It can start a local orchestrator and GPU workers, checkpoint caption storage, write `.txt` captions for local datasets, or export JSONL for Hugging Face datasets.

Use it when the user asks to caption or refresh captions before training. Treat it as a side-effectful job requiring approval for model choice, worker count, dataset writeback/export paths, and runtime cost.

## Evaluation features

| feature | use | caveats |
|---|---|---|
| CLIP score tracking | Relative prompt-adherence metric across validation prompts. | Not image quality/fidelity; meaningful comparisons need many prompts; incompatible with SageAttention. |
| Eval loss | Stable validation loss on datasets with `dataset_type: "eval"`. | Experimental; eval datasets are not used for training; full charting expects W&B, while other trackers may receive only mean values. |

You can disable eval loss while keeping eval datasets for CLIP scoring with `eval_loss_disable: true`.

## Evidence provenance

Distilled from evidence named `documentation/TREAD.md`, `documentation/CAPTIONFLOW.md`, `documentation/distillation/*.md`, `documentation/experimental/*.md`, `documentation/evaluation/*.md`, `scripts/prompt2effect/*`, and `tests/helpers/distillation/*`.
