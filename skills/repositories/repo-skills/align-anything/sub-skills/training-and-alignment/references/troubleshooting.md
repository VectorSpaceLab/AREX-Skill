# Training Troubleshooting

Use this reference to diagnose Align-Anything trainer import, config, dataset, launcher, and algorithm failures before modifying source code.

## Import and dependency triage

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: align_anything` | Package not installed or checkout not on `PYTHONPATH`. | Install the package or set `AA_REPO_ROOT=<checkout-root>` when using the bundled launch script. Verify with `python -c "import align_anything"`. |
| DeepSpeed imports but warns about `CUDA_HOME` | CUDA toolkit headers are absent or not exported. | Treat this as a warning for import-only checks. For real GPU launches, set `CUDA_HOME` to the CUDA toolkit used by PyTorch or use a runtime image with toolkit headers. |
| CUDA PyTorch import succeeds but trainer import fails | PyTorch/CUDA readiness does not prove all package extras are installed. | During inspection, CUDA PyTorch import readiness was separable from trainer optional dependencies. Install the missing package named by the import error and re-run the specific trainer import. |
| DeepSpeed launch fails building fused ops/FusedAdam | CUDA toolkit, compiler, or architecture mismatch. | Confirm `torch.version.cuda`, `nvcc --version`, GPU architecture, and DeepSpeed install variant. Use a compatible prebuilt/runtime image or reinstall DeepSpeed in the target environment. |
| `ModuleNotFoundError` for Janus-related imports | Optional Janus-compatible package is not installed. | Treat Janus trainers as optional; prepare the Janus package/model/data first. Representative non-Janus trainers imported in the prepared inspection runtime; Janus requires the optional package. Do not keep placeholder `PYTHONPATH` values. |
| vLLM import/runtime failure in PPO vLLM | Optional vLLM dependency or GPU memory plan missing. | Use standard PPO unless vLLM version, tensor parallel size, and memory utilization are explicitly planned. |
| Audio/video decode import errors | Missing media dependencies or codec support. | Check `torchaudio`, `librosa`, `soundfile`, video backend packages, and system codecs. For text-to-audio diffusion, the optional text-to-audio dependency group may be needed. |
| VLA/action imports fail under `models.spoc_models` | SPOC/VLA dependencies or data runtime missing. | Treat `text_video_to_action/sft` as a specialized GPU/data workflow; prepare dependencies and Objaverse/SPOC data before launch. |

## Launcher and distributed failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Hang at first `dist.barrier()` | Distributed process group not initialized or ranks cannot communicate. | Use `deepspeed` for DeepSpeed trainers. For diffusion/Accelerate trainers, use `torchrun` or `accelerate launch`; avoid bare `python` unless verified single-process init works. |
| Address already in use / master port collision | Chosen `MASTER_PORT` is occupied. | Set a free `MASTER_PORT` explicitly or let the bundled launcher choose one. On clusters, ensure all nodes use the same port. |
| NCCL timeout or rank mismatch | Wrong `NUM_GPUS`, Slurm task layout, or host connectivity. | Match `NUM_GPUS`, `--gres`, `--ntasks-per-node`, visible CUDA devices, and launcher world size. Start with one node before multi-node. |
| `deepspeed: command not found` | DeepSpeed CLI is missing from environment. | Install/activate the training environment or run with `python -m deepspeed.launcher.runner` only if the environment supports it. |
| Torchrun works for import but fails at DeepSpeed optimizer init | DeepSpeed-backed trainer still relies on DeepSpeed optimizer/config. | Prefer the DeepSpeed launcher for non-diffusion modules unless the environment has already proven torchrun+DeepSpeed initialization. |
| Slurm job runs but cannot find script/module | Batch job working directory or environment differs from interactive shell. | Use the bundled Slurm wrapper with explicit `AA_REPO_ROOT`, module load/activation commands, and output path. Avoid relying on relative paths created in another shell. |

## Config and override failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `You must set the valid datasets path! Here is None` | `train_datasets`/`eval_datasets` was left `null` or override key missed. | Pass `--train_datasets` or set it in YAML. Inspect with `inspect_alignment_config.py --task ... --show`. |
| `You must set the valid template path! Here is None` | `train_template`/`eval_template` was omitted. | Pick a registered template matching the raw data schema. Use `--templates` with the inspection script to list names. |
| Override seems ignored | Wrong leaf key, shell quoting problem, or duplicate key updated unexpectedly. | Use leaf keys exactly as in scripts. Quote values containing spaces/comma lists. Use `--check-overrides key=value` to identify matching sections. |
| Nested section disappears after override | Category-prefixed key replaced a whole dict. | Avoid `--train_cfgs:...` and similar keys; restore config and use leaf-key overrides. |
| `save_interval`/modulo-by-zero in tiny smoke test | `epochs * len(dataloader) // save_total_limit` became zero. | Lower `save_total_limit`, increase data size/epochs, or avoid using that tiny run as a final trainer validation. |
| ZeRO config not found | `train_cfgs.ds_cfgs` or `ZERO_STAGE_FILE` points to missing DeepSpeed JSON. | Set `ZERO_STAGE_FILE` only to a JSON present in the package DeepSpeed config set or use the default. |
| Both fp16 and bf16 enabled or unsupported dtype | Precision config mismatch. | Enable only one precision mode and match GPU capability. Use fp32/`bf16=False fp16=False` for debugging if memory allows. |

