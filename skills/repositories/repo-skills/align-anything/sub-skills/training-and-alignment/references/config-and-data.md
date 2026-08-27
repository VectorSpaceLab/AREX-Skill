# Config and Data Contracts

Use this reference before editing Align-Anything training YAML, CLI overrides, dataset templates, or modality-specific data inputs.

## Config anatomy

Training configs are grouped by modality and algorithm. The important top-level sections are:

| Section | Purpose | Common keys |
| --- | --- | --- |
| `train_cfgs` | Runtime/training hyperparameters and distributed settings. | `ds_cfgs`, `epochs`, `seed`, `per_device_train_batch_size`, `per_device_prompt_batch_size`, `gradient_accumulation_steps`, `learning_rate`, `actor_lr`, `critic_lr`, `bf16`, `fp16`, `eval_strategy`, `eval_interval`, `save_checkpoint`, `load_checkpoint`, `gradient_checkpointing`, algorithm coefficients. |
| `data_cfgs` | Dataset location, split, template, subset/name, files, size, and optional loader args. | `train_datasets`, `train_template`, `train_split`, `train_name`, `train_data_files`, `eval_*`, `ptx_*`, `load_multi_datasets`. |
| `model_cfgs` | Model identifiers and generation/model limits. | `model_name_or_path`, `actor_model_name_or_path`, `reward_model_name_or_path`, `reward_critic_model_name_or_path`, `cost_model_name_or_path`, `processor_name_or_path`, `remote_rm_url`, `trust_remote_code`, `model_max_length`, `temperature`, `top_p`. |
| `logger_cfgs` | Logging, output, cache, and checkpoint retention. | `log_type`, `log_project`, `log_run_name`, `output_dir`, `cache_dir`, `save_total_limit`, `save_interval`. |
| `lora_cfgs` | LoRA adapter training/saving. | `use_lora`, `task_type`, `r`, `lora_alpha`, `lora_dropout`, `target_modules`, `save_full_model`. |
| `bnb_cfgs` | QLoRA/bits-and-bytes quantization. | `use_bnb`, `load_in_4bit`, `load_in_8bit`, `bnb_4bit_quant_type`, `bnb_4bit_compute_dtype`. |
| `sensor_cfgs` | VLA/action sensor selection. | `input_sensors`. |
| `vllm_cfgs` | Optional PPO vLLM acceleration. | `use_vllm`, `vllm_num_engines`, `vllm_tensor_parallel_size`, `vllm_max_model_len`, `vllm_gpu_memory_utilization`. |

## Override rules

Align-Anything trainers parse unknown CLI flags and pass each `--key value` through a recursive leaf-key update helper.

Practical rules:

1. Use the same leaf-key style as repository scripts: `--model_name_or_path`, `--train_datasets`, `--train_template`, `--output_dir`, `--learning_rate`, `--epochs`.
2. Avoid category-prefixed keys such as `--train_cfgs:learning_rate` unless you have inspected the current parser. The helper can replace whole nested dictionaries when category prefixes are used incorrectly.
3. Boolean-like strings are converted when exactly `True` or `False`; lowercase `true`/`false` are not converted by the same path.
4. Numeric strings become `int`/`float`. Comma-separated strings become lists, and bracketed strings like `[a,b]` also become lists after stripping brackets.
5. The recursive update applies a matching leaf key anywhere in the config. If a leaf name appears in multiple sections, inspect first with the bundled config script.
6. `ENV_PREFIX__...` environment variables can also override YAML keys during load. Treat them as powerful global overrides and clear them when reproducing another run.
7. `ZERO_STAGE_FILE=<json>` overrides `train_cfgs.ds_cfgs` for DeepSpeed config selection and sets `ZERO_STAGE` from the selected DeepSpeed JSON.

Example safe override set:

```bash
--model_name_or_path meta-llama/Llama-3.1-8B-Instruct \
--train_datasets tatsu-lab/alpaca \
--train_template Alpaca \
--train_split train \
--output_dir outputs/llama_sft \
--epochs 1 \
--per_device_train_batch_size 1 \
--gradient_accumulation_steps 8
```

## Template flow

The training data path goes through two layers:

1. A dataset formatter registered by name, such as `Alpaca`, `PKUSafeRLHF`, `AA_TI2T`, `AA_TA2T`, `AA_TV2T`, `DiffusionDB`, `Pickapic`, `Any2Any`, `ANYTHING_TI2TI`, `SafeRLHF_V_Reward`, or `SafeRLHF_V_Cost`.
2. A model formatter/tokenizer/processor wrapper that applies the target model's chat template and converts multimodal information into the model's expected inputs.

Formatter methods used by trainer family:

| Trainer/data family | Required formatter method | Required return shape |
| --- | --- | --- |
| SFT text/multimodal | `format_supervised_sample` | `(conversation, multimodal_info)` which becomes prompt+full response. |
| RM/DPO/ORPO/SimPO preference | `format_preference_sample` | `(better_conversation, worse_conversation, meta_info)` with `better_response` and `worse_response` in metadata. |
| PPO/GRPO prompt-only | `format_prompt_only_sample` | `(prompt_conversation, multimodal_info)`; prompt-only datasets deduplicate prompts. |
| KTO/unmatched | `format_unmatched_supervised_sample` | `(conversation, multimodal_info)` with response length metadata derived by dataset code. |
| Diffusion SFT | `format_diffusion_supervised_sample` | `(prompt, multimodal_info)` where media target is available to processor/dataset code. |
| Diffusion DPO | `format_diffusion_preference_sample` | `(prompt, multimodal_info)` with preferred/rejected media fields handled by diffusion preference dataset. |

