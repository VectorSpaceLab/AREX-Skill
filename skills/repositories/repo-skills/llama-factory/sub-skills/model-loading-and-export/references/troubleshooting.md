# Troubleshooting

## Fast Triage

Ask these first:

- Is the user loading, training with adapters, exporting, quantizing, or converting checkpoints?
- Is the model local, Hugging Face Hub, ModelScope, or OpenMind/Modelers?
- Is `trust_remote_code` required and acceptable for the model source?
- Is the model already PTQ-quantized, being quantized on the fly with `quantization_bit`, or being quantized during export with `export_quantization_bit`?
- Are adapters being resumed, merged, or newly created?
- Is this an RM/value-head artifact or a normal causal/seq2seq/multimodal model?

## Tokenizer Load Failure

Typical symptoms:

- `OSError: Failed to load tokenizer.`
- SentencePiece/protobuf/tiktoken errors.
- Private/gated hub access errors.
- Remote-code tokenizer class not found.

Likely fixes:

- Set `trust_remote_code: true` only for trusted custom model repos.
- Check `model_name_or_path`, `model_revision`, and whether the local path has tokenizer files.
- Provide hub credentials through environment or secret handling, not committed config values.
- Clear or change `cache_dir` if a partial snapshot is suspected.
- Toggle `use_fast_tokenizer`; the loader already retries the opposite tokenizer implementation for `ValueError`, but dependency errors still need package fixes.
- Install tokenizer dependencies required by the model family, such as SentencePiece or protobuf, when the traceback names them.

## Processor Load Failure

The loader logs processor failures and continues with `processor: None`. This is acceptable for text-only flows but usually wrong for image, video, or audio models.

Fixes:

- Confirm the model repo includes processor/preprocessor files.
- Set `trust_remote_code: true` for trusted custom multimodal processors.
- Install model-specific processor dependencies.
- For multimodal data/template issues after loading succeeds, route to `data-and-templates`.

## Hub, Cache, Revision, and Mirror Problems

For hub access errors:

- Confirm whether the model is gated/private and whether access was granted.
- Use `hf_hub_token` only through safe secret injection when possible.
- Check `model_revision` for a valid branch/tag/commit.
- Try a fresh `cache_dir` if files are corrupt or mixed across revisions.
- Use `USE_MODELSCOPE_HUB=1` or `USE_OPENMIND_HUB=1` only when that mirror hosts the requested model and the user wants mirror routing.

Avoid hardcoding machine-specific cache or environment paths in reusable runtime guidance.

## Quantization Optional Dependencies

Map the failure to the backend:

- bitsandbytes: needed for `quantization_method: bnb` and `quantization_bit: 4` or `8`; 4-bit FSDP/auto device-map paths need newer bitsandbytes.
- GPTQModel/Optimum: needed for `export_quantization_bit` and GPTQ PTQ models.
- AutoAWQ: needed for AWQ PTQ models.
- AQLM: needed for AQLM PTQ models.
- HQQ: needed for `quantization_method: hqq`.
- EETQ: needed for `quantization_method: eetq`.
- FP8/MXFP4 model configs may need hardware- and package-specific stacks; identify the exact model quantization config before advising.

Do not suggest vLLM to fix export quantization. vLLM is an inference backend.

## Cannot Resize Quantized Vocab

Symptoms include embedding resize errors, dtype/device errors, or PEFT save gaps after adding tokens.

Rules:

- `resize_vocab: true` changes embedding layers and is safest before quantization.
- Quantized weights may not support resizing or may produce invalid quantized embedding states.
- For LoRA with new tokens, make sure embeddings are saved via `additional_target` or rely on LlamaFactory's automatic additional target warning path when applicable.
- Prefer preparing an unquantized merged/base checkpoint with the final tokenizer first, then quantize/export.

## Cannot Merge Quantized Model

Export and adapter code reject or restrict quantized merges:

- Export aborts when a loaded model is quantized and `adapter_name_or_path` is set: adapters cannot be merged into a quantized model.
- Export aborts when `adapter_name_or_path` and `export_quantization_bit` are both set: merge adapters first, then quantize in a second export.
- Adapter setup restricts quantized models to a single adapter in important paths and treats them as non-mergeable.

Recommended two-step plan:

1. Export/merge LoRA against the unquantized base model without `quantization_bit` or `export_quantization_bit`.
2. Run a second export from the merged output with `export_quantization_bit` and a calibration dataset.

## Adapter Restrictions

Common adapter failures:

- Multiple adapters with quantized model, DeepSpeed ZeRO-3, KTransformers, or Unsloth.
- DoRA with PTQ-quantized models other than bitsandbytes-style quantization.
- `lora_target` names not present after multimodal/projector filtering.
- Missing adapter subfolder when `adapter_folder` is set.
- `create_new_adapter` changes whether supplied adapters are merged or resumed.

Fixes:

- Reduce to one adapter when the backend requires it.
- Remove `quantization_bit` and use an unquantized base for merge/export.
- Use explicit target module names if `all` selects unsupported modules.
- Confirm adapter config `base_model_name_or_path` and model family match the requested base.

## Value-Head or Reward-Model Issues

If RM/PPO paths complain about missing value-head weights:

- Check whether the final adapter path or base model path contains LlamaFactory value-head files.
- RM export copies value-head weights only when present.
- Missing value-head logs can be harmless for non-value-head flows.
- Route PPO/RM training objective details to `training-and-configs`; keep this sub-skill focused on artifact loading/export.

## Transformers 5 Export Save Error

A `NotImplementedError` from `transformers.core_model_loading.reverse_op` during save can happen for some architectures under Transformers 5+ weight conversion reversal. Workarounds are to use a compatible Transformers version below 5 or report/follow the upstream architecture issue.

## Safe Preflight

Before an export or merge run:

```bash
python scripts/check_export_config.py CONFIG.yaml
```

Address `ERROR` findings first. `WARN` findings usually require user confirmation or environment checks.
