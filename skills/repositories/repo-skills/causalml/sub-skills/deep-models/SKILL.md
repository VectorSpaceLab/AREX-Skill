---
name: deep-models
description: "Operate CausalML optional deep neural estimators: DragonNet and
  CEVAE across TensorFlow, Torch/Pyro, and JAX backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# deep-models

Use this sub-skill for CausalML 0.17.0 workflows that need optional neural causal estimators:

- TensorFlow `causalml.inference.tf.DragonNet`
- Torch/Pyro `causalml.inference.torch.CEVAE`
- JAX `causalml.inference.jax.DragonNet`
- JAX `causalml.inference.jax.CEVAE`

Prefer keyword arguments (`X=`, `treatment=`, `y=`) for all `fit` and `fit_predict` calls. The current neural-estimator order is `X, treatment, y, p`; using keywords avoids argument-order migration warnings and makes the treatment/outcome roles explicit.

## Route here when

- The user asks for DragonNet, CEVAE, neural causal estimators, hidden-confounder CEVAE, or optional `tf`, `torch`, or `jax` backends.
- The user needs tiny CPU examples for backend smoke checks before running larger experiments.
- The user asks how to save/load TensorFlow or JAX DragonNet checkpoints, or JAX CEVAE checkpoints.
- The user sees optional-backend import errors, CUDA warnings, Pyro/JAX runtime issues, or shape errors in neural CATE estimation.

For non-neural meta-learners, TMLE, IV/DRIV, or serialization helpers, use [`../causal-estimation/SKILL.md`](../causal-estimation/SKILL.md). For AUUC/Qini/cumulative-gain scoring and decision optimization after producing ITE/CATE predictions, use [`../analysis-and-decision/SKILL.md`](../analysis-and-decision/SKILL.md).

## Reference map

- [`references/backend-setup.md`](references/backend-setup.md): extras, imports, CPU/GPU expectations, and backend smoke checks.
- [`references/dragonnet.md`](references/dragonnet.md): TensorFlow and JAX DragonNet API recipes, outputs, and save/load.
- [`references/cevae.md`](references/cevae.md): Torch/Pyro and JAX CEVAE API recipes, tiny settings, and checkpoint differences.
- [`references/troubleshooting.md`](references/troubleshooting.md): common import, runtime, training, shape, and checkpoint failures.

## Minimal operating sequence

1. Choose the backend and install the matching optional extra; do not assume one deep backend implies the others are installed.
2. Build numeric `X` with shape `(n_samples, n_features)`, binary `treatment` with shape `(n_samples,)`, and numeric `y` with shape `(n_samples,)`.
3. Start with a tiny CPU configuration to prove imports, shapes, and method availability.
4. Fit with keyword arguments and inspect only finite ITE/propensity outputs before using metrics or policy decisions.
5. Save only where the wrapper supports it: TensorFlow DragonNet, JAX DragonNet, and JAX CEVAE. Torch/Pyro CEVAE exposes no CausalML `save`/`load` wrapper.
