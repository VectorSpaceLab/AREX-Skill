# Specialized Tuner Troubleshooting

## Target modules are not found

Symptoms include errors that no target modules were found, no compatible layer types were found, or adapter injection leaves no trainable parameters.

Checklist:

1. Print base model module names with `for name, _ in model.named_modules(): print(name)` on a small instance.
2. Use suffixes that match the architecture, such as `q_proj`/`v_proj` for many decoder-only models, `q`/`v`/`wi`/`o` for some encoder-decoder models, or `c_attn`/`c_proj` for GPT-style modules.
3. For IA3, include both attention targets and feed-forward targets when the method needs them.
4. For layer-restricted configs, avoid combining regex `target_modules` with `layers_to_transform` if the config rejects that combination.
5. For custom linear subclasses, first test with a standard `torch.nn.Linear`-backed toy model to separate PEFT configuration issues from unsupported layer classes.

## IA3 feedforward validation fails

`IA3Config` requires `feedforward_modules` to be a subset of `target_modules` when both are concrete lists/sets. Fix by adding the feed-forward module to `target_modules` or removing it from `feedforward_modules`.

Example:

```python
IA3Config(target_modules=["q_proj", "v_proj", "fc2"], feedforward_modules=["fc2"])
```

## Projection checkpoints are not reproducible

VeRA, PVeRA, RandLoRA, TinyLoRA, and similar random-projection methods can save small checkpoints by omitting projection matrices and regenerating them from a seed/key. This is storage-efficient but may not be exactly reproducible across all devices or future PyTorch versions. Use `save_projection=True` for training continuation, audits, or reproducibility-sensitive releases.

## VBLoRA checkpoint cannot resume training

If a `VBLoRAConfig` saved only top-k weights/indices, the checkpoint is intended for merge or inference. To resume training, save all trainable logits instead of only top-k weights.

## Mixed adapter batches do not work

Do not assume every specialized tuner supports per-sample `adapter_names` routing. Prefer methods registered as mixed-compatible, such as IA3, LoHa, LoKr, RoAd, HiRA, or BEFT in this PEFT version. For other tuners, ordinary multiple-adapter load/set operations may work while mixed-batch routing still does not.

If weighted adapter composition fails:

- Keep target-module declarations the same type across adapters; do not mix regex strings and lists.
- Avoid conflicting `modules_to_save` entries across adapters.
- For IA3, keep `feedforward_modules` declaration types consistent across adapters.
- Validate adapter outputs one adapter at a time before testing a mixed batch.

## XLora setup fails

XLora is a LoRA-expert router. It requires compatible LoRA adapters and should not be configured as a standalone non-LoRA tuner. Validate each LoRA expert first, then create the XLora routing config. Route LoRA target selection, LoRA initialization, or quantized LoRA questions to the LoRA sub-skill.

## OSF does not preserve previous tasks

OSF is designed for continual learning with preserved and trainable subspaces. If forgetting remains high:

1. Recompute or re-wrap after each task so preserved directions match the latest weights.
2. Increase the preserved `effective_rank` or preserved fraction for later tasks.
3. Use consistent target modules across the task sequence.
4. Confirm that merge/unload semantics fit the planned sequential training loop; some OSF flows are not symmetric merge/unmerge workflows.

## Optional backend classes are missing

Some tuners expose optional backend-specific classes only when optional packages are installed, for example quantized linear backends. A normal PEFT install with PyTorch, Transformers, and Accelerate is enough for standard config introspection, but backend-specific layer replacement may require extra packages. Do not add broad optional dependencies unless the workflow needs that backend.

## Config class name mismatch

Common spelling/case traps:

- `BOFTConfig`, not `BoftConfig`.
- `IA3Config`, not `Ia3Config`.
- `VBLoRAConfig`, not `VbLoraConfig`.
- `XLoraConfig`, not `XLoRAConfig`.
- `LNTuningConfig`, not `LayerNormTuningConfig`.
- `PveraConfig`, `FrodConfig`, `HiraConfig`, `ShiraConfig`, `PsoftConfig`, `TinyLoraConfig`, and `AdamssConfig` use mixed casing that may differ from the method acronym.

Use `scripts/list_peft_methods.py --filter <name>` to confirm what the installed package exports.

## Unsupported task or model combination

When a method works on a toy model but fails on the real model:

1. Confirm the model class exposes the target module types the method wraps.
2. Set `task_type` explicitly so PEFT picks the correct task-specific wrapper.
3. Test a tiny compatible model from the same architecture family before scaling to the full checkpoint.
4. Use `print_trainable_parameters()` and inspect adapter module classes to verify injection.
5. If the method depends on LoRA experts, prompt learning, or quantization, route to the owning sub-skill and combine guidance only at integration time.
