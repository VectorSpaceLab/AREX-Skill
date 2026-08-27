# trlX Accelerate training API reference

## Installed package facts

- Public package: `trlx` version `0.7.0`.
- Top-level public entrypoint: `trlx.train`.
- Registered methods observed: `ppoconfig`, `ilqlconfig`, `sftconfig`, `rftconfig`, plus base `methodconfig`.
- Registered Accelerate trainers observed: `AcceleratePPOTrainer`, `AccelerateILQLTrainer`, `AccelerateSFTTrainer`, `AccelerateRFTTrainer`, and base `AccelerateRLTrainer`.
- Registered pipeline for normal training: `PromptPipeline`.
- NeMo trainer names can appear in the trainer registry, but in the verified environment they were dummy entries because NeMo/Apex was not installed; route NeMo work to `../nemo/SKILL.md`.

## `trlx.train` signature and routing

```python
trlx.train(
    model_path=None,
    reward_fn=None,
    dataset=None,
    samples=None,
    rewards=None,
    prompts=None,
    eval_prompts=None,
    metric_fn=None,
    config=None,
    stop_sequences=[],
)
```

Argument behavior:

| Argument | Meaning | Notes |
| --- | --- | --- |
| `model_path` | Hugging Face model id or local model directory | Overrides `config.model.model_path` when provided. |
| `reward_fn` | Online reward callback | Called with keyword arguments `samples`, `prompts`, `outputs`, `tokenizer`, and prompt metadata. Required for PPO/RFT online training. |
| `dataset` | Deprecated offline tuple | Split into `samples` and `rewards`; prefer those explicit arguments. |
| `samples` | Offline samples | For ILQL, use with `rewards`; for SFT, omit `rewards`. Strings train whole text; even-length lists represent alternating prompt/output dialogue. |
| `rewards` | Offline scalar rewards | Must align one-to-one with `samples`. Presence selects ILQL default if `config` is omitted. |
| `prompts` | Online prompt source | List of strings or dicts with required `"prompt"` key and extra metadata. Defaults to BOS prompts if omitted in online mode. |
| `eval_prompts` | Evaluation prompt source | Same shape as `prompts`; use explicit values for reproducible evaluation. |
| `metric_fn` | Evaluation metric callback | Called with generated `samples`, decoded `prompts`, decoded `outputs`, and metadata. Return `dict[str, list[float]]` when possible. |
| `config` | `TRLConfig` | Use explicit config; implicit default selection is deprecated. |
| `stop_sequences` | List of strings | Decoded outputs are trimmed before reward/metric use. |

Internal branch selection:

1. If `config is None`, trlX warns and selects `default_ppo_config()` when `reward_fn` exists, `default_ilql_config()` when `rewards` exists, otherwise `default_sft_config()`.
2. Trainer class is resolved from `config.train.trainer` and initialized with `config`, `reward_fn`, `metric_fn`, `stop_sequences`, and `config.train.trainer_kwargs`.
3. `max_prompt_length = config.train.seq_length - config.method.gen_kwargs["max_new_tokens"]`. Ensure `max_new_tokens` exists and is smaller than `seq_length` for normal `trlx.train` generation modes.
4. Online branch: if `reward_fn` is provided, `PromptPipeline` is built from `prompts` and attached as the prompt pipeline.
5. Offline branch: if `samples` is provided, `trainer.make_experience(...)` builds the algorithm-specific store; if `rewards` is present, lengths must match.
6. If neither `reward_fn` nor `samples` is provided, trlX raises `ValueError`.

## Config classes

Top-level `TRLConfig` sections are all required when building a full config:

| Section class | Required role | Key fields |
| --- | --- | --- |
| `TrainConfig` | Training loop, trainer, logging, checkpoints | `seq_length`, `epochs`, `total_steps`, `batch_size`, `checkpoint_interval`, `eval_interval`, `pipeline`, `trainer`, `trainer_kwargs`, `checkpoint_dir`, `rollout_logging_dir`, `save_best`, `save_optimizer`, `resume_from_checkpoint`, `tracker`, `logging_dir`, `project_name`, `run_name`, `entity_name`, `group_name`, `tags`, `seed`, `minibatch_size` |
| `ModelConfig` | Model wrapper and PEFT | `model_path`, `model_arch_type` (`"causal"` or `"seq2seq"`), `num_layers_unfrozen`, `peft_config`, `model_extra_configs` |
| `TokenizerConfig` | Tokenizer loading and truncation | `tokenizer_path`, `padding_side`, `truncation_side`, `tokenizer_extra_configs` |
| `OptimizerConfig` | Optimizer registry lookup | `name`, `kwargs` |
| `SchedulerConfig` | Scheduler registry lookup | `name`, `kwargs` |
| `MethodConfig` subclass | Algorithm hyperparameters | `name` plus algorithm-specific fields below |

