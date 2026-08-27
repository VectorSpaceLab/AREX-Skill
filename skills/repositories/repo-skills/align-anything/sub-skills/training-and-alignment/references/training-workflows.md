# Align-Anything Training Workflow Routing

This reference maps training requests to Align-Anything trainer modules, config identifiers, dataset family, launch style, and important caveats. It is self-contained; use package-relative identifiers only as names for modules/configs, not as links to a checkout.

## Grounded invariants

- Trainer modules read their default YAML with `read_cfgs(mode="train", task=<modality>/<algorithm>)`, then apply unknown CLI flags as leaf-key overrides.
- DeepSpeed-backed modules initialize distributed training before constructing trainer objects. Their default DeepSpeed JSON is chosen by `train_cfgs.ds_cfgs`, with `ZERO_STAGE_FILE` able to override that file at runtime.
- Supervised/DPO/RM/cost trainers are usually one-policy or score-model flows; PPO-like trainers load actor, reference actor, reward model, and reward critic/cost critic as needed.
- Diffusion SFT/DPO modules use Accelerate-style optimizer preparation while still participating in distributed barriers; prefer `torchrun` or `accelerate launch` for those modules instead of bare `python`.
- Script evidence shows shell commands passing `--module align_anything.trainers.<...>` to DeepSpeed and setting `MODEL_*`, `TRAIN_*`, `PTX_*`, and `OUTPUT_DIR` variables before launch. The bundled launch template copies that pattern without depending on repository shell scripts.

## Fast routing matrix

