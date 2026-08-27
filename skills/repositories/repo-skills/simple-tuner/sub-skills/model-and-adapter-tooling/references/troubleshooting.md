# Troubleshooting model and adapter tooling

Use this reference to diagnose model registry, adapter, conversion, Prompt2Effect, distillation, experimental regularizer, and evaluation failures without reopening source evidence.

## First triage

1. Classify the failure: registry/config, adapter format, checkpoint conversion/extraction, safetensors merge, Prompt2Effect, distillation, experimental regularizer, CaptionFlow/evaluation, or training launch.
2. Check whether the next action is read-only. If it can write/download/train/caption/merge, pause for explicit approval.
3. Route non-owned areas:
   - dataset schemas, reference pairs, conditioning, masks, caption files, and eval datasets → `data-and-config`;
   - launch/distributed/offload/resume/backend runtime → `training-workflows`;
   - WebUI/API/jobs/cloud workers → `webui-and-operations`;
   - code/test/doc changes → `repo-development`.
4. Prefer bundled helper dry-runs before advising any heavy action.

## Registry and model-family issues

| symptom | likely cause | fix |
|---|---|---|
| Requested family is unknown | User used display name, old alias, or unsupported package version. | Run `inspect_model_registry.py --format markdown`; map display name to registry family id; ask user to upgrade only if the family is absent from installed metadata. |
| `model_flavour` rejected | Flavour not in registry metadata or family-specific quickstart. | Inspect the family with `--family`; choose one of the listed flavours or ask the user for the exact installed package version they intend to use. |
| Tooling wants to import every model class | Heavy import path was chosen unnecessarily. | Use metadata inspection instead; import model classes only when the task needs real class behavior. |
| Flow-only method fails on older diffusion model | Prediction type is epsilon/v/sample rather than flow matching. | Use a different method or explicitly plan Diff2Flow bridging if the method supports it. |

Registry command:

```bash
python skills/disco/simple-tuner/sub-skills/model-and-adapter-tooling/scripts/inspect_model_registry.py --format markdown
```

## Adapter format issues

| symptom | likely cause | fix |
|---|---|---|
| Adapter loads in SimpleTuner but not ComfyUI | Diffusers/PEFT key format was exported for a ComfyUI consumer. | Convert only if the family has a supported ComfyUI mapping; preserve `.alpha` values. |
| Adapter strength is wrong after conversion | Missing alpha entries, mixed ranks, or wrong global alpha. | Inspect keys and metadata; for mixed ranks, require per-module rank/alpha patterns. |
| ComfyUI adapter converted to Diffusers has wrong prefix | Target prefix not matched to family component. | Use `transformer` for many DiT/video families and `unet` for SD/SDXL routes; do not assume across families. |
| `NaN` during LyCORIS SDXL | FeedForward targets or risky attention kernel combination. | Remove FeedForward from LyCORIS config and train attention-only; reduce LR if needed. |
| Flux.2 LyCORIS does not converge | Generic `Attention`/`FeedForward` target names omit Flux.2 custom blocks. | Use Flux.2 target classes such as `Flux2Attention`, `Flux2FeedForward`, and optionally `Flux2ParallelSelfAttention`. |
| T-LoRA inference differs from validation | Standalone pipeline did not apply timestep-dependent rank masking. | Use SimpleTuner pipeline support or explicitly apply matching T-LoRA config in standalone inference. |

## ControlNet, sliders, and CaptionFlow

| symptom | likely cause | fix |
|---|---|---|
| ControlNet ignores conditioning | Dataloader image and conditioning datasets are not paired or `controlnet` is missing. | Set `controlnet: true`; route dataset pairing and conditioning generation to `data-and-config`. |
| ControlNet startup is slow | GPU-based conditioning generator or latent-encoded conditioning. | Make cost explicit; precompute CPU-friendly conditioning when possible. |
| Slider LoRA has weak directionality | Positive/negative buckets are imbalanced or no `slider_strength` values exist. | Add positive and negative data backends with opposite `slider_strength` signs; route validation to `data-and-config`. |
| CaptionFlow tab asks for install | Optional captioning dependencies are missing. | Install the captioning extra only with user approval; CaptionFlow can write captions/exports and use GPUs. |
| CaptionFlow raw config fields are ignored | SimpleTuner owns runtime host/port/storage/auth/dataset fields. | Keep advanced CaptionFlow settings, but expect SimpleTuner to override local runtime wiring. |

## Extraction and conversion failures

| symptom | likely cause | fix |
|---|---|---|
| No tensors extracted | Target module filter too narrow, include/exclude regex mismatch, or delta below threshold. | Start with default targets; inspect tensor key prefixes; reduce `min_delta_norm`; use `all-linear` only when intended. |
| Shape mismatch between base and target | Different architecture, component, flavour, revision, or subfolder. | Confirm both references point to the same component type; set base/target subfolders explicitly; do not skip mismatches unless the user accepts partial extraction. |
| LyCORIS extraction validation fails | LyCORIS package missing or generated state dict not recognized. | Install required LyCORIS dependency with approval or switch to PEFT extraction. |
| Converted SD/SDXL checkpoint misses optimizer state | The conversion maps model components only. | Do not claim it is a full training checkpoint; preserve training state separately if needed. |
| Flux conversion fails on missing keys | Wrong source checkpoint type or component flag. | Confirm transformer versus VAE conversion and original checkpoint key layout before writing. |
| Cosmos/Ideogram component extraction selects wrong keys | Family-specific key filters or config file mismatch. | Treat as a model-component extraction task; require source/revision and output approval, then validate selected key patterns. |

