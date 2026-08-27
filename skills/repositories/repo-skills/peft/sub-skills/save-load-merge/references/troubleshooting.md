# Save/Load/Merge Troubleshooting

## Loaded adapter gives bad or base-like outputs

Check in this order:

1. Confirm the adapter was loaded on the same base model family and revision used for training. `adapter_config.json` should contain `base_model_name_or_path`; if it is missing or wrong, load the known base explicitly.
2. Confirm the right task class was used. A causal-LM adapter should load on `AutoModelForCausalLM` or `AutoPeftModelForCausalLM`, not a bare encoder or sequence-classification class.
3. Confirm adapters are active: inspect `active_adapters`, `get_model_status()`, and `get_layer_status()`.
4. Confirm inference mode and dtype are appropriate. For adapter training or resumed training, pass `is_trainable=True` to `PeftModel.from_pretrained`.
5. Run a tiny fixed input through base, unmerged adapter, and merged model to ensure the adapter changes outputs before debugging generation settings.

## Missing or unavailable base model

PEFT adapter checkpoints do not contain base weights. If `base_model_name_or_path` is `null`, private, renamed, or unavailable:

- Ask for the original base model ID/path and revision.
- Load the base model explicitly and then call `PeftModel.from_pretrained(base_model, adapter_dir)`.
- If the base cannot be recovered, the adapter alone is not enough to reconstruct the full model.
- For future handoff, update documentation or model card metadata to identify the exact base model and tokenizer.

## Random embeddings after vocabulary extension

If training added tokens and then the loaded model behaves randomly for those tokens, the resized embeddings probably were not saved or were not recreated before loading.

Fix pattern:

```python
tokenizer.add_tokens(new_tokens)
base_model.resize_token_embeddings(len(tokenizer))
model = PeftModel.from_pretrained(base_model, adapter_dir)
```

For future saves:

- Use `save_embedding_layers=True` when calling `save_pretrained` if full embedding changes must travel with the adapter.
- Use `trainable_token_indices` for a small number of trained new token rows when using LoRA workflows that support it.
- Use `modules_to_save` for task heads or other non-adapter modules that were trained.

## Unexpected keyword argument while loading config

An error like `TypeError: LoraConfig.__init__() got an unexpected keyword argument ...` usually means the adapter was saved by a newer PEFT version than the installed runtime.

Best fix:

```bash
pip install -U peft
```

If upgrading is impossible, inspect `adapter_config.json` and remove only the unknown key after confirming it is not required for the adapter behavior. This is a compatibility workaround, not a preferred packaging strategy.

## Slow adapter loading

Adapter loading can be slow when many adapters or large adapter tensors are repeatedly initialized and overwritten.

Use:

```python
model = PeftModel.from_pretrained(base_model, adapter_dir, low_cpu_mem_usage=True)
model.load_adapter(other_adapter_dir, adapter_name="other", low_cpu_mem_usage=True)
```

For serving many compatible LoRA adapters, consider hotswapping instead of deleting and reloading adapters.

## Multiple adapters do not activate together

Symptoms include only one adapter affecting outputs or `set_adapter` appearing ignored.

- Use distinct `adapter_name` values when loading each adapter.
- Call `model.set_adapter("name")` for one active adapter or `model.set_adapter(["a", "b"])` for supported multi-adapter activation.
- For different adapter types, use `PeftMixedModel` and remember that mixed compositions are recreated by script, not saved as a single mixed checkpoint.
- Confirm the method supports the desired composition; incompatible tuner types should fail rather than silently combine.

## Merge fails or merged outputs differ

Common causes:

- The PEFT method does not support merging, or the specific variant/quantization setting blocks merge.
- The wrong adapter was active when `merge_and_unload` was called.
- Multiple adapters were active in an unsupported or order-sensitive configuration.
- The base model was quantized or sharded in a way that does not support weight updates.
- Vocabulary or embedding sizes differ between the base and adapter-trained model.

Mitigation:

```python
model.set_adapter("adapter_to_merge")
with torch.inference_mode():
    before = model(**inputs).logits
merged = model.merge_and_unload()
with torch.inference_mode():
    after = merged(**inputs).logits
```

Compare `before` and `after` on a small deterministic input before saving or uploading the merged model.

## Hotswap rejects an adapter

Hotswap requires compatible LoRA structure. The incoming adapter must use the same method and target the same layers or a subset of the layers already present. If ranks differ and the model is compiled, call `prepare_model_for_compiled_hotswap(model, target_rank=max_rank)` before `torch.compile`.

## Checkpoint inspector reports no weight file

`adapter_config.json` alone is not loadable. Re-save the adapter with `model.save_pretrained(...)` or recover the missing `adapter_model.safetensors`/`adapter_model.bin` from the training output. If both weight files exist, prefer safetensors and remove stale duplicates only after verifying which file is current.
