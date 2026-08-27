---
name: layers-and-models
description: "Use FLA layer, module, and Transformers model APIs for attention
  replacement, model construction, generation, training, and evaluation
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# FLA Layers and Models

Use this sub-skill when the task is about constructing or smoke-checking Flash Linear Attention (FLA) layers, fused modules, or Transformers-compatible causal language models.

## Route here for

- Replacing a standard token-mixing or self-attention block with an FLA layer from `fla.layers`, such as `GatedLinearAttention` or `KimiDeltaAttention`.
- Building a tiny or production FLA model with `transformers.AutoModelForCausalLM.from_config(...)` and config classes from `fla.models`.
- Understanding hybrid attention plans through a model config's `attn` field.
- Using fused modules such as `RMSNorm` or `FusedLinearCrossEntropyLoss` in model/loss code.
- Planning generation, training, or evaluation flows for FLA models while identifying network, dataset, checkpoint, and GPU requirements.

## Do not route here for

- Kernel implementation internals, backend dispatch, Triton/Gluon/TileLang/CUDA/NPU optimization, or operator benchmark loops.
- Full repository contribution readiness or PR packaging.
- Native test execution. This sub-skill only provides safe API smoke helpers and distilled runtime guidance.

## Minimal workflow

1. Read `references/api-reference.md` for import surfaces, verified signatures, config knobs, return shapes, and known constraints.
2. Read `references/model-workflows.md` for attention replacement, tiny `AutoModelForCausalLM.from_config` construction, hybrid attention plans, fused losses, generation, training, and evaluation recipes.
3. If something fails to import, instantiate, or generate, consult `references/troubleshooting.md` before changing code.
4. For a safe local sanity check that avoids downloads and native test suites, run from this sub-skill directory:

```bash
python scripts/smoke_layer_model.py --help
python scripts/smoke_layer_model.py --device cpu
```

Use `--device cuda --require-cuda` only when CUDA is intentionally part of the check.

## Import rule of thumb

Import config classes from `fla.models`, not from top-level `fla`:

```python
from fla.models import GLAConfig, KDAConfig
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_config(GLAConfig())
```

Top-level `fla` exports many layer/model classes when optional imports succeed, but it deliberately omits names ending in `Config`.