## Safetensors merge failures

Dry-run first:

```bash
python skills/disco/simple-tuner/sub-skills/model-and-adapter-tooling/scripts/merge_safetensors_shards.py \
  --src-dir PATH/TO/SHARDS \
  --dst-file PATH/TO/MERGED.safetensors \
  --dry-run --json
```

| symptom | likely cause | fix |
|---|---|---|
| No shards found | Wrong directory or glob pattern. | Set `--pattern` to match the real shard names. |
| Duplicate tensor keys | Shards are not a single disjoint shard set or include prior merged output. | Remove the wrong input from the candidate set; never merge duplicate-key shards. |
| Output exists | Write would overwrite a file. | Keep dry-run, choose a new output, or use `--overwrite` only after explicit approval. |
| Output path is one of the shards | Destination matches an input file. | Choose a separate output file outside the matched shard set. |
| Import error for safetensors/torch | Runtime lacks merge dependencies. | Install dependencies only with approval or run on an environment where SimpleTuner conversion dependencies are available. |

## Distillation failures

| symptom | likely cause | fix |
|---|---|---|
| Text encoder training rejected | Distillation methods block text encoder training. | Disable text encoder training for distillation. |
| AnyFlow rejects adapter preparation | Nonzero `lora_dropout` or unsupported target mode. | Use `lora_dropout=0.0`; remove deprecated target-mode settings. |
| AnyFlow base-prediction route errors | `diffusion_target="base_prediction"` needs adapter training and `fuse_guidance_scale=1.0`. | Set both correctly or use the default flow target. |
| Flow-DPO says low-rank required | Full-rank or non-LoRA mode selected. | Use `model_type: "lora"`; Flow-DPO is adapter-only. |
| Flow-DPO missing rejected latents | Rejected dataset is not paired as `reference_strict`. | Fix the paired conditioning dataset in `data-and-config`. |
| H3 drift rejects family or model type | Not MiniMax H3, or full-rank training. | Use H3 drift only for MiniMax H3 LoRA/LyCORIS. |
| H3 drift wraps itself | Recursive inner distiller is invalid. | Use a non-H3 inner distiller or disable nesting. |
| DMD OOM | Fake score path adds major memory. | Prefer LCM/DCM/adapter-only routes or increase backend resources with user approval. |
| TwinFlow asks for EMA | EMA teacher required by default. | Enable EMA or explicitly accept no-EMA fallback if the workflow supports it. |
| TwinFlow on SDXL fails | Diffusion model was not bridged to flow. | Add Diff2Flow settings only if the user accepts experimental behavior. |

## Experimental regularizer failures

| symptom | likely cause | fix |
|---|---|---|
| TREAD route error | Missing `routes` array or unsupported family. | Add route objects with `selection_ratio`, `start_layer_idx`, `end_layer_idx`; confirm family support. |
| TREAD slows training | Routes too small, gradient checkpointing interaction, or LoRA overhead dominates. | Adjust layer windows and ratio; disable if speed does not improve. |
| CREPA/REPA missing hidden states | Unsupported family or invalid block index. | Choose supported families and lower block index. |
| CREPA causes stripes/washed-out video | Regularization too strong or active too long. | Schedule decay, lower `crepa_lambda`, or set cutoff/threshold. |
| LayerSync cannot find layer | Block index beyond exposed hidden states. | Set student and teacher blocks to valid earlier/deeper layers. |
| Self-Flow startup rejects config | EMA disabled, teacher block missing, TwinFlow also enabled, or mask ratio too high. | Enable EMA, set teacher block, disable TwinFlow, keep mask ratio within bounds. |
| ConvRot/SDNQ quality drops | Quantization damage is model-specific. | Validate loss and samples before long runs; use bf16/fp8 route if quality is unacceptable. |

## Evaluation issues

| symptom | likely cause | fix |
|---|---|---|
| CLIP score conflicts with attention backend | SageAttention is incompatible with CLIP scoring. | Disable one of them. |
| CLIP score looks good but images are poor | CLIP measures prompt-feature alignment, not fidelity. | Use visual validation and task-specific metrics; do not rely on CLIP alone. |
| Eval loss trains on eval data | Misunderstanding of `dataset_type: "eval"`. | Eval datasets are validation-only; route dataset schema checks to `data-and-config`. |
| Eval charting missing | Tracker support limitation. | W&B has full charting; other trackers may receive only mean values. |

## Evidence provenance

Distilled from evidence named `documentation/QUICKSTART.md`, `documentation/LYCORIS.md`, `documentation/CONTROLNET.md`, `documentation/CAPTIONFLOW.md`, `documentation/SLIDER_LORA.md`, `documentation/TREAD.md`, `documentation/distillation/*.md`, `documentation/experimental/*.md`, `documentation/evaluation/*.md`, conversion/extraction source scripts, Prompt2Effect source scripts, and focused tests for adapters, LoRA format, metadata, and distillation.
