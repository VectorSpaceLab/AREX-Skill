# Shared API Reference

Read this when a task spans more than one route or when you need a quick map of public Evaluate APIs before choosing a sub-skill.

## Package And Entry Points

| Surface | Purpose | Route |
| --- | --- | --- |
| `evaluate.load(path, config_name=None, module_type=None, process_id=0, num_process=1, cache_dir=None, experiment_id=None, keep_in_memory=False, download_config=None, download_mode=None, revision=None, **init_kwargs)` | Instantiate metrics, comparisons, measurements, local modules, and Hub/community modules. | `sub-skills/module-loading/` |
| `evaluate.list_evaluation_modules(module_type=None, include_community=True, with_details=False)` | Discover Hub-hosted evaluation modules. | `sub-skills/module-loading/` |
| `evaluate.inspect_evaluation_module(path, local_path, download_config=None, **download_kwargs)` | Copy a module script locally for review or modification. | `sub-skills/module-loading/` |
| `EvaluationModule.compute(*, predictions=None, references=None, **kwargs)` | Compute a module result. | `sub-skills/module-computation/` |
| `EvaluationModule.add(...)` / `add_batch(...)` | Accumulate examples or batches before `compute()`. | `sub-skills/module-computation/` |
| `evaluate.combine(evaluations, force_prefix=False)` | Run multiple modules over the same inputs. | `sub-skills/module-computation/` |
| `evaluate.save(path_or_file, **data)` | Save result dictionaries and metadata to JSON/CSV-compatible output. | `sub-skills/module-computation/` |
| `evaluate.evaluator(task=None)` | Build a task evaluator for model/pipeline + dataset evaluation. | `sub-skills/evaluator-pipelines/` |
| `EvaluationSuite` / `SubTask` | Group evaluator subtasks. | `sub-skills/evaluator-pipelines/` |
| `evaluate.push_to_hub(...)` | Update Hub model-card evaluation metadata. | `sub-skills/hub-and-cli/` |
| `evaluate-cli create ...` | Create a custom evaluation module Space from templates. | `sub-skills/hub-and-cli/` |

## Module Types

- `metric`: scores predictions against references or task-specific inputs, for example accuracy, BLEU, ROUGE, F1, or SQuAD metrics.
- `comparison`: compares model/system outputs, for example exact-match or statistical comparison modules.
- `measurement`: measures properties of data or generations, for example word counts, duplicates, toxicity, or perplexity.

Each loaded module exposes `info`, `name`, `description`, `citation`, `features`, `inputs_description`, `module_type`, and related metadata. Always inspect `features` and `inputs_description` before assuming the input names are `predictions` and `references`.

## Optional Extras And Dependencies

- Base install: `pip install evaluate` for loading and computing modules that only require core dependencies.
- Evaluator install: `pip install "evaluate[evaluator]"` for `transformers` and `scipy`; actual pipeline inference also needs a backend such as PyTorch, TensorFlow, or Flax.
- Template/CLI authoring: `evaluate-cli` imports `cookiecutter`; generated widgets may need Gradio.
- Module-specific requirements: many built-in modules have their own dependencies. Install the dependency named in the module card or requirements only for the module being used.
- Visualization: `evaluate.visualization.radar_plot(data, model_names, invert_range=[], config=None, fig=None)` requires `matplotlib`.

## Supported Evaluator Tasks

The evaluator registry includes these task names in this checkout: `text-classification`, `image-classification`, `question-answering`, `token-classification`, `text-generation`, `text2text-generation`, `summarization`, `translation`, `automatic-speech-recognition`, and `audio-classification`.

Use `sub-skills/evaluator-pipelines/scripts/inspect_evaluator_tasks.py` to inspect the installed registry without downloading models or datasets.