Algorithm config fields:

| Class | Used with | Fields |
| --- | --- | --- |
| `PPOConfig` | `AcceleratePPOTrainer` | `name`, `ppo_epochs`, `num_rollouts`, `chunk_size`, `init_kl_coef`, `target`, `horizon`, `gamma`, `lam`, `cliprange`, `cliprange_value`, `vf_coef`, `scale_reward`, `ref_mean`, `ref_std`, `cliprange_reward`, `gen_kwargs`, `gen_experience_kwargs`, `num_value_layers_unfrozen` |
| `ILQLConfig` | `AccelerateILQLTrainer` | `name`, `tau`, `gamma`, `cql_scale`, `awac_scale`, `alpha`, `beta`, `steps_for_target_q_sync`, `two_qs`, `gen_kwargs` |
| `SFTConfig` | `AccelerateSFTTrainer` | `name`, `gen_kwargs` |
| `RFTConfig` | `AccelerateRFTTrainer` | `name`, `gen_kwargs`, `start_percentile`, `end_percentile`, `n_improve_steps`, `n_generations_per_prompt` |

Default factories:

| Factory | Default trainer / pipeline / model arch / method | Intended mode |
| --- | --- | --- |
| `default_ppo_config()` | `AcceleratePPOTrainer` / `PromptPipeline` / causal / `PPOConfig` | Online PPO with `reward_fn` + `prompts` |
| `default_ilql_config()` | `AccelerateILQLTrainer` / `PromptPipeline` / causal / `ILQLConfig` | Offline ILQL with `samples` + `rewards` |
| `default_sft_config()` | `AccelerateSFTTrainer` / `PromptPipeline` / causal / `SFTConfig` | Causal SFT with `samples` only |

## Trainer classes

| Trainer | Data mode | Model wrapper | Main store/pipeline |
| --- | --- | --- | --- |
| `AcceleratePPOTrainer` | Online reward function | `AutoModelForCausalLMWithHydraValueHead` or `AutoModelForSeq2SeqLMWithHydraValueHead` | `PromptPipeline` for prompts, `PPORolloutStorage` for rollouts |
| `AccelerateILQLTrainer` | Offline reward-labeled samples | `AutoModelForCausalLMWithILQLHeads` or `AutoModelForSeq2SeqLMWithILQLHeads` | `ILQLRolloutStorage` or `ILQLSeq2SeqRolloutStorage` |
| `AccelerateSFTTrainer` | Offline samples without rewards | `AutoModelForCausalLM` | `PromptPipeline` for strings or `DialogStore` for prompt/output dialogues |
| `AccelerateRFTTrainer` | Online reward function with rejection filtering | `AutoModelForCausalLM` | `PromptPipeline`; generated outputs are filtered into selected samples |

Shared `AccelerateRLTrainer` facts:

- Builds `Accelerator(log_with=config.train.tracker, project_dir=config.train.logging_dir)`.
- Initializes tokenizer with `tokenizer_path`, `tokenizer_extra_configs`, `padding_side`, and `truncation_side`.
- Sets `tokenizer.sep_token = "<sep>"`; if no pad token exists, it sets a pad token string.
- `train.minibatch_size`, when set, must divide `train.batch_size`.
- `learn()` performs initial evaluation outside Ray, trains through `MiniBatchIterator`, saves periodic checkpoints, and logs metrics through Accelerate.

## Pipeline and data contracts

| API | Contract |
| --- | --- |
| `PromptPipeline(prompts, max_prompt_length, tokenizer, add_special_tokens=False)` | Accepts list of strings or list of dicts with `"prompt"`. Tokenizes prompts with truncation and no padding, stores metadata, and creates a padded dataloader. Dict prompts are mutated by popping `"prompt"`; pass copies if the caller needs original dicts later. |
| `DialogStore(dialogs, tokenizer)` | Stores tokenized dialogue for causal SFT. Prompt tokens have labels `-100`; output tokens are labels. |
| `tokenize_dialogue(dialogue, tokenizer, max_length=2048)` | A string becomes `[BOS, string+EOS]`. A list must have an even number of phrases alternating prompt/output. The final phrase gets EOS if missing. Truncation follows `tokenizer.truncation_side`. |
| `ILQLRolloutStorage(input_ids, attention_mask, rewards, states_ixs, actions_ixs, dones)` | Causal ILQL rollout rows. Creates `ILQLBatch` with padded fields. |
| `ILQLSeq2SeqRolloutStorage(input_ids, attention_mask, decoder_input_ids, rewards, states_ixs, actions_ixs, dones)` | Seq2seq ILQL rollout rows. Creates `ILQLSeq2SeqBatch`. |
| `PPORolloutStorage(pad_token_id, padding_side)` | PPO rollout history. `push` appends `PPORLElement`, `clear_history` resets, `export_history` writes rollout JSON to an existing directory. |
| `MiniBatchIterator(data_loader, mb_size, num_mb)` | Splits dataclass or `BatchEncoding` batches into microbatches. Warns and stops if data are too small to saturate requested minibatches. |

