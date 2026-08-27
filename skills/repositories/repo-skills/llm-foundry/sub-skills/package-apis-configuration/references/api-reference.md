# LLM Foundry API Reference

This reference covers the installed package API surface used by configuration, registry, and lightweight inspection tasks. It deliberately avoids data-prep, training, evaluation, inference, and checkpoint-conversion workflows.

## Package identity

- Distribution name: `llm-foundry`
- Import package: `llmfoundry`
- Observed version in the prepared package facts: `0.23.0.dev0`
- Console script: `llmfoundry`
- Top-level exports include `__version__`, `StreamingTextDataset`, `StreamingFinetuningDataset`, `InContextLearningDataset`, `InContextLearningMetric`, `ComposerHFCausalLM`, `MPTConfig`, `MPTPreTrainedModel`, `MPTModel`, `MPTForCausalLM`, `ComposerMPTCausalLM`, `DecoupledLionW`, and package namespaces such as `algorithms`, `callbacks`, `data`, `eval`, `loggers`, `metrics`, `models`, `optim`, `tokenizers`, `tp`, and `utils`.

Use the API probe when the active environment is uncertain:

```bash
python scripts/llmfoundry_api_probe.py
```

## Installed registry entries

LLM Foundry uses typed `catalogue` registries under `llmfoundry.registry` and `llmfoundry.layers_registry`. Main runtime registries observed in the installed package are:

| Registry | Entries |
| --- | --- |
| `models` | `contrastive_lm`, `finetune_embedding_model`, `fmapi_causal_lm`, `fmapi_chat`, `hf_causal_lm`, `hf_t5`, `mpt_causal_lm`, `openai_causal_lm`, `openai_chat` |
| `dataloaders` | `contrastive_pairs`, `finetuning`, `text` |
| `callbacks` | `early_stopper`, `env_logging`, `eval_output_logging`, `fdiff_metrics`, `generate_callback`, `global_lr_scaling`, `hf_checkpointer`, `kill_loss_spike`, `layer_freezing`, `load_checkpoint`, `loss_perp_v_len`, `lr_monitor`, `mbmoe_tok_per_expert`, `memory_monitor`, `memory_snapshot`, `mono_checkpoint_saver`, `nan_monitor`, `oom_observer`, `optimizer_monitor`, `run_timeout`, `runtime_estimator`, `scheduled_gc`, `speed_monitor`, `system_metrics_monitor` |
| `callbacks_with_config` | `async_eval`, `curriculum_learning`, `dataset_swap` |
| `optimizers` | `adalr_lion`, `clip_lion`, `decoupled_adamw`, `decoupled_lionw`, `no_op` |
| `schedulers` | `constant_with_warmup`, `cosine_with_warmup`, `inv_sqrt_with_warmup`, `linear_decay_with_warmup` |
| `algorithms` | `alibi`, `gated_linear_units`, `gradient_clipping`, `low_precision_layernorm` |
| `tokenizers` | `tiktoken` |
| `metrics` | `language_cross_entropy`, `language_perplexity`, `lm_accuracy`, `lm_expected_calibration_error`, `masked_accuracy`, `mc_accuracy`, `mc_expected_calibration_error`, `qa_accuracy`, `token_accuracy` |
| `loggers` | `in_memory_logger`, `inmemory`, `mlflow`, `mosaicml`, `tensorboard`, `wandb` |

Additional typed registries useful for lower-level package work include `dataset_replication_validators`, `collators`, `data_specs`, `icl_datasets`, `config_transforms`, `load_planners`, `save_planners`, `tp_strategies`, `norms`, `param_init_fns`, `module_init_fns`, `ffns`, `ffns_with_norm`, `ffns_with_megablocks`, `attention_classes`, `attention_implementations`, and `fcs`.

## Public constructor signatures

The following signatures are the key package API contracts for this sub-skill.

