---
name: foolbox
description: "Foolbox operating guidance for wrapping vision models, running
  adversarial attacks, measuring clean and robust accuracy, handling
  NumPy/PyTorch/TensorFlow/JAX backends, and loading Foolbox-compatible
  model-zoo repositories."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Foolbox

Foolbox 3.3.4 is an EagerPy-based library for generating and evaluating
adversarial examples against image classifiers. Use this skill when a task
mentions Foolbox, `foolbox`, adversarial examples, robust accuracy, attack
budgets, `LinfPGD`/FGSM/DeepFool/BoundaryAttack, model wrappers, or Foolbox
model-zoo repositories.

## Command, cache, and output paths

The commands in this skill use the generated skill root, not the native Foolbox
checkout and not the caller's current directory. From any cwd, set the root to
the directory containing this `SKILL.md` and change into it before running a
command that uses a relative skill path:

```bash
# Replace this non-executable placeholder with the absolute directory containing this SKILL.md.
export SKILL_ROOT=/path/to/installed/skills/disco/foolbox
cd "$SKILL_ROOT"
```

Use the actual installed skill-root path if it differs from the example above.
The root `scripts/` and `sub-skills/` paths below are relative to `SKILL_ROOT`;
an absolute path such as `python "$SKILL_ROOT/scripts/smoke.py"` is equivalent.
Write generated plots and other artifacts only to an explicit absolute path or
to a dedicated directory such as `"$SKILL_ROOT/outputs/"` (create it first);
do not rely on an unspecified cwd and do not write into the native checkout or
the skill's source/reference assets. Foolbox model-zoo clones and downloaded
weights use Foolbox's own cache (typically under `~/.foolbox_zoo`), not these
relative paths; inspect the exact returned path and never delete the whole cache
as cleanup.

Cloning a zoo repository or downloading/extracting weights is a networked,
potentially untrusted external-state operation. Obtain explicit approval before
calling `zoo.get_model(...)` or `zoo.fetch_weights(...)`, even when a cache entry
may already exist. The local zoo checker and bundled sample assets are the
offline alternatives.

## Install and verify

Install the package and the small helper dependencies only with the environment's
package-install/network approval; otherwise use an existing environment:

```bash
cd "$SKILL_ROOT"
python -m pip install foolbox pillow matplotlib
python -c "import foolbox as fb; print(fb.__version__)"
```

PyTorch, TensorFlow, and JAX are deliberately not base dependencies. Install
one separately using its own supported wheel/build when the selected model or
gradient attack needs it. Run the bundled CPU-native check before a larger
workflow:

```bash
cd "$SKILL_ROOT"
python scripts/smoke.py --help
python scripts/smoke.py
```

Read [`references/api-reference.md`](references/api-reference.md) for the
verified public signatures and output-shape rules. Read
[`references/troubleshooting.md`](references/troubleshooting.md) when imports,
bounds, preprocessing, optional frameworks, or attack outputs fail.

## Route by task

- **Wrap a model, prepare sample images, transform bounds, compute accuracy, or
  plot results:** read [`sub-skills/models/SKILL.md`](sub-skills/models/SKILL.md).
- **Choose or run attacks, compare robust accuracy, use criteria/distances,
  compose EOT or DatasetAttack, or author a new attack:** read
  [`sub-skills/attacks/SKILL.md`](sub-skills/attacks/SKILL.md).
- **Load a local/remote Foolbox model repository or fetch weights:** read
  [`sub-skills/zoo/SKILL.md`](sub-skills/zoo/SKILL.md).

## Core execution contract

1. Make the model callable through the matching Foolbox wrapper and state its
   input bounds before attacking. Include preprocessing and data format when
   they are not already native to the model.
2. Keep images and labels batched. Labels are a 1-D integer tensor aligned with
   the first dimension of model outputs.
3. Choose an untargeted label criterion (`labels` passed directly) or an
   explicit `TargetedMisclassification(target_classes)` criterion.
4. Call an attack with `epsilons=<float>`, `epsilons=<sequence>`, or `None` only
   when that attack supports minimization without a fixed budget.
5. Interpret `(raw, clipped, success)`: clipped results obey the requested
   distance budget; `success` is a boolean mask of actual adversarial examples.
   For a sequence of epsilons, raw/clipped are lists and success has shape
   `(K, N)`; for one scalar, outputs are tensors and success has shape `(N,)`.
6. Report clean accuracy, attack family, distance, epsilon(s), backend, and
   robust accuracy (`1 - success.float32().mean(axis=-1)`) together.

## Scope and limitations

The CPU/NumPy route and black-box/noise attacks are covered by the local smoke
and native verification plan. Framework gradient attacks, EOT over stochastic
models, and pretrained example models remain backend- and often network-
dependent; do not claim them verified merely because `import foolbox` works.
The model-zoo route can clone repositories or download weights and must be
explicitly approved before network or external-state operations.

## Provenance

Before using version-sensitive behavior or refreshing this skill, read
[`references/repo-provenance.md`](references/repo-provenance.md).
