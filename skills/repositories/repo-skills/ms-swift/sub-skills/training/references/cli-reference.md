# Training CLI Reference

This reference focuses on high-impact options for `swift sft` and `swift pt`. Use `swift sft --help` and `swift pt --help` in the active environment for the full installed-version argument list.

## Routes and Launch Forms

| Form | Use |
| --- | --- |
| `swift sft ARGS...` | Supervised fine-tuning, LoRA/QLoRA/full tuning, multimodal SFT. |
| `swift pt ARGS...` | Continued pre-training; equivalent to SFT with `use_chat_template=false` and `loss_scale=all`. |
| `swift sft CONFIG.yaml` | Config-file launch; YAML/JSON keys become CLI flags. |
| `NPROC_PER_NODE=4 swift sft CONFIG.yaml` | Distributed launch through `torch.distributed.run`. |

Config `ENV` entries set environment variables only when they are not already set in the shell.

## Core Inputs

| Option | Notes |
| --- | --- |
| `--model` | Model id or local model path. Use local path plus `--check_model false` for offline/local-only runs. |
| `--model_type` | Optional architecture/template hint when auto-detection is insufficient. |
| `--dataset` | One or more dataset ids or local paths. Local JSONL/CSV/JSON/folders are supported. |
| `--cached_dataset` | Uses an already prepared cached dataset. Keep cache-time `max_length`/truncation compatible. |
| `--custom_dataset_info` | Custom registration file; route schema details to `data-model-customization`. |
| `--use_hf` | `true` uses HuggingFace source behavior; false/default uses ModelScope behavior. |
| `--check_model` | Set false for trusted local/offline model paths when remote checks would fail. |
| `--template` | Template override; `default` is often safer when adapting a base model into chat behavior. |
| `--use_chat_template` | True for SFT-style chat by default; false for `swift pt`. |
| `--loss_scale` | `all` for pre-training-style all-token loss. |

## Training Shape

| Option | Notes |
| --- | --- |
| `--train_type` | `lora`, `qlora`, `full`, and other tuner modes depending on installed extras/version. |
| `--learning_rate` | Defaults differ: full tuning uses a lower default than LoRA-like tuners. |
| `--max_length` | Primary memory and truncation control. Reduce first for OOM. |
| `--per_device_train_batch_size` | Per-device batch. Reduce for OOM. |
| `--gradient_accumulation_steps` | Raise to preserve effective batch size after reducing per-device batch. |
| `--num_train_epochs` | Epoch-based training when dataset length is known. |
| `--max_steps` | Required for streaming datasets; also useful for smoke runs. |
| `--torch_dtype` | Choose `bfloat16`, `float16`, or `float32` when defaults are not appropriate. |
| `--attn_impl` | Required as a flash attention implementation for `packing`/`padding_free`. |

## Validation and Evaluation During Training

| Option | Notes |
| --- | --- |
| `--split_dataset_ratio` | Creates a validation split from training data. |
| `--val_dataset` / `--eval_dataset` | Explicit validation/evaluation data. |
| `--eval_strategy` | Defaults to save strategy unless no validation data exists, then becomes `no`. |
| `--eval_steps` | Defaults to `save_steps` when step evaluation is used. |
| `--predict_with_generate` | Enables generation-based metrics; may increase memory/time. |
| `--eval_use_evalscope` | Training-loop EvalScope hook; requires optional `evalscope` dependency. Keep full evaluation workflows in `export-evaluation`. |
| `--eval_metric` | May require optional packages for some metrics. |

## Checkpointing and Resume

| Option | Notes |
| --- | --- |
| `--output_dir` | Explicit output root; defaults are model-derived. |
| `--add_version` | True by default; creates versioned subdirectories to avoid overwrites. |
| `--save_strategy` | `steps`, `epoch`, or `no`. |
| `--save_steps` | Step interval for checkpoint saves. |
| `--save_total_limit` | Retains best and last when set to 2. |
| `--create_checkpoint_symlink` | Creates stable `best` and `last` symlinks under output dir. |
| `--resume_from_checkpoint` | Restores weights, optimizer state, RNG, and step progress. |
| `--resume_only_model` | Loads model/adapters only from the resume checkpoint. |
| `--ignore_data_skip` | Controls data skipping when resuming only model weights. |
| `--adapters` | Loads adapter weights but is not a full training-state resume. |
| `--load_args` | Defaults false for training; be explicit if loading `args.json` is desired. |

