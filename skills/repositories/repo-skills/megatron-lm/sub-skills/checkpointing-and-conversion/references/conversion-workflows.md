# Conversion workflows

## Choose the conversion path

| Goal | Recommended path |
|---|---|
| Load a GPT checkpoint into a HybridModel run without writing a second copy | Use load-time GPT-to-Hybrid translation. |
| Produce a standalone HybridModel checkpoint | Use the offline GPT-Hybrid converter. |
| Convert HybridModel back to GPTModel | Use the offline converter only when the pattern is GPT-compatible. |
| Convert Hugging Face ↔ Megatron for model exchange | Use Megatron Bridge or a model-specific conversion example with explicit mounts/tokens/checkpoints. |

## Load-time GPT-to-Hybrid translation

Use this when the target training run can read the source GPT checkpoint directly. The run must set `--hybrid-layer-pattern` so GPT layers can be paired with Hybrid layer positions. This path can preserve optimizer state when the checkpoint format and optimizer state format support it.

Key choices:

- Use `--load` for full resume semantics.
- Use finetune semantics when iteration/scheduler/RNG should restart.
- Use `--no-load-optim` when optimizer state is incompatible or intentionally fresh.

## Offline GPT-Hybrid converter

The converter command shape:

```bash
python tools/checkpoint/gpt_hybrid_conversion.py \
  --direction gpt-to-hybrid \
  --load-dir <source-checkpoint-root> \
  --save-dir <target-checkpoint-root> \
  --hybrid-layer-pattern "*-*-" \
  --input-format auto \
  --output-format auto
```

The bundled `render_gpt_hybrid_conversion_command.py` validates basic arguments and prints a template.

## Hybrid layer pattern rules

Pattern symbols:

| Symbol | Layer family | GPT source mapping |
|---|---|---|
| `*` | Attention | Maps from GPT self-attention occurrence. |
| `-` | Dense MLP | Maps from GPT MLP occurrence. |
| `E` | MoE MLP | Maps from GPT MoE MLP when the source is uniformly MoE. |
| `M` | Mamba | No GPT source; initialized fresh in GPT-to-Hybrid paths that allow it. |
| `G` / `D` | GDN / DSA | Not supported by GPT-compatible conversion paths. |

Architecture-preserving examples:

- Dense GPT with N layers: repeat `*-` N times.
- All-layer MoE GPT with N layers: repeat `*E` N times when supported by the selected path.

The converter rejects patterns when attention and MLP-bearing positions cannot be paired with source GPT layers, when unsupported symbols appear, or when MTP suffixes have no source weights.

## Hugging Face / Megatron conversion

HF conversion is model-specific and often uses Megatron Bridge. Before running:

- Verify the model name and tokenizer source.
- Ensure HF cache, Megatron checkpoint directory, and output directory are mounted inside the execution environment.
- Confirm credentials such as HF tokens are available only to the command that needs them.
- Match process count to the target conversion script's distributed assumptions.

Do not embed credentials or private cache paths in generated commands.

## Validation after conversion

- Check the target checkpoint root/tracker layout.
- Run a weights-only load smoke before full resume.
- If optimizer state was translated, use a short run to confirm optimizer step succeeds.
- Verify model architecture flags match the checkpoint's expected layer pattern and dimensions.
