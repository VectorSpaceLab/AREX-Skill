---
name: metrics
description: "Prepare and route safe ALAE FID, reconstruction FID, PPL, and
  LPIPS metric workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# ALAE metrics

Use this sub-skill when a user asks how to evaluate ALAE/StyleALAE with FID, reconstruction FID, PPL, or LPIPS, or when they need to decide whether a legacy metric run is ready, too expensive, or blocked by dependencies.

## Routing contract

- Use `references/metrics-workflows.md` for commands, required artifacts, metric outputs, sample-count costs, and config caveats.
- Use `references/troubleshooting.md` for TensorFlow/dnnlib, metric pickle, CUDA/cuDNN, checkpoint, TFRecord, and stale-script failures.
- Run `scripts/check_metrics_stack.py` before recommending a native metric run. The checker is safe: it does not import `metrics/*.py`, does not download files, and does not run evaluation.
- Route TFRecord creation, raw dataset conversion, and sample-image layout questions to `../data-preparation/SKILL.md`.
- Route checkpoint download, pretrained artifact readiness, generation, reconstruction, or style-mixing asset questions to `../generation/SKILL.md` or the root setup guidance.
- Route training launch, checkpoint semantics, or architecture/checkpoint compatibility questions to `../training/SKILL.md`.

## Non-negotiable safety notes

- Do not import `metrics/fid.py`, `metrics/fid_rec.py`, `metrics/ppl.py`, or `metrics/lpips.py` merely to inspect them. Their top-level module code initializes the legacy TensorFlow/dnnlib stack and calls a metric pickle download helper.
- Treat metrics as optional legacy workflows. The inspected environment proved TensorFlow 1.15-style APIs and `dnnlib.tflib` imports, but TensorFlow GPU libraries for the old CUDA/cuDNN stack were missing or unverified.
- Do not run bundled full metric evaluations. Native metric scripts process 10k to 50k samples and require explicit user approval, local data, checkpoints, metric pickle files, CUDA, and the legacy TensorFlow/dnnlib stack.
- Do not route `metrics/fid_sep.py` as executable. It depends on the absent separate-model implementation and a missing separate-model default config.

## Default operating sequence

1. Confirm the user has a checkout root and intends to run an expensive optional metric, not just inspect readiness.
2. From the ALAE repository root, ensure `PYTHONPATH` includes the checkout root before running native repository scripts.
3. From this sub-skill directory (or by using the generated skill's script path), run the safe stack checker with an explicit config name or path, for example `python scripts/check_metrics_stack.py --repo-root <ALAE-checkout> --config ffhq`.
4. If the checker reports missing TensorFlow 1.x APIs, `dnnlib`, metric pickle files, a checkpoint pointer, CUDA visibility, or required TFRecords, resolve those first through the routed sub-skills.
5. Only then present the native metric command and its expected output file or stdout result from `references/metrics-workflows.md`.