Data classes:

| Class | Fields |
| --- | --- |
| `PPORLElement` | `query_tensor`, `response_tensor`, `logprobs`, `values`, `rewards` |
| `PPORLBatch` | `query_tensors`, `response_tensors`, `logprobs`, `values`, `rewards` |
| `ILQLElement` | `input_ids`, `attention_mask`, `rewards`, `states_ixs`, `actions_ixs`, `dones` |
| `ILQLSeq2SeqElement` | `input_ids`, `attention_mask`, `decoder_input_ids`, `rewards`, `states_ixs`, `actions_ixs`, `dones` |
| `ILQLBatch` | Batched `ILQLElement` fields |
| `ILQLSeq2SeqBatch` | Batched `ILQLSeq2SeqElement` fields |

## Model wrappers relevant to users

| Wrapper | Purpose |
| --- | --- |
| `PreTrainedModelWrapper` | Base wrapper around Hugging Face pretrained models. Handles PEFT config creation/loading and save/load filtering. Explicitly rejects `load_in_8bit` as not fully supported. |
| `AutoModelForCausalLMWithValueHead` | Causal LM plus value head. |
| `AutoModelForCausalLMWithHydraValueHead` | Causal PPO wrapper with value head and optional frozen hydra reference head. If PEFT is active, reference logits come from the base model with adapters disabled/bypassed. |
| `AutoModelForSeq2SeqLMWithValueHead` | Seq2seq LM plus value head. Seq2seq value branching with `num_value_layers_unfrozen > 0` is unsupported. |
| `AutoModelForSeq2SeqLMWithHydraValueHead` | Seq2seq PPO wrapper with value head and T5-oriented hydra branch. |
| `ILQLHeads` | Adds V head, one or two Q heads, and target Q heads with sync by `alpha`. |
| `AutoModelForCausalLMWithILQLHeads` | Causal ILQL wrapper. Custom generation biases token logits with `beta * (Q - V)` and top-k/temperature controls. |
| `AutoModelForSeq2SeqLMWithILQLHeads` | Seq2seq ILQL wrapper with decoder-side ILQL heads and custom generation. |

PEFT save/load facts:

- A directory with `adapter_config.json` is treated as a trained adapter when PEFT is available.
- Passing a new `peft_config` while loading a directory that already contains an adapter causes the existing adapter config to be ignored.
- PPO/ILQL state dicts include `v_head.*` or `ilql_heads.*`. With PEFT, strict loading is relaxed because base weights live in the adapter/base model combination.

## Optimizer and scheduler names

Optimizer registry values:

- `adam` -> `torch.optim.Adam`
- `adamw` -> `torch.optim.AdamW`
- `sgd` -> `torch.optim.SGD`
- `adam_8bit_bnb` -> `bitsandbytes.optim.Adam8bit` if bitsandbytes is installed
- `adamw_8bit_bnb` -> `bitsandbytes.optim.AdamW8bit` if bitsandbytes is installed

Scheduler registry values:

- `cosine_annealing` -> `torch.optim.lr_scheduler.CosineAnnealingLR`
- `linear` -> `torch.optim.lr_scheduler.LinearLR`

## Logging and checkpoint APIs

- `trainer.save_pretrained(directory=None, **kwargs)` saves the underlying model, tokenizer, and config files. Default target is `config.train.checkpoint_dir/hf_model`.
- `trainer.save(directory=None, **kwargs)` saves Accelerate state to `directory or config.train.checkpoint_dir`; PEFT runs remove oversized intermediate model bins and re-save adapter/head artifacts.
- `trainer.load(directory=None, **kwargs)` loads Accelerate state. PEFT runs register a pre-hook so model adapters/heads are loaded from the input directory.
- Supported `train.tracker` values are `"wandb"`, `"tensorboard"`, and `None`; any other value raises.
