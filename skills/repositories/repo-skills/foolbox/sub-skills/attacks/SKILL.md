---
name: attacks
description: "Foolbox adversarial-attack guidance for selecting fixed-epsilon,
  minimization, gradient, decision-based, score-based, stochastic, spatial,
  dataset, EOT, and custom attack workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Foolbox attacks

Use this route when the task is to generate adversarial examples, compare
robust accuracy, choose an attack by threat model, configure criteria or
distances, or implement a new attack. Read
[`references/attack-overview.md`](references/attack-overview.md) to choose a
family, [`references/api-reference.md`](references/api-reference.md) for call
semantics, and [`references/workflows.md`](references/workflows.md) for recipes.
## Command path

The `scripts/` path below is relative to the generated Foolbox skill root, not
to a native Foolbox checkout and not to the caller's current directory. From
any cwd, use the directory containing the root `SKILL.md`:

```bash
# Replace this non-executable placeholder with the absolute directory containing the root SKILL.md.
export SKILL_ROOT=/path/to/installed/skills/disco/foolbox
cd "$SKILL_ROOT"
```

Use the actual skill-root path when it differs from this installation. Keep
plots and other generated artifacts in an explicit absolute output directory or
`"$SKILL_ROOT/outputs/"`; never rely on a plot filename resolving to the native
checkout or overwrite files under `references/` or `scripts/`.


## Run an attack safely

1. Wrap the model through the [`models` route](../models/SKILL.md), check clean
   accuracy, and ensure inputs lie inside the declared bounds.
2. Choose untargeted labels or a `TargetedMisclassification` criterion. Confirm
   the concrete attack supports that criterion.
3. Instantiate the attack with explicit steps for expensive or stochastic
   methods. Use `epsilons` as a scalar for one budget or a sequence to compare
   budgets in one call.
4. Use `clipped` outputs for visualizing or measuring budgeted adversarials; use
   `success` to calculate attack success and robust accuracy.
5. Report backend, attack class, distance, epsilon(s), steps, clean accuracy,
   and stochastic/repeat policy. Never compare attack results without stating
   whether the model and data preprocessing are identical.

Run the helper below for a safe NumPy noise plus DatasetAttack check. Framework
gradient attacks require an installed framework and are not proved by the CPU
smoke.

```bash
cd "$SKILL_ROOT"
python sub-skills/attacks/scripts/smoke_attacks.py --help
python sub-skills/attacks/scripts/smoke_attacks.py
```

The helper is also linked at [`scripts/smoke_attacks.py`](scripts/smoke_attacks.py).

## Select by threat model

- **Fast white-box:** `FGSM`/`FGM`, `LinfPGD`, `L2PGD`, basic iterative, momentum,
  Adam-PGD; requires differentiable framework tensors.
- **Minimization:** Carlini-Wagner, EAD, DeepFool, NewtonFool, contrast, blur,
  BoundaryAttack; choose when the perturbation should be minimized or when the
  attack owns an early-stop distance.
- **Decision/score/black-box:** additive/repeated noise, HopSkipJump,
  BoundaryAttack, Brendel-Bethge, Pointwise, DatasetAttack; use when gradients
  or probabilities are unavailable.
- **Special geometry:** `SpatialAttack` searches rotations/translations and has
  no normal epsilon argument; it expects 4-D image batches.
- **Randomized models:** wrap the model with EOT before a compatible gradient
  attack; EOT averages repeated model outputs and may be expensive.

Use [`references/troubleshooting.md`](references/troubleshooting.md) for
unsupported criteria, missing distances, invalid epsilons, bounds, channel
axes, and optional-backend failures. For authoring, read
[`references/attack-authoring.md`](references/attack-authoring.md).
