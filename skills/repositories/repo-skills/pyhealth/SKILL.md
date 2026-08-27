---
name: pyhealth
description: "Guides PyHealth 2.0 healthcare-AI workflows for clinical datasets,
  task construction, preprocessing, models, training, evaluation, medical-code
  mapping, and multimodal data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyHealth

Use this skill when a task involves the `pyhealth` Python package or a
healthcare-AI pipeline built from structured EHR, clinical text, medical codes,
images, signals, or multimodal samples. PyHealth 2.0 organizes work as:
**dataset → task → processor/sample → model → trainer → metrics**. Keep patient
identity out of train/validation/test overlap unless the experiment explicitly
requires another protocol.

## First route

1. Check the Python/package prerequisite and resource gates in
   [installation-and-environment](references/installation-and-environment.md).
2. Decide whether the request is primarily data preparation, task definition,
   model training, evaluation, or medical-code/text/multimodal work.
3. Read exactly one focused route first:
   - [data-pipelines](sub-skills/data-pipelines/SKILL.md) for dataset classes,
     schemas, processors, splits, loaders, and local fixtures.
   - [clinical-tasks](sub-skills/clinical-tasks/SKILL.md) for built-in tasks,
     labels, feature keys, and custom task classes.
   - [models-training](sub-skills/models-training/SKILL.md) for model selection,
     dataset contracts, `Trainer`, devices, checkpoints, and inference.
   - [evaluation-interpretability](sub-skills/evaluation-interpretability/SKILL.md)
     for metrics, calibration, prediction sets, and explanations.
   - [medical-code-text](sub-skills/medical-code-text/SKILL.md) for `InnerMap`,
     `CrossMap`, NLP, code/text/vision/audio/signal, and multimodal routes.
4. For a complete experiment, follow the links between routes rather than
   copying an old example verbatim. Several public examples target PyHealth
   1.x names; prefer the current APIs documented in the focused route.

## Minimal checks

After installing the package, verify the public import before accessing a
clinical dataset:

```bash
python -c "import pyhealth; print('PyHealth import ok')"
python -c "from pyhealth.datasets import SampleDataset, split_by_patient, get_dataloader; from pyhealth.trainer import Trainer; print('core API ok')"
```

The package metadata requires Python `>=3.12,<3.14`. Install the base package
with `pip install pyhealth`; use `pip install 'pyhealth[graph]'` for
PyTorch-Geometric paths and `pip install 'pyhealth[nlp]'` for NLP metrics and
fuzzy matching. Use a compatible PyTorch build for the requested device; a CPU
import does not prove CUDA behavior.

## Safety and evidence gates

Do not download MIMIC, eICU, OMOP, PhysioNet, MEDS, model-hub weights, mapping
caches, or NLTK corpora unless the user has supplied authorization, access, and
a bounded destination. Do not put PHI or credentials in generated fixtures.
Use synthetic/local fixtures for API and schema checks. Treat training,
benchmark, and notebook-scale examples as recipes until data size, runtime,
and device are explicitly bounded.

Read [troubleshooting](references/troubleshooting.md) for cross-cutting import,
optional-dependency, data-access, device, and legacy-example failures. Read
[repo-provenance](references/repo-provenance.md) before deciding whether this
skill matches a changed PyHealth checkout.
