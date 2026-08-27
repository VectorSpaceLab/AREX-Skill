# PaLM Modeling Troubleshooting

## CPU Hosts And README `.cuda()` Calls

### Symptom
- A simple README-style snippet fails on a CPU-only machine because it calls `.cuda()` unconditionally.

### Cause
- The README example is written for a CUDA training environment.

### Recovery
- Move the model and tensors with `device = torch.device(...)` and `.to(device)` instead.
- Run `scripts/tiny_palm_smoke.py --device auto` to confirm the API on the current host.

## `flash_attn=True` Questions

### Symptom
- The attention path changes unexpectedly or a `flash_attn` run fails.

### Cause
- The package uses PyTorch scaled-dot-product attention, not a separate flash-attn wheel.
- PyTorch versions older than 2.0 do not support the `flash_attn=True` path.

### Recovery
- Set `flash_attn=False` first.
- Verify `torch.__version__` and rerun the smoke check.
- Compare outputs only after the basic CPU path is working.

## Generation Length Confusion

### Symptom
- The returned tensor is shorter than expected.

### Cause
- `PaLM.generate(seq_len, prompt=...)` counts the target total length, and the default return omits the prompt.

### Recovery
- If you want a suffix of length `k`, pass `seq_len = prompt_len + k`.
- If you want the full prompt-plus-generation tensor, set `return_seq_without_prompt=False`.

## LoRA Scope Collisions

### Symptom
- `add_finetune_params` or `finetune_parameters` raises an assertion.

### Cause
- Scope names must be unique and must exist before use.

### Recovery
- Add a fresh scope name.
- Remove or merge the existing scope intentionally.
- Keep base and finetune optimizers separate if that is your goal.

## Loss And Ignore Index Pitfalls

### Symptom
- Cross-entropy behaves strangely when token `0` appears in the labels.

### Cause
- The default `cross_entropy_ignore_index` is `0`.

### Recovery
- Choose a different ignore index if token `0` is a real label in your task.

## Save/Load Issues

### Symptom
- Loading a checkpoint fails because the file does not exist or the construction differs.

### Cause
- `load(path)` expects a real file and a compatible model shape.

### Recovery
- Save with `torch.save(palm.state_dict(), path)`.
- Recreate the same model shape and any required LoRA scopes before loading.

## When To Stop

Stop and ask for clarification if the user wants a full enwik8 training run, a pretrained checkpoint, or a new dependency install such as `lion-pytorch` that has not been approved.
