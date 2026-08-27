# Optimum cross-cutting troubleshooting

Read this when a task fails before it clearly belongs to one sub-skill.

## Base install imports but a deeper module fails

Symptoms:

- `import optimum.version` works, but `from optimum.exporters.tasks import TasksManager` fails.
- `from optimum.utils.preprocessing.task_processors_manager import TaskProcessorsManager` fails.
- A partner package import such as `optimum.onnxruntime` or `optimum.intel` is missing.

Likely causes and recovery:

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named 'requests'` while importing exporter tasks | Exporter task utilities import `requests`; some base installs may not include it explicitly | Install `requests`, rerun the import, then use `sub-skills/exporters-and-cli/scripts/tasks_manager_probe.py` |
| `No module named 'torchvision'` or Pillow-related error from preprocessing imports | Image preprocessing processors require `torchvision`/Pillow | Install `torchvision` and Pillow for preprocessing workflows, or avoid importing task processors when the task is text-only and does not need them |
| Missing `datasets` for task processors or GPTQ dataset helpers | Dataset-backed processors/helpers are optional | Install `datasets` only when the user approves dataset dependencies and any network/cache needs |
| `No module named 'optimum.onnxruntime'`, `optimum.exporters.onnx`, or `optimum.intel` | Hardware/backend implementation lives in a partner distribution | Install the documented partner package (`optimum-onnx`, `optimum[onnxruntime]`, `optimum-intel[openvino]`, etc.) and rerun the relevant sub-skill probe |
| Base `optimum-cli` help shows only `export` and `env` | Partner CLI subcommands are registered only when partner packages are installed | Use `sub-skills/exporters-and-cli/` to diagnose registration and dependency boundaries |

## Optional backend claims

Do not treat a successful base import as proof of optional backend readiness.

- ONNX/ONNX Runtime/OpenVINO native checks need partner packages and often model cache or network access.
- GPTQ quantization needs `gptqmodel>=7.0.0`, usually `accelerate`, a compatible model/tokenizer, and GPU/backend resources for real quantization.
- FX tensor parallelism needs a compatible Python/torch stack, CUDA or the chosen backend, process-group setup, and enough devices for the requested world size.

Use the root install checker and sub-skill probes first:

```bash
python scripts/check_optimum_install.py --json
python sub-skills/exporters-and-cli/scripts/probe_optimum_cli.py --run-env --json
python sub-skills/gptq-quantization/scripts/gptq_availability_probe.py --json
python sub-skills/fx-graph-workflows/scripts/fx_transform_smoke.py --check-compose
```

## Network and cache boundaries

Many native Optimum examples/tests use Hugging Face Hub models. If the user did not authorize network or downloads:

1. Prefer bundled no-download smoke scripts.
2. Use `local_files_only=True` only when the needed model/config/tokenizer is already cached.
3. Explain that native exporter/pipeline/GPTQ validation is blocked by model/cache availability, not by the generated skill.
4. Avoid destructive cache cleanup unless the user explicitly asks.

## Version-sensitive surfaces

- `optimum.fx.parallelization` is advanced and version-sensitive. The repository's tensor-parallel CI uses Python 3.10 and CUDA containers. If an import fails on newer Python with a dataclass mutable-default error, use a Python stack matching the repository's tested workflow or refresh this skill after upstream code changes.
- Transformers 5 can deprecate or remove some task aliases. Use `TasksManager.get_all_tasks()` and `TasksManager.map_from_synonym(...)` instead of hard-coding task aliases.
- `ipex` accelerator routing is deprecated in `optimum.pipelines.pipeline`; prefer `ov` for OpenVINO.

## When to stop

Stop and ask for user approval before:

- Installing broad extras such as all partner packages, full test requirements, or GPU-specific packages that are outside the requested workflow.
- Running full export, pipeline inference, GPTQ quantization, distributed tensor-parallel tests, dataset processing, training, or benchmarks.
- Using credentials, Hub tokens, private model repositories, or paid/limited accelerators.