## LoRA and Adapter Controls

| Option | Notes |
| --- | --- |
| `--target_modules` | Default often targets all linear layers. Can pass suffixes such as `q_proj k_proj v_proj`. |
| `--target_regex` | Regex targeting; overrides `target_modules`. |
| `--target_parameters` | Parameter-level LoRA targeting for layers that use `nn.Parameter`; requires a compatible PEFT version. |
| `--lora_rank` | Adapter rank. Match vLLM LoRA settings at inference if serving adapters directly. |
| `--lora_alpha` | LoRA scaling. |
| `--lora_dropout` | LoRA dropout. |
| `--lora_dtype` | LoRA module dtype. |
| `--lorap_lr_ratio` | Enables LoRA+ optimizer behavior. |
| `--use_rslora` / `--use_dora` | Variant toggles when supported by the installed dependency set. |
| `--init_weights` | Supports LoRA initializers such as PiSSA, OLoRA, LoftQ, and LoRA-GA variants. |
| `--modules_to_save` | Save extra original modules with the adapter checkpoint. |

## Multimodal Controls

| Option or ENV | Notes |
| --- | --- |
| `--freeze_llm` | Freeze or avoid adding LoRA to the LLM part, depending on tuning mode. |
| `--freeze_vit` | Defaults true; covers vision/audio tower behavior in multimodal models. |
| `--freeze_aligner` | Defaults true; controls projector/aligner training. |
| `--vit_gradient_checkpointing` | Defaults on when ViT is trainable. |
| `MAX_PIXELS` | Qwen-VL-style image memory cap; reduce for OOM. |
| `VIDEO_MAX_PIXELS` | Video frame memory cap; reduce for video OOM. |
| `--lazy_tokenize` | Often true by default for multimodal training; useful to avoid preloading media. |

## Packing and Data Pipeline

| Option | Notes |
| --- | --- |
| `--packing` | Packs samples and enables `padding_free`; requires flash attention and changes effective sample count. |
| `--padding_free` | Flattens within-batch data to reduce padding; requires flash attention. |
| `--packing_length` | Defaults to `max_length` if omitted. |
| `--packing_num_proc` | Affects packed dataset construction; different values can produce different packed datasets. |
| `--streaming` | Requires explicit `max_steps`; combine with save/eval cadence that does not depend on finite epochs. |
| `--truncation_strategy` | Keep consistent with cached dataset creation when split truncation stores input ids. |

## Distributed and Memory Backends

| Option or ENV | Notes |
| --- | --- |
| `NPROC_PER_NODE` | Enables top-level distributed launch for train routes. |
| `NNODES`, `NODE_RANK`, `MASTER_ADDR`, `MASTER_PORT` | Multi-node torchrun controls. |
| `--deepspeed` | Built-ins: `zero0`, `zero1`, `zero2`, `zero3`, `zero2_offload`, `zero3_offload`, or a config path. Requires optional DeepSpeed. |
| `--zero_hpz_partition_size` | ZeRO++ partitioning; if grad norm becomes NaN, try `--torch_dtype float16`. |
| `--deepspeed_autotp_size` | Requires DeepSpeed zero0/zero1/zero2 and full-parameter tuning. |
| `--fsdp` | Built-in `fsdp2` or config path. Do not combine with DeepSpeed or `device_map`. |
| `--gradient_checkpointing_kwargs` | For DDP reducer errors, use `'{"use_reentrant": false}'`. |
| `PYTORCH_CUDA_ALLOC_CONF` | `expandable_segments:True` can help fragmentation and flash checkpointing. |
| `CUDA_VISIBLE_DEVICES` | Select GPU devices. |

## Logging and Experiment Tracking

| Option | Notes |
| --- | --- |
| `--report_to` | Values such as `tensorboard`, `wandb`, or `swanlab` depend on installed packages. |
| `--logging_steps` | Logging interval. |
| `--run_name` | Defaults to output directory when omitted. |
| `--logging_dir` | Defaults under output directory when omitted. |
| `--swanlab_*` | Requires optional SwanLab package when reporting to `swanlab`. |
