---
name: rbm
description: "Routes legacy binary RBM examples, CD versus PCD decisions,
  binarized MNIST assumptions, and NumPy compatibility troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Unlicense
---

# RBM

Use this sub-skill for the repository's binary Restricted Boltzmann Machine examples: Contrastive Divergence and Persistent Contrastive Divergence.

## Route here when

- The user asks for a binary RBM, Bernoulli visible/hidden variables, CD, or PCD.
- The user asks how the RBM examples binarize MNIST or generate preview images.
- The user needs to diagnose `np.float`, TensorFlow MNIST-loader, or working-directory failures in the RBM examples.

## Route elsewhere when

- GAN variants: `../gan/SKILL.md`
- VAE variants: `../vae/SKILL.md`
- Helmholtz Machine wake-sleep: `../helmholtz-machine/SKILL.md`
- Shared catalog, provenance, and compatibility: `../../SKILL.md`

## Fast decisions

- Use CD when the user wants the canonical binary RBM baseline or does not mention persistent chains.
- Use PCD when the user asks for persistent sampling, persistent contrastive divergence, or model samples carried between updates.
- Treat both scripts as legacy NumPy training loops that still import the TensorFlow 1.x MNIST helper.
- Expect binarized MNIST (`> 0.5`) and preview image grids under a working-directory-local `out/` folder.

## Read next

- `references/workflows.md` for CD-vs-PCD behavior and data assumptions.
- `references/troubleshooting.md` for RBM-specific failures.
- `../../references/model-catalog.md` for the repo-wide source artifact catalog.
- `../../references/compatibility.md` for the shared legacy stack notes.
- `../../scripts/check_legacy_stack.py` before claiming an unchanged RBM example can execute.