## Dataset loader behavior

- Dataset classes accept local `.json`, local `.jsonl`, or Hugging Face `load_dataset()` inputs.
- For Hugging Face datasets, configs pass `path`, `name`, `split`, `data_files`, optional args, and `trust_remote_code=True`.
- `size` limits samples for most dataset classes. Some classes select ranges, while prompt-only text data may slice a Python list after deduplication; confirm behavior when running tiny smoke tests.
- Supervised collators right-pad labels with `IGNORE_INDEX=-100` and mask the prompt portion so only assistant outputs contribute to loss.
- Preference collators concatenate better and worse samples into a `2 * batch_size` tensor and record response lengths in `meta_info.response_lens`.
- Prompt-only collators left-pad prompts for generation.
- Multimodal collators use processor/tokenizer outputs and may include image/audio/video tensors, grid metadata, or processor-specific keys. Do not assume a pure text batch.

## Data contracts by workflow

| Workflow | Minimal data fields or structure | Template examples | Notes |
| --- | --- | --- | --- |
| Text SFT | Instruction/prompt and output/response. | `Alpaca`, `AA_T2T`, `O1_T2T`, `TLDR`, `GSM8K`. | `Alpaca` combines `instruction` and `input`, then uses `output`. |
| Text preference/RM/DPO/PPO | Prompt and two responses or prompt-only rows. | `PKUSafeRLHF`, `Math-Zero-RL`. | Preference formatter must decide better/worse and provide response metadata. |
| Text+image to text | Prompt/question, image, response(s). | `AA_TI2T`, `RLAIFV`, `SPA_VL`, `SafeRLHF_V_Reward`, `SafeRLHF_V_Cost`, Qwen/VQA-style templates. | Images may be PIL objects, paths, URLs, or base64 depending on template. |
| Text+audio to text | Prompt/question, audio path/object, response(s). | `AA_TA2T`, `AA_TA2T_LLF`, `AudioCaps`, `LibriSpeech`, `AudioSet`. | Validate audio decode packages and sample-rate expectations. |
| Text+video to text | Prompt/question, video path/object, response(s). | `AA_TV2T`, `Webvid`, `SafeSora`. | Video frame extraction can be memory-heavy; plan frame count/resolution. |
| Text to image diffusion | Text prompt plus target image or preferred/rejected images. | `DiffusionDB`, `DiffusionDBCanny`, `Pickapic`. | SFT trains on prompt-image pairs; DPO trains on image preferences. |
| Text to audio diffusion | Text prompt plus target/preference audio. | `WavCaps`, `AA_T2A`. | Some paths require text-to-audio optional dependencies. |
| Text to video diffusion | Text prompt plus video target/preference. | `Webvid`, `SafeSora`. | Treat as GPU-only for meaningful training. |
| Text+image to text+image | Interleaved text/image prompt/output or tokenized `.pt`. | `ti2ti`, `Chameleon`, `ANYTHING_TI2TI`, `PICKAPIC_TI2TI`. | Chameleon-style workflows often require pre-tokenization before trainer launch. |
| Any-to-any | Mixed understanding/generation rows with a mode marker. | `Any2Any`. | Example mode names distinguish understanding (`TU`) from generation (`TG`) tasks. |
| Janus | Janus-specific generation/understanding tokenized data. | `Janus_TI2T` and Janus project templates. | Optional Janus package and preprocessing are required. |
| VLA/action | Dataset directory with task types, sensor inputs, sliding windows, action labels. | VLA config fields rather than chat template. | Uses `data_dir`, `dataset_task_type`, `input_sensors`, and model architecture/version. |

## Multi-dataset handling

Some supervised multimodal trainers support lists for `train_datasets`, `train_template`, `train_name`, `train_split`, `train_data_files`, and optional args. When lists are used:

- Keep list lengths aligned across datasets/templates/names/splits/files.
- Use the combined dataset/batch sampler path only when the trainer and dataset family support it.
- Avoid mixing incompatible modalities or collators in one combined run.
- For PTX data in PPO, set `ptx_datasets`, `ptx_template`, `ptx_split`, and optional `ptx_data_files` separately from prompt-only RL data.

## Pre-launch config checklist

Before a future Researcher runs training, confirm:

- The trainer module and config task match. Diffusion tasks are the common exception: config `text_to_image/sft` maps to module `text_to_image.sft_diffusion`.
- `output_dir` is intentional and not a shared checkpoint directory unless resuming.
- `load_checkpoint=True` has a model/output path containing the expected `slice_<step>` convention where applicable.
- `save_total_limit` is not larger than the number of expected training steps for tiny smoke tests; otherwise save interval calculation may become zero in several trainers.
- `bf16`/`fp16` match the hardware and model. Do not enable both.
- For DeepSpeed ZeRO-3, model loading code may instantiate `HfDeepSpeedConfig`; ensure the selected DeepSpeed JSON is present.
- For LoRA/BnB, optional dependencies and target modules are model-family appropriate.
- For reward/cost/critic flows, tokenizer compatibility is planned. PPO remote RM explicitly checks reward critic tokenizer compatibility with the actor tokenizer.
- For multimodal/video/audio data, media files or dataset columns are accessible from the training process, including worker processes and Slurm nodes.

## Useful config inspection commands

List all available training config tasks and inferred trainer modules:

```bash
python scripts/inspect_alignment_config.py --list
```

Show a config summary, template registry names, and potential override targets:

```bash
python scripts/inspect_alignment_config.py \
  --task text_image_to_text/ppo \
  --show \
  --templates \
  --check-overrides train_datasets=PKU-Alignment/align-anything train_template=AA_TI2T per_device_prompt_batch_size=2
```