| Request signal | Trainer module | Config task | Primary data contract | Recommended launcher | Notes |
| --- | --- | --- | --- | --- | --- |
| Text SFT / instruction tuning | `align_anything.trainers.text_to_text.sft` | `text_to_text/sft` | supervised prompt+response | DeepSpeed | Baseline LLM SFT; supports LoRA/BnB config sections. |
| Text RM | `align_anything.trainers.text_to_text.rm` | `text_to_text/rm` | preference chosen/rejected | DeepSpeed | Builds score/reward model from preference pairs. |
| Text reward scoring | `align_anything.trainers.text_to_text.rm_score` | `text_to_text/rm_score` | preference-like scoring data | DeepSpeed | Use when scoring with an RM rather than training PPO. |
| Text DPO | `align_anything.trainers.text_to_text.dpo` | `text_to_text/dpo` | preference chosen/rejected | DeepSpeed | Loads policy and reference model from the same model path. |
| Text PPO | `align_anything.trainers.text_to_text.ppo` | `text_to_text/ppo` | prompt-only + optional PTX SFT data | DeepSpeed | Needs actor, reward model, reward critic; prompt batch must be divisible by train batch. |
| Text PPO remote RM | `align_anything.trainers.text_to_text.ppo_remote_rm` | `text_to_text/ppo_remote_rm` | prompt-only + optional PTX | DeepSpeed | Requires `remote_rm_url`; reward critic is forced to actor path if mismatched in source logic. |
| Text PPO vLLM | `align_anything.trainers.text_to_text.ppo_vllm` | `text_to_text/ppo_vllm` | prompt-only + optional PTX | DeepSpeed plus vLLM runtime | Optional acceleration path; validate vLLM package/GPU memory separately. |
| Text GRPO | `align_anything.trainers.text_to_text.grpo` | `text_to_text/grpo` | prompt-only + reward model | DeepSpeed | Generates multiple completions per prompt; uses grouped normalized rewards and KL term. |
| Text KTO | `align_anything.trainers.text_to_text.kto` | `text_to_text/kto` | unmatched supervised/preference-style data | DeepSpeed | Inherits DPO-style mechanics; confirm template supports unmatched sample formatting. |
| Text ORPO | `align_anything.trainers.text_to_text.orpo` | `text_to_text/orpo` | preference chosen/rejected | DeepSpeed | Preference objective variant; inspect config for beta/ratio defaults. |
| Text SimPO | `align_anything.trainers.text_to_text.simpo` | `text_to_text/simpo` | preference chosen/rejected | DeepSpeed | Reference-free preference objective variant built on DPO structure. |
| Text+image to text SFT | `align_anything.trainers.text_image_to_text.sft` | `text_image_to_text/sft` | multimodal supervised image+text prompt | DeepSpeed | Common LLaVA-style route; examples use `AA_TI2T` templates and optional dataset `name`. |
| Text+image to text RM | `align_anything.trainers.text_image_to_text.rm` | `text_image_to_text/rm` | multimodal preference | DeepSpeed | Uses image-aware preference collator and score model. |
| Text+image to text DPO | `align_anything.trainers.text_image_to_text.dpo` | `text_image_to_text/dpo` | multimodal preference | DeepSpeed | Typical vision-language DPO flow. |
| Text+image to text PPO | `align_anything.trainers.text_image_to_text.ppo` | `text_image_to_text/ppo` | multimodal prompt-only + optional PTX | DeepSpeed | Needs reward and critic models compatible with actor tokenizer/processor. |
| Text+image cost model | `align_anything.trainers.text_image_to_text.cost_model` | `text_image_to_text/cost_model` | safety/cost preference | DeepSpeed | Use before safer RLHF when cost feedback is required. |
| Text+image safer RLHF | `align_anything.trainers.text_image_to_text.saferlhf` | `text_image_to_text/saferlhf` | prompt-only + reward/cost + PTX | DeepSpeed | Needs actor, reward model, reward critic, cost model, and cost critic path(s). |
| Text+audio to text SFT | `align_anything.trainers.text_audio_to_text.sft` | `text_audio_to_text/sft` | audio+text supervised | DeepSpeed | Qwen2-Audio style scripts pass audio template and dataset path. |
| Text+audio to text RM/DPO/PPO | `align_anything.trainers.text_audio_to_text.{rm,dpo,ppo}` | `text_audio_to_text/{rm,dpo,ppo}` | audio preference or prompt-only | DeepSpeed | Validate audio decoding and processor support before launch. |
| Text+video to text SFT | `align_anything.trainers.text_video_to_text.sft` | `text_video_to_text/sft` | video+text supervised | DeepSpeed | Requires video decoding stack and video processor kwargs. |
| Text+video to text RM/DPO/PPO | `align_anything.trainers.text_video_to_text.{rm,dpo,ppo}` | `text_video_to_text/{rm,dpo,ppo}` | video preference or prompt-only | DeepSpeed | Watch frame count/resolution and model max length. |
| Text+video to action SFT | `align_anything.trainers.text_video_to_action.sft` | `text_video_to_action/sft` | VLA/CHORES multitask sensor data | DeepSpeed | Requires Objaverse/SPOC-style data directories and GPU; source save path has a ZeRO-stage caveat. |
| Any-to-any SFT | `align_anything.trainers.any_to_any.sft` | `any_to_any/sft` | mixed generation/understanding JSON or tokenized data | DeepSpeed | Emu3-style flow; data samples distinguish `TU` and `TG` modes. |
| Any-to-text SFT | `align_anything.trainers.any_to_text.sft` | `any_to_text/sft` | combined image/audio/text to text | DeepSpeed | Uses combined dataset helpers when multiple datasets are passed. |
| Text+image to text+image SFT/RM/DPO/PPO | `align_anything.trainers.text_image_to_text_image.{sft,rm,dpo,ppo}` | `text_image_to_text_image/{sft,rm,dpo,ppo}` | Chameleon/interleaved or tokenized `.pt` data | DeepSpeed | Often needs project preprocessing and optional Chameleon-capable Transformers runtime. |
| Text to image diffusion SFT/DPO | `align_anything.trainers.text_to_image.{sft_diffusion,dpo_diffusion}` | `text_to_image/{sft,dpo}` | diffusion prompt/image supervised or preference | `torchrun` or `accelerate launch` | Config file uses `sft.yaml`/`dpo.yaml`; module suffix is `_diffusion`. |
| Text to audio diffusion SFT/DPO | `align_anything.trainers.text_to_audio.{sft_diffusion,dpo_diffusion}` | `text_to_audio/{sft,dpo}` | diffusion prompt/audio supervised or preference | `torchrun` or `accelerate launch` | Requires audio diffusion dependencies; `text-to-audio` extra may be needed for some paths. |
| Text to video diffusion SFT/DPO | `align_anything.trainers.text_to_video.{sft_diffusion,dpo_diffusion}` | `text_to_video/{sft,dpo}` | diffusion prompt/video supervised or preference | `torchrun` or `accelerate launch` | Video diffusion is heavy; CPU substitution is not useful for real training. |
| Janus generation SFT/DPO | `align_anything.trainers.janus.{sft_gen,dpo_gen}` | `janus/{sft_gen,dpo_gen}` | tokenized/preprocessed Janus generation data | DeepSpeed plus optional Janus package | Import requires Janus-compatible package availability. |
| Janus understanding SFT/DPO | `align_anything.trainers.janus.{sft_und,dpo_und}` | `janus/{sft_und,dpo_und}` | tokenized/preprocessed Janus understanding data | DeepSpeed plus optional Janus package | Treat as optional unless Janus package/model/data are prepared. |

