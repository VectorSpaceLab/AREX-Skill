---
name: modelscope
description: "Use ModelScope SDK workflows for Hub access, pipelines, datasets,
  training, serving, export, customization, and repository contribution without
  relying on a source checkout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ModelScope Repo Skill

Use this skill when a task names ModelScope or needs a Python SDK for Model-as-a-Service workflows: Hub downloads and cache management, model inference pipelines, dataset/config loading, training/evaluation planning, serving/export utilities, custom pipeline extension, or focused repository-development guidance.

This skill is self-contained for future Researcher use. It distills package behavior, safe command shapes, helper scripts, and troubleshooting notes; do not reopen the original source checkout for routine use.

## Install and quick check

Choose the smallest extra set for the task:

```bash
pip install modelscope
pip install 'modelscope[framework]'
pip install 'modelscope[server]'
```

Domain extras such as `cv`, `nlp`, `audio`, `multi-modal`, and `science` can be large and backend-specific. Install them only when the selected model/task requires them. For CPU-only planning, pass `device='cpu'` to `pipeline(...)` and use local/offline smoke checks first.

Run the bundled environment checker after installation:

```bash
python scripts/check_modelscope_environment.py --summary
```

The checker imports public modules, reports package versions, verifies CLI help when available, and can optionally probe torch/CUDA. It does not download models, contact the Hub, start a server, train, or mutate files.

## Route by user request

| User intent | Read |
| --- | --- |
| Download or upload Hub repositories/files, inspect/cache/clear ModelScope cache, authenticate, set endpoint/cache variables, plan offline downloads, or use `modelscope`/`ms` CLI. | [hub-and-cli](sub-skills/hub-and-cli/SKILL.md) |
| Build inference with `pipeline(...)`, load `Model.from_pretrained(...)`, inspect task/output keys, use local model configs, debug registries, devices, batching, plugins, or `trust_remote_code`. | [pipelines-and-models](sub-skills/pipelines-and-models/SKILL.md) |
| Load local/HF/ModelScope datasets, validate dataset recipes, use JSON/YAML file IO, parse/merge `Config`, or handle `.py` config trust gates. | [datasets-config](sub-skills/datasets-config/SKILL.md) |
| Plan fine-tuning/evaluation, convert `TrainingArgs` flags to config, use `build_trainer`, choose checkpoint/hooks/metrics, or preflight model/data/GPU requirements. | [training-and-evaluation](sub-skills/training-and-evaluation/SKILL.md) |
| Launch ModelScope server, choose vLLM handoff, inspect exporter support, or dry-run checkpoint conversion/weight-diff utility side effects. | [serving-export-and-tools](sub-skills/serving-export-and-tools/SKILL.md) |
| Create custom pipeline/model/preprocessor wrappers, scaffold template commands, register components, understand plugins/lazy imports, or contribute to ModelScope source. | [customization-and-development](sub-skills/customization-and-development/SKILL.md) |

## Repo-level references

- Read [package overview](references/package-overview.md) for package surfaces, optional extras, public entry points, and environment choices.
- Read [troubleshooting](references/troubleshooting.md) for install/import, optional dependency, backend, cache, trust, and workflow-selection failures that cut across sub-skills.
- Read [repository provenance](references/repo-provenance.md) before deciding whether this skill is stale for a newer checkout.
- `references/repo-routing-metadata.json` is structured router metadata for managed repo-skill import; it is not a user manual.

## Operating guardrails

1. ModelScope can download models/datasets and run remote-code/plugin paths. Confirm trust, credentials, endpoint, cache root, and network policy before executing Hub/model-loading commands.
2. Many domain examples require large model/data downloads, GPU memory, optional extras, or credentials. This skill verifies package-level CPU/base workflows; CUDA/domain execution is optional and must be verified in the target environment before claiming success.
3. Prefer dry-run planners and safe helper scripts before side-effecting commands: `hub-and-cli/scripts/plan_download.py`, `training-and-evaluation/scripts/build_training_args_preview.py`, `serving-export-and-tools/scripts/checkpoint_conversion_plan.py`, and `customization-and-development/scripts/pipeline_template_plan.py`.
4. Do not treat `trust_remote_code=True`, Python configs, plugins, uploads, cache clears, real training, server launch, or checkpoint conversion as harmless. Require explicit user approval or a clear task mandate.
5. When a workflow spans multiple surfaces, route in order: Hub/cache → dataset/config → pipeline/training/serving → troubleshooting.

## Minimal API memory

```python
from modelscope.pipelines import pipeline
from modelscope.msdatasets import MsDataset
from modelscope.trainers import build_trainer
from modelscope.hub.snapshot_download import snapshot_download

model_dir = snapshot_download('owner/model', local_files_only=True)
pipe = pipeline(task='text-classification', model=model_dir, device='cpu')
# dataset = MsDataset.load('csv', data_files={'train': 'train.csv'}, split='train')
# trainer = build_trainer(name='trainer', default_args={'model': model_dir})
```

The exact task, model, dataset, trainer name, extras, and backend requirements come from the selected sub-skill and user context.
