---
name: helmholtz-machine
description: "Routes the legacy binary Helmholtz Machine wake-sleep example,
  MNIST assumptions, output behavior, and NumPy compatibility troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Unlicense
---

# Helmholtz Machine

Use this sub-skill for the repository's single one-layer binary Helmholtz Machine example trained with the wake-sleep algorithm.

## Route here when

- The user asks how the wake-sleep example works.
- The user asks about recognition weights, generative weights, binary hidden units, binarized MNIST, or generated `H`/`V` image grids.
- The user needs to diagnose `np.float`, TensorFlow MNIST-loader, or working-directory failures in the Helmholtz Machine example.

## Route elsewhere when

- GAN variants: `../gan/SKILL.md`
- VAE variants: `../vae/SKILL.md`
- Binary RBM CD/PCD: `../rbm/SKILL.md`
- Shared catalog, provenance, and compatibility: `../../SKILL.md`

## Fast decisions

- This sub-skill owns only the binary wake-sleep example.
- The learning loop is NumPy after MNIST loading; TensorFlow is used only for the legacy loader.
- The example is useful for explaining wake-sleep intuition, not for modern production modeling.
- Preview image grids are written under a working-directory-local `out/` folder in source checkouts.

## Read next

- `references/workflows.md` for the wake/sleep phase breakdown.
- `references/troubleshooting.md` for Helmholtz-specific failures.
- `../../references/model-catalog.md` for the repo-wide source artifact catalog.
- `../../references/compatibility.md` for the shared legacy stack notes.
- `../../scripts/check_legacy_stack.py` before claiming the unchanged example can execute.
