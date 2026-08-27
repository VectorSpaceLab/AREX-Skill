---
name: siammask
description: "Routes SiamMask visual object tracking, segmentation, benchmark
  evaluation, dataset preparation, and CUDA training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SiamMask Repo Skill

Use this skill when a task involves the SiamMask CVPR/TPAMI visual object tracking and segmentation codebase: running a demo, evaluating VOT/DAVIS/YouTube-VOS results, preparing benchmark or training data, or training SiamMask/SiamRPN checkpoints.

This skill is self-contained guidance plus bundled helpers. It assumes the user has or will provide a SiamMask checkout to operate on; pass that checkout to bundled scripts with `--repo-root <siammask-checkout>` instead of relying on this skill's construction checkout.

## Start Here

1. Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill matches a checkout or before refreshing it.
2. Read [references/install-and-setup.md](references/install-and-setup.md) before running any workflow; SiamMask is legacy PyTorch code and has important NumPy, CUDA, OpenCV, and Cython-extension constraints.
3. Run the read-only environment probe when you need to verify imports and backend readiness:

   ```bash
   python scripts/check_environment.py --repo-root <siammask-checkout> --expect-cuda auto --check-cli
   ```

4. Build checkout-local Cython extensions when tracking/evaluation imports fail on `region` or `_mask` modules:

   ```bash
   bash scripts/build_extensions.sh --repo-root <siammask-checkout> --python <python-in-your-env>
   ```

5. Pick the nearest sub-skill below for the user-facing task.

## Route Map

| Task signal | Read next | Why |
| --- | --- | --- |
| Run the OpenCV demo, track one sequence, generate VOT/DAVIS/YouTube-VOS benchmark outputs, evaluate VOT result folders, or tune tracking hyperparameters | [sub-skills/tracking/SKILL.md](sub-skills/tracking/SKILL.md) | Covers inference-time model/config/checkpoint selection, `mask`/`refine` behavior, benchmark result layout, and dry-run-first launch helpers. |
| Train SiamMask base, train the refine/sharp model, train the unofficial SiamRPN/ResNet baseline, resume checkpoints, inspect experiment configs, or plan GPU/batch-size usage | [sub-skills/training/SKILL.md](sub-skills/training/SKILL.md) | Covers CUDA-only training scripts, dataset JSON/crop requirements, ResNet pretraining, snapshots, TensorBoard logs, and launch command composition. |
| Download or validate VOT/DAVIS/YouTube-VOS/COCO/DET/VID data, build COCO pycocotools, crop `crop511` training data, generate dataset JSON indexes, or debug missing data paths | [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md) | Covers raw-data sources, expected directory layouts, preprocessing order, read-only layout checks, and VOT metadata generation. |

## Repo-Wide Facts to Keep in Mind

- SiamMask is not packaged with `setup.py` or `pyproject.toml`. Its Python entry points expect the checkout root on `PYTHONPATH`; bundled helpers add this automatically.
- The official README tested Ubuntu 16.04, Python 3.6, PyTorch 0.4.1, CUDA 9.2, and RTX 2080-era GPUs. Modern environments can import the code, but keep NumPy below 1.24 unless you patch legacy `np.float`/`np.int` aliases.
- Tracking and VOT evaluation can be CPU-capable, although slow. Training scripts and the VOS tuning script call CUDA APIs unconditionally and require a CUDA-capable PyTorch environment.
- Interactive demo mode uses OpenCV GUI ROI selection. Headless machines should use benchmark/test wrappers or non-interactive validation instead.
- Checkpoint files and full datasets are not bundled. Treat downloads as user-authorized network/data acquisition steps and validate paths before starting long runs.
- Read [references/model-overview.md](references/model-overview.md) when choosing between SiamMask base, SiamMask refine/sharp, and SiamRPN experiment families.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/backend failures.

## Avoid Using This Skill When

- The task is about a different tracker family or a general OpenCV/PyTorch issue with no SiamMask-specific code, config, checkpoint, or dataset signal.
- The user asks for paper-level distillation rather than operating this repository.
- The user needs to import/export DisCo skills; that is handled by repo-skill management workflows, not this operating skill.