```python
MPTConfig(
    d_model: int = 2048,
    n_heads: int = 16,
    n_layers: int = 24,
    head_dim: Optional[int] = None,
    expansion_ratio: Union[int, float] = 4,
    max_seq_len: int = 2048,
    vocab_size: int = 50368,
    resid_pdrop: float = 0.0,
    emb_pdrop: float = 0.0,
    learned_pos_emb: bool = True,
    attn_config: Optional[dict] = None,
    ffn_config: Optional[dict] = None,
    init_device: str = 'cpu',
    logit_scale: Union[float, str, None] = None,
    no_bias: bool = False,
    attention_bias: Optional[bool] = None,
    embedding_fraction: float = 1.0,
    norm_type: str = 'low_precision_layernorm',
    norm_eps: float = 1e-5,
    use_cache: bool = False,
    init_config: Optional[dict] = None,
    fc_type: Union[str, dict] = 'torch',
    tie_word_embeddings: bool = True,
    use_pad_tok_in_ffn: bool = True,
    block_overrides: Optional[dict[str, Any]] = None,
    final_logit_softcapping: Optional[float] = None,
    **kwargs: Any,
)

MPTForCausalLM(config: MPTConfig)

ComposerMPTCausalLM(
    tokenizer: Optional[PreTrainedTokenizerBase] = None,
    use_train_metrics: Optional[bool] = True,
    additional_train_metrics: Optional[list] = None,
    loss_fn: Optional[Union[str, dict]] = 'fused_crossentropy',
    **kwargs: dict[str, Any],
)

ComposerHFCausalLM(
    tokenizer: PreTrainedTokenizerBase,
    pretrained_model_name_or_path: str,
    pretrained: bool = True,
    pretrained_lora_id_or_path: Optional[str] = None,
    trust_remote_code: bool = True,
    use_auth_token: bool = False,
    use_flash_attention_2: bool = False,
    load_in_8bit: bool = False,
    init_device: str = 'cpu',
    config_overrides: Optional[dict[str, Any]] = None,
    peft_config: Optional[dict[str, Any]] = None,
    use_train_metrics: bool = True,
    allow_embedding_resizing: bool = False,
    additional_train_metrics: Optional[list] = None,
    additional_eval_metrics: Optional[list] = None,
    should_save_peft_only: bool = True,
    attn_implementation: Optional[str] = None,
)

# Public introspection may report ComposerHFT5 as (*args, **kwargs) because it is experimental.
# Operational constructor parameters are:
ComposerHFT5(
    tokenizer: PreTrainedTokenizerBase,
    pretrained_model_name_or_path: str,
    pretrained: bool = True,
    trust_remote_code: bool = True,
    use_auth_token: bool = False,
    config_overrides: Optional[dict[str, Any]] = None,
    init_device: str = 'cpu',
    additional_train_metrics: Optional[list] = None,
    name: Optional[str] = None,
)

DecoupledLionW(
    params: Union[Iterable[torch.Tensor], Iterable[dict]],
    lr: float = 1e-4,
    betas: tuple[float, float] = (0.9, 0.99),
    weight_decay: float = 0.0,
)
```

## Builder functions

The builders in `llmfoundry.utils.builders` are the stable entry points from YAML/config dicts into registries.

```python
build_tokenizer(tokenizer_name: str, tokenizer_kwargs: dict[str, Any]) -> PreTrainedTokenizerBase
build_composer_model(name: str, cfg: dict[str, Any], tokenizer: Optional[PreTrainedTokenizerBase], init_context: Optional[ContextManager] = None, master_weights_dtype: Optional[str] = None) -> ComposerModel
build_optimizer(model: torch.nn.Module, name: str, optimizer_config: dict[str, Any]) -> Optimizer
build_scheduler(name: str, scheduler_config: Optional[dict[str, Any]] = None) -> ComposerScheduler
build_callback(name: str, kwargs: Optional[dict[str, Any]] = None, train_config: Any = None) -> Callback
build_logger(name: str, kwargs: Optional[dict[str, Any]] = None) -> LoggerDestination
build_algorithm(name: str, kwargs: Optional[dict[str, Any]] = None) -> Algorithm
build_metric(name: str, kwargs: Optional[dict[str, Any]] = None) -> Metric
build_icl_evaluators(icl_tasks, tokenizer, default_max_seq_len, default_batch_size, destination_dir=None, icl_subset_num_batches=None) -> tuple[list[Evaluator], list[str]]
build_load_planner(name: str, **kwargs: Any) -> LoadPlanner
build_save_planner(name: str, **kwargs: Any) -> SavePlanner
build_tp_strategies(name: str, model: ComposerModel) -> dict[str, ParallelStyle]
```

