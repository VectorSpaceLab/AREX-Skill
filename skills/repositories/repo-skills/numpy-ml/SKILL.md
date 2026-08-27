---
name: numpy-ml
description: "Routes numpy-ml users to the right classical ML, preprocessing,
  neural-component, probabilistic, and RL workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# numpy-ml

`numpy-ml` is an educational machine-learning library implemented mostly in
NumPy and SciPy. Use this root skill to choose the right workflow, install a
compatible runtime, and confirm whether a task belongs to a focused sub-skill.

## Verified compatibility

This legacy snapshot was verified on Python 3.8 with:

```bash
python -m pip install "numpy<1.24" "scipy<1.11" numpy-ml
python -c "import numpy_ml; print('ok')"
```

Why this matters:

- Python 3.10+ fails on this commit because the package imports
  `collections.Hashable`.
- NumPy 1.24+ can break older code paths that use removed aliases such as
  `np.int` and `np.float`.
- Base runtime use does not require Gym, PyTorch, TensorFlow, or plotting
  libraries.

Read [`references/repo-provenance.md`](references/repo-provenance.md) when you
need to check whether this skill matches the current checkout or before running
`refresh-repo-skill`.

## Quick checks

Run the bundled environment check when you are unsure whether the current Python
can use the package:

```bash
python scripts/check_numpy_ml_environment.py
```

Run the cross-family smoke matrix when you want a fast confidence pass over the
bundled helpers:

```bash
python scripts/api_smoke_matrix.py
```

## Route map

| User intent | Read next |
| --- | --- |
| linear models, trees, KNN/GP regression, or matrix factorization | [`sub-skills/supervised-and-tabular-models/SKILL.md`](sub-skills/supervised-and-tabular-models/SKILL.md) |
| GMM, HMM, LDA, or n-gram language models | [`sub-skills/probabilistic-and-sequence-models/SKILL.md`](sub-skills/probabilistic-and-sequence-models/SKILL.md) |
| activations, layers, losses, optimizers, schedulers, or toy NN models | [`sub-skills/neural-network-components/SKILL.md`](sub-skills/neural-network-components/SKILL.md) |
| standardization, encoding, tokenization, DSP, kernels, distances, graphs, queues, or samplers | [`sub-skills/preprocessing-and-utilities/SKILL.md`](sub-skills/preprocessing-and-utilities/SKILL.md) |
| bandits, policy comparison, EnvModel, or optional Gym-backed RL agents | [`sub-skills/bandits-and-reinforcement-learning/SKILL.md`](sub-skills/bandits-and-reinforcement-learning/SKILL.md) |

## What to avoid

- Do not treat the repository's original comparison tests as runtime
  dependencies; they are optional diagnostics.
- Do not assume a fit method returns the model object. Many `numpy-ml` classes
  mutate in place and return `None`.
- Do not promise GPU support or modern autograd behavior; this library is a
  NumPy/SciPy reference implementation.

## Helper references

- [`references/api-overview.md`](references/api-overview.md) for the module map.
- [`references/compatibility.md`](references/compatibility.md) for version and
  dependency constraints.
- [`references/troubleshooting.md`](references/troubleshooting.md) for shared
  import and legacy-compatibility failures.

## Best-fit rule

Choose the smallest sub-skill that owns the user-facing workflow. If the task
starts with raw text, labels, signals, or feature dictionaries, route through
preprocessing first. If the task needs a bandit or RL loop, use the RL sub-skill
instead of the supervised one. If the task needs tensor-based deep learning or a
modern framework, this package is probably the wrong tool.
