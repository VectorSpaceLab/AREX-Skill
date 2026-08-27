---
name: core-lora-api
description: "Integrate loralib into PyTorch modules, select trainable adapter
  parameters, save or load LoRA-only checkpoints, and control merge behavior
  safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core loralib API

Use this sub-skill when the user wants to replace PyTorch layers with LoRA
counterparts, adapt a custom model, inspect trainable parameters, or serialize
only the low-rank update.

## Route here

- Replace `nn.Linear`, `nn.Embedding`, or a supported convolution with a LoRA
  layer.
- Use `MergedLinear` when one projection stores multiple logical projections,
  such as a fused QKV matrix.
- Freeze the base model, optionally train selected biases, and save adapter-only
  state.
- Diagnose missing `lora_A`/`lora_B` keys, wrong rank/scaling, or unexpected
  eval-time weight changes.

## Start fast

1. Install PyTorch, then `python -m pip install loralib`.
2. Import with `import loralib as lora` and replace only the modules that should
   receive a low-rank update.
3. Use a positive `r`, normally choose `lora_alpha` explicitly, and decide
   whether the module should merge its update during `eval()`.
4. Call `lora.mark_only_lora_as_trainable(model, bias="none")` before creating
   the optimizer. Use the same bias policy when calling `lora.lora_state_dict`.
5. Load the base checkpoint first, then load the adapter state with
   `strict=False`.

Run the shared smoke helper before changing a custom model. From this
sub-skill directory, use:

```bash
python ../../scripts/check_lora_core.py --json
```

## Layer choices

- `lora.Linear`: ordinary dense layers; set `fan_in_fan_out=True` when the
  stored weight uses transposed Conv1D-style layout.
- `lora.Embedding`: low-rank update to an embedding table. Its API has no
  dropout argument.
- `lora.MergedLinear`: fused projections; `enable_lora` selects which equal-
  width slices get adapters. The list length must divide `out_features`.
- `lora.Conv1d`, `lora.Conv2d`, `lora.Conv3d`: convolution wrappers. Keep
  `kernel_size` an integer for this repository implementation.

## Reroute

- GLUE model flags and RoBERTa/DeBERTa insertion points: use
  `../nlu-glue-adaptation/SKILL.md`.
- GPT-2 data conversion, beam search, and evaluation-file layout: use
  `../nlg-gpt2-adaptation/SKILL.md`.

## References

- Read [API reference](references/api-reference.md) for verified signatures,
  tensor shapes, parameter names, and bias policies.
- Read [integration workflows](references/workflows.md) for replacement,
  checkpoint, fused-QKV, and merge/unmerge recipes.
- Read [troubleshooting](references/troubleshooting.md) for import, optimizer,
  state-dict, and merge failures.

## Common request patterns

Use this sub-skill when the user asks to:

- replace a single dense layer with LoRA and verify only adapter parameters are
  trainable;
- integrate LoRA into a custom `nn.Module` and keep the base checkpoint format;
- merge or unmerge weights around `eval()` and `train()`;
- compare `lora_state_dict()` output for different `bias=` policies; or
- diagnose why a fused projection needs `MergedLinear` instead of two separate
  linear wrappers.

## Exit checklist

Before returning, confirm all of the following when they apply:

1. the layer rank and alpha are explicitly set;
2. the target module path is correct;
3. the base model has been frozen or filtered with
   `mark_only_lora_as_trainable`;
4. the adapter state is saved with `lora_state_dict`;
5. the load path uses `strict=False` for adapter-only checkpoints; and
6. the output explains whether `merge_weights` is enabled.