Builder behavior to remember:

- `build_tokenizer` checks `registry.tokenizers` first. If the name is not registered, it calls Hugging Face `AutoTokenizer.from_pretrained`, which can download unless the name/path is local and cached.
- `build_composer_model` passes `tokenizer` plus the model config dict into `registry.models`; `mpt_causal_lm` maps to `ComposerMPTCausalLM`, `hf_causal_lm` maps to `ComposerHFCausalLM`, and `hf_t5` maps to `ComposerHFT5`.
- `build_callback` uses `callbacks_with_config` when the callback name is registered there, deep-copies the full train config into reserved keyword `train_config`, and rejects user-provided `train_config` inside callback kwargs.
- `build_optimizer` extracts params from the model. Do not include `params` in optimizer config. `disable_grad` and `param_groups` are processed before registry construction; pass a copy of the config if it will be reused.
- `build_scheduler`, `build_logger`, `build_algorithm`, and `build_metric` use exact registry keys and pass kwargs through to constructors.

## Common YAML/API fragments

Model config fragments are generally nested under `model`, `tokenizer`, `optimizer`, `scheduler`, `callbacks`, `algorithms`, and `loggers` keys in train/eval YAMLs. Examples of API-key-bearing or remote-loading configs belong to the owning workflow sub-skill; here, use them only to reason about constructor keys.

```yaml
model:
  name: mpt_causal_lm
  d_model: 2048
  n_heads: 16
  n_layers: 24
  max_seq_len: 2048
  attn_config:
    attn_impl: flash
  loss_fn: torch_crossentropy  # safer than fused_crossentropy for CPU/API checks

tokenizer:
  name: tiktoken
  kwargs:
    model_name: gpt-4

optimizer:
  name: decoupled_lionw
  lr: 1.0e-4
  betas: [0.9, 0.99]
  weight_decay: 0.0

scheduler:
  name: cosine_with_warmup
  t_warmup: 100ba
  alpha_f: 0.1

callbacks:
  speed_monitor:
    window_size: 10
  lr_monitor: {}

loggers:
  wandb:
    project: my-project
```

## Tokenizer API notes

- Registered tokenizer `tiktoken` maps to `TiktokenTokenizerWrapper`.
- `TiktokenTokenizerWrapper` requires exactly one of `model_name` or `encoding_name`.
- Useful wrapper options include `add_bos_token`, `add_eos_token`, `use_default_system_prompt`, `unk_token`, `eos_token`, `bos_token`, `pad_token`, `errors`, and `chat_template`.
- `build_tokenizer` requires the final tokenizer to have an `eos_token`; BERT-style tokenizers without EOS fail fast.

## Metrics, loggers, callbacks, optimizers

- Default causal LM train metrics are `language_cross_entropy`, `language_perplexity`, and `token_accuracy`.
- Default causal LM eval metrics add ICL LM/MC/QA metrics.
- Encoder-decoder metrics are `language_cross_entropy` and `masked_accuracy`.
- Logger keys map to Composer logger destinations. `inmemory` and `in_memory_logger` both map to in-memory logging; `wandb`, `tensorboard`, `mlflow`, and `mosaicml` require their runtime services/configs as appropriate.
- `DecoupledLionW` rejects non-positive learning rates, beta values outside `[0, 1]`, and warns for high weight decay.