## Algorithm-specific planning notes

### SFT

- Required: `model_name_or_path`, `train_datasets`, `train_template`, `train_split` or equivalent local `train_data_files`, and `output_dir`.
- For multimodal SFT, verify the model loader returns both tokenizer and processor; templates emit multimodal metadata (`image`, `audio`, or `video`) consumed by dataset/collator code.
- For any-to-any SFT, set `processor_name_or_path` in addition to `model_name_or_path` when the model family needs a separate processor/tokenizer.

### RM and cost model

- Required: preference dataset with better/worse responses and a template whose `format_preference_sample` populates `better_response` and `worse_response` metadata.
- Reward models are used by PPO/GRPO and may also be trained/scored independently. Cost models are safety-specific and feed safer RLHF.
- If evaluation datasets are provided, use matching `eval_template`, `eval_split`, `eval_name`, and `eval_data_files` conventions.

### DPO, KTO, ORPO, SimPO

- DPO-family modules need preference-style data and a policy model path. DPO loads a reference model from the same base path unless the specific variant changes this behavior.
- KTO uses unmatched supervised-style samples; confirm the formatter implements `format_unmatched_supervised_sample` or the selected dataset/template combination is known to support it.
- SimPO and ORPO are text-to-text variants in this checkout; extending them to other modalities requires code adaptation, not only a config change.

### PPO and safer RLHF

- PPO needs prompt-only data for generation. Optional PTX data adds supervised regularization and doubles actor DeepSpeed batch settings in the base RL trainer when enabled.
- Required model arguments: `actor_model_name_or_path`, `reward_model_name_or_path`, `reward_critic_model_name_or_path`; safer RLHF also needs `cost_model_name_or_path` and usually a cost critic path/config.
- `per_device_prompt_batch_size` must be divisible by `per_device_train_batch_size` in PPO-like trainers.
- PPO remote RM replaces the local reward model with HTTP reward scoring through `remote_rm_url` and still trains a reward critic locally.

### GRPO

- GRPO is text-to-text in this checkout. It generates `num_generations` completions per prompt, scores them with a reward model, normalizes rewards within each group, and applies a KL penalty controlled by `beta`.
- Plan GPU memory for actor, reference actor, reward model, and multiple return sequences.

### Diffusion SFT/DPO

- The config task names are `text_to_{image,audio,video}/sft` and `.../dpo`, but the trainer module files are `sft_diffusion` and `dpo_diffusion`.
- SFT optimizes the diffusion model against supervised media targets. DPO compares preferred/rejected media targets with `beta_coeff` and `loss_type` such as sigmoid or hinge.
- Real training requires CUDA/MPS-class accelerator resources and matching diffusers/audio/video dependencies. A CPU import only proves module availability.

### Janus-aligned flows