## Dataset and template failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `KeyError` for dataset columns | Template does not match raw dataset schema. | Inspect the raw sample keys and choose or implement a matching formatter. For `Alpaca`, expect `instruction`, `input`, `output`; for `PKUSafeRLHF`, expect prompt/response and preference fields. |
| Preference dataset becomes empty after filtering | Formatter marks equal responses or invalid safety labels. | Check `format_preference_sample`, `check_equal`, and `check_validation` behavior; sample several rows before training. |
| PPO prompt-only duplicates disappear | Prompt-only dataset deduplicates prompts. | If the number of samples is lower than expected, verify duplicate prompts after formatting. |
| Image loading failure | Path/URL/base64/PIL object mismatch or worker cannot access local files. | Use dataset paths visible to all workers/nodes; test one formatted sample in the target environment. |
| Qwen/VL image resize error about aspect ratio | Extremely thin/tall media violates `smart_resize` aspect constraints. | Filter or resize media before training. Keep width/height ratios within processor constraints. |
| Audio decode errors or unexpected duration/frame shape | Bad file paths, codecs, sampling rates, or long clips. | Validate audio loading independently; cap duration/frames using config keys where available. |
| Video read failures or OOM | Missing video backend/codecs or too many frames/pixels. | Confirm video package availability and reduce frame count/resolution/model length before scaling. |
| Chameleon/text-image-to-text-image raw JSON fails | Trainer expects tokenized/preprocessed `.pt` files for the selected path. | Run or reproduce the appropriate preprocessing workflow first; pass dataset directory and `train_data_files`/`eval_data_files` consistently. |
| Any-to-any samples fail validation | Mode marker or input/output media fields do not match expected mode. | Ensure records distinguish understanding and generation modes and provide the corresponding input/output media fields. |
| VLA dataloader returns `None` batches | Missing sensor files, action labels, or data directory layout mismatch. | Validate `data_dir`, `dataset_task_type`, `input_sensors`, sliding window, and max-sample settings before full launch. |

## Model, tokenizer, and processor failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `trust_remote_code` prompt/failure | Model family requires custom code. | Set `trust_remote_code=True` only for trusted model sources; many configs default to true. |
| PPO reward critic tokenizer mismatch | Actor and reward critic tokenizers differ. | Use a reward critic initialized from the actor-compatible base or pass `--reward_critic_model_name_or_path` appropriately. |
| PPO remote RM reward critic path is changed at runtime | Source logic forces reward critic path to actor path when remote RM is used. | Plan for actor-compatible critic initialization. If a distinct critic is required, that is a code change, not only a CLI override. |
| Cost model missing in safer RLHF | Safety PPO requires both reward and cost feedback. | Provide reward model, reward critic, cost model, and cost critic paths or narrow to standard PPO. |
| Generation exceeds memory or truncates prompts | `model_max_length`, `max_new_tokens`, media token expansion, or long remote-RM math prompts. | Reduce batch sizes/frames/resolution, adjust max length, or choose longer-context model/config intentionally. |
| LoRA save output is not a full model | `lora_cfgs.use_lora=True` with `save_full_model=False`. | Expect adapter output; set `save_full_model=True` only if memory and licensing permit merging. |
| BnB/QLoRA load error | bits-and-bytes or GPU architecture unsupported. | Disable `use_bnb` for debugging or install a compatible BnB build. |

