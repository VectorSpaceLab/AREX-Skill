---
name: mmsegmentation
description: "Use MMSegmentation for semantic segmentation configs, datasets,
  inference, training, evaluation, model customization, registries, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMSegmentation

Use this repo skill when a task involves OpenMMLab MMSegmentation: semantic segmentation or depth configs, model zoo recipes, datasets and transforms, inference, training/testing, metrics, custom models, registries, checkpoints, or OpenMMLab dependency errors.

## Start Here

1. Confirm the installed package imports:

   ```bash
   python -c "import mmseg, mmcv, mmengine; print(mmseg.__version__, mmcv.__version__, mmengine.__version__)"
   ```

2. Read [install-and-compatibility](references/install-and-compatibility.md) if the task touches setup, dependency pins, CPU/CUDA, `mmcv`, `torch`, `numpy`, OpenCV, or optional project dependencies.
3. Run [check_mmseg_env.py](scripts/check_mmseg_env.py) for a deterministic import/version/backend check before blaming user code.
4. Route to the focused sub-skill below.

## Route By Task

- **Inference and visualization**: read [inference](sub-skills/inference/SKILL.md) for `MMSegInferencer`, `init_model`, image/video/batch inference, `SegDataSample`, headless output, saved masks, remote-sensing tiled inference, and deployment caveats.
- **Configs, datasets, and transforms**: read [data-configuration](sub-skills/data-configuration/SKILL.md) for MMEngine config inheritance, `--cfg-options`, packaged config families, dataset layouts, `BaseSegDataset`, transforms, class palettes, and dataset-conversion patterns.
- **Training, testing, and metrics**: read [training-evaluation](sub-skills/training-evaluation/SKILL.md) for safe train/test command construction, `Runner.from_cfg`, resume vs fine-tune, `IoUMetric`, `DepthMetric`, TTA, output formatting, distributed launch, Slurm, and log analysis.
- **Models, registries, and checkpoints**: read [model-customization](sub-skills/model-customization/SKILL.md) for built-in components, custom backbones/heads/losses/metrics, `MODELS`/`METRICS`, `custom_imports`, project extensions, checkpoint conversion, FLOPs caveats, and registry debugging.

## Common Decisions

- Prefer adapting an existing model-zoo config over writing a full `model` dict from scratch.
- Prefer local config and checkpoint files for deterministic inference; model aliases can trigger checkpoint downloads.
- Treat training, testing, benchmarks, dataset conversion, checkpoint conversion, and distributed jobs as side-effectful; use bundled dry-run wrappers first and execute only after approval.
- Keep `default_scope = 'mmseg'` unless intentionally composing with another OpenMMLab package.
- Use CPU for inspection and small smoke checks; document CUDA/NPU/other backends as runtime choices that need matching `torch`/`mmcv` builds.

## Shared References

- [repo-provenance](references/repo-provenance.md) records the source snapshot and evidence baseline for refresh decisions.
- [repo-routing-metadata](references/repo-routing-metadata.json) is used by DisCo's managed router during import.
- [install-and-compatibility](references/install-and-compatibility.md) covers dependency and backend compatibility.
- [troubleshooting](references/troubleshooting.md) covers cross-cutting install/import/backend/config/data failures.

## Bundled Helpers

- `scripts/check_mmseg_env.py`: imports core modules, checks versions, optional CUDA visibility, and warns about common incompatible `numpy`/OpenCV/torch/MMCV combinations.
- Sub-skill helpers provide safe inference, config inspection, dataset layout checking, dry-run train/test commands, log analysis, and registry inspection.

## Do Not

- Do not tell future agents to run original checkout scripts or open original docs as part of this skill. Use the bundled references and scripts here.
- Do not launch long training, distributed jobs, benchmarks, downloads, or dataset conversion without user approval.
- Do not assume `mmcv-lite` can run all model/API paths; model components that use compiled ops may require full `mmcv` matched to `torch` and the backend.
- Do not treat random-weight inference or a no-checkpoint model build as meaningful segmentation output.