- Janus generation (`*_gen`) and understanding (`*_und`) are separate trainer/config pairs.
- Repository scripts set a Janus-compatible package path on `PYTHONPATH`; in a reusable runtime, require the user to install/prepare that optional package rather than using placeholder paths.
- Data is commonly tokenized/preprocessed into `.pt` files. Do not assume raw image/text JSON will work without the Janus preprocessing step.

### VLA/action flow

- `text_video_to_action/sft` uses CHORES/SPOC-style multitask sensor/action data, not the standard `train_datasets`/`train_template` contract.
- Required config areas include `data_cfgs.data_dir`, `data_cfgs.dataset_task_type`, `sensor_cfgs.input_sensors`, `model_cfgs.model_architecture`, and `model_cfgs.model_version`.
- Shell evidence exports Objaverse/SPOC data environment variables before launch. Treat those as user-provided dataset locations, not defaults.

## Launcher patterns

### DeepSpeed module launch

Use this for most non-diffusion trainers:

```bash
LAUNCHER=deepspeed \
TRAINER_MODULE=align_anything.trainers.text_to_text.dpo \
MODEL_NAME_OR_PATH=meta-llama/Llama-3.1-8B-Instruct \
TRAIN_DATASETS=PKU-Alignment/PKU-SafeRLHF-single-dimension \
TRAIN_TEMPLATE=PKUSafeRLHF \
TRAIN_SPLIT=train \
OUTPUT_DIR=outputs/text_dpo \
bash scripts/launch_training_template.sh --dry-run
```

Remove `--dry-run` only after model/data/output paths and device plan are confirmed.

### Torchrun or Accelerate launch for diffusion

Use `torchrun` or `accelerate` when the trainer relies on Accelerate internals:

```bash
LAUNCHER=torchrun NUM_GPUS=1 \
TRAINER_MODULE=align_anything.trainers.text_to_image.sft_diffusion \
MODEL_NAME_OR_PATH=runwayml/stable-diffusion-v1-5 \
TRAIN_DATASETS=<dataset-or-json> TRAIN_TEMPLATE=DiffusionDB TRAIN_SPLIT=train \
OUTPUT_DIR=outputs/t2i_sft \
bash scripts/launch_training_template.sh --dry-run
```

### Slurm wrapper

Set `LAUNCHER=slurm` to generate an sbatch wrapper from the same command. The bundled script only submits when `SLURM_SUBMIT=1`; otherwise it writes a reviewable batch file.

## Source script import/adaptation map

| Repository script family inspected | Bundled treatment | Why |
| --- | --- | --- |
| `scripts/llama/*` | Adapted into `launch_training_template.sh` examples and argument mapping. | Covers text SFT/RM/DPO/PPO/GRPO/KTO/ORPO/remote RM/vLLM patterns without preserving model-specific shells. |
| `scripts/llava/*` and `scripts/qwen2_5_vl/*` | Adapted into multimodal model/data/reward argument mapping. | Shows image/VL training flags, dataset `name`, PTX data, and output handling. |
| `scripts/qwen2_audio/*` | Adapted into text-audio routing and generic launch variables. | Audio workflows use the same DeepSpeed module pattern with audio templates. |
| `scripts/safe_rlhf_v/*` | Adapted into safer-RLHF notes and model argument mapping. | Adds cost-model/cost-critic planning beyond standard PPO. |
| `scripts/vla/spoc_sft.sh` | Adapted into VLA/action data prerequisites. | Original placeholders and data roots are environment-specific; do not copy as-is. |
| `scripts/slurm/*` | Adapted into Slurm wrapper generation. | Original script points at a specific shell script; bundled launcher constructs the command directly. |
| `scripts/janus/*` | Reference/adapted notes only. | Original scripts require an optional Janus-compatible package path; keep optional caveat explicit. |
| `scripts/test/test_text_to_text.sh` | Not bundled as a runtime training launcher. | It batch-executes many shell scripts and deletes outputs; unsuitable for future task execution without careful isolation. |