## Algorithm-specific failures

### SFT

- If labels are all ignored or loss is zero/NaN, inspect prompt/response split and template output. The supervised dataset masks prompt tokens and trains on the assistant response.
- If evaluation loss keys are missing, confirm `eval_datasets` and `eval_template` are set and non-empty.

### DPO / ORPO / SimPO / KTO

- If reward accuracy stays near random, inspect whether better/worse labels are reversed or equal responses were not filtered.
- If a variant expects unmatched samples (KTO), do not use a template that only implements ordinary preference pairs.
- Long response lengths can produce left-padding or response-length mismatches; reduce `model_max_length` only after confirming no critical answer truncation.

### PPO / GRPO / safer RLHF

- `per_device_prompt_batch_size` must divide cleanly by `per_device_train_batch_size`; several trainers raise explicit errors.
- PPO holds actor, reference actor, reward model, and critic/cost models. Plan memory for all of them, plus generation activations.
- PTX data is optional but changes actor batch math when enabled. If PTX length is tiny, cycling behavior may be surprising.
- GRPO multiplies completions by `num_generations`; reduce this before reducing other hyperparameters when memory fails.

### PPO remote reward model

- Confirm the reward server is reachable from every training rank at `remote_rm_url`.
- Payloads are prompt/response lists and the client expects a scalar/list/tensor-like reward convertible to tensors.
- If scoring intermittently times out, adjust `remote_rm_timeout` and `remote_rm_retry_times` or move the server closer to the training nodes.

### Diffusion SFT/DPO

- If `torch.distributed` barrier fails, use `torchrun`/`accelerate launch` so Accelerate initializes process state.
- If VAE encode or UNet OOMs, reduce resolution, batch size, gradient accumulation, or disable full UNet training with LoRA/freeze settings.
- DPO diffusion `loss_type` must be supported by the trainer (for example sigmoid or hinge in audio diffusion). Unknown values raise errors.

### Janus

- Missing Janus package is expected unless prepared. Do not mark the core package broken.
- Confirm whether the task is generation (`*_gen`) or understanding (`*_und`) before selecting trainer/config.
- Confirm tokenized `.pt` data path and filename separately; scripts usually pass a dataset directory plus `train_data_files`.

### VLA/action

- Treat CPU substitution as unsupported for meaningful training. The trainer directly moves the model to CUDA.
- The source save path has a caveat for non-ZeRO-stage saves in the VLA trainer: a variable used for plain `save_pretrained` is not initialized in the inspected code. Prefer ZeRO-backed checkpoint saving for this workflow or treat a non-ZeRO save failure as a source caveat to resolve deliberately.

## Minimal safe diagnostic sequence

1. Inspect config without imports:

   ```bash
   python scripts/inspect_alignment_config.py --task text_to_text/sft --show
   ```

2. If dependencies are supposed to be ready, optionally import the trainer:

   ```bash
   python scripts/inspect_alignment_config.py --task text_to_text/sft --import-trainer
   ```

3. Dry-run the launch command:

   ```bash
   LAUNCHER=deepspeed TRAINER_MODULE=align_anything.trainers.text_to_text.sft \
   MODEL_NAME_OR_PATH=<model> TRAIN_DATASETS=<dataset> TRAIN_TEMPLATE=<template> OUTPUT_DIR=<out> \
   bash scripts/launch_training_template.sh --dry-run
   ```

4. Only after command, model/data, output, and device plan are correct, remove `--dry-run`.
