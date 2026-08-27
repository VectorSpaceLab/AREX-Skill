# Optimizer Reference

## Custom Optimizer Names

The inspected LMFlow install exposes these custom optimizer names through `OptimizerNames`:

- `dummy`
- `adabelief`
- `adabound`
- `lars`
- `lamb`
- `adamax`
- `nadam`
- `radam`
- `adamp`
- `sgdp`
- `yogi`
- `sophia`
- `adan`
- `adam`
- `novograd`
- `adadelta`
- `adagrad`
- `muon`
- `adamw_schedule_free`
- `sgd_schedule_free`

## When To Use Them

- Use `adam` or the default optimizer family when the user does not need a special optimizer.
- Use `adabelief`, `lamb`, `lars`, or `adamw_schedule_free` only when the user has a known reason.
- Use `dummy` only for tutorial-style or diagnostic cases.
- Use `sgdp`, `yogi`, `sophia`, `adan`, or `muon` when the user explicitly asks for those variants.

## Training Memory Notes

- LoRA and QLoRA are the first places to look when memory is tight.
- QLoRA depends on bitsandbytes-style quantization support.
- LISA trades layer activation for memory.
- Full fine-tuning consumes the most memory and needs the clearest hardware explanation.

## Useful Combinations

- `LoRA + cosine schedule + bf16` is a common strong baseline.
- `QLoRA + 4-bit quantization + LoRA adapters` is the tight-memory path.
- `LISA + conversation template` is useful when the user wants a memory-efficient adaptation strategy.
