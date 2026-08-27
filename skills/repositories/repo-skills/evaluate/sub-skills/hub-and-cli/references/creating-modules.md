# Creating Custom Evaluation Modules

This reference covers custom Evaluate module authoring and `evaluate-cli create` workflows. For loading and computing existing modules, use the sibling loading and computation sub-skills.

## Safety Model

`evaluate-cli --help` and the bundled inspector script are safe because they only import the CLI and print parser help. `evaluate-cli create` is not a dry-run scaffold command: the source creates a Hugging Face Space, clones it with Git, renders the cookiecutter template, commits, and pushes. Only run it when the user has explicitly approved network and credentialed Hub mutation.

## CLI Create Behavior

Command shape:

```bash
evaluate-cli create "My Metric" --module_type metric --output_dir ./modules
```

Important arguments:

| Argument | Meaning | Notes |
| --- | --- | --- |
| `module_name` | Pretty name such as `Exact Match` | Must not contain `-`; slug becomes lowercase with spaces replaced by `_`. |
| `--module_type` | One of `metric`, `comparison`, or `measurement` | Any other value raises `ValueError`. |
| `--dataset_name` | Dataset-specific module card value | Optional; inserted into README frontmatter. |
| `--module_description` | Short module description | Optional but useful for generated template context. |
| `--output_dir` | Parent directory for the cloned/rendered module | Defaults to current working directory. |
| `--organization` | Hub namespace for the Space | If omitted, CLI calls `HfApi().whoami()` and uses the logged-in user's name. |
| `--private` | Create private Space | Requires token permissions for private Space creation. |

The current source imports `cookiecutter.main.cookiecutter` and `huggingface_hub.Repository`. Environments with a newer `huggingface_hub` that no longer exports `Repository` can fail before the CLI parser is usable.

## Template File Structure

`evaluate-cli create` renders the repository `templates/` tree into a Hub Space. A generated module slug such as `my_metric` contains:

| File | Purpose |
| --- | --- |
| `my_metric.py` | Defines the class inheriting from `evaluate.Metric`, `evaluate.Comparison`, or `evaluate.Measurement`; implements `_info`, optional `_download_and_prepare`, and `_compute`. |
| `README.md` | Space/module card with YAML frontmatter, description, examples, inputs, outputs, limitations, citation, and references. |
| `requirements.txt` | Extra runtime dependencies for the Space/module. The template pins Evaluate from the upstream Git repository; adjust for release or reproducibility needs. |
| `app.py` | Loads the published module with `evaluate.load("namespace/my_metric")` and launches the Gradio widget. |
| `tests.py` | Defines `test_cases` with predictions, references, and expected result dictionaries. |

## Module Script Responsibilities

Implement `_info` first because it drives documentation, feature validation, and widget inputs. Return the appropriate `evaluate.MetricInfo`, `evaluate.ComparisonInfo`, or `evaluate.MeasurementInfo` with:

- `module_type`: the same kind used for `--module_type`.
- `description`: concise module behavior and intended use.
- `citation`: BibTeX or other citation text.
- `inputs_description`: expected arguments, return fields, and doctest-style example usage.
- `features`: a `datasets.Features` object, or a list of `datasets.Features` objects when multiple input schemas are accepted.
- Optional `homepage`, `codebase_urls`, and `reference_urls`.

Implement `_compute` with arguments matching the `features` fields and return a dictionary of result names to values. Keep `_compute` deterministic and side-effect-light; put downloads or model/resource initialization in `_download_and_prepare` instead.

Use `_download_and_prepare(self, dl_manager)` only when the module needs external cached resources. Use the download manager for URLs or archives; document any large, licensed, or authenticated resources in the README and requirements.

## README and Module Card Expectations

The README starts with YAML frontmatter used by Spaces and Hub rendering. Preserve valid YAML, including fields such as `title`, `datasets`, `tags`, `description`, `sdk`, `sdk_version`, `app_file`, and `pinned` when using the template.

Fill the human-readable sections with:

- clear module description and typical task context;
- minimal usage example with `evaluate.load(...)` and `.compute(...)`;
- inputs and defaults matching `_info().features` and `_compute`;
- output dictionary examples, score ranges, and what values mean;
- representative examples, including atypical inputs when relevant;
- limitations, bias, citations, and further references.

Tests in the repository validate that metric/comparison/measurement README YAML can be loaded as a dictionary, so malformed frontmatter is a publishability issue.

## Gradio Widget Caveats

The template `app.py` uses `evaluate.utils.launch_gradio_widget`. The widget helper imports Gradio lazily; missing Gradio fails only when launching the app, not when inspecting normal CLI help.

The widget infers Dataframe input types from `metric.features`: integer/float features become numeric, string features become string cells, and other feature types are treated as JSON strings and parsed with `json.loads`. For text metrics, widget users may need to wrap strings in double quotes. Complex features, multiple feature schemas, or custom UX may need a custom Gradio app instead of the default helper.

## Local Planning Without Credentials

When the user asks to plan or draft a custom module without publishing:

1. Choose a valid `module_type`: `metric`, `comparison`, or `measurement`.
2. Choose a pretty name without hyphens and derive the slug by lowercasing and replacing spaces with underscores.
3. Sketch the five generated files from the template table.
4. Specify `_info().features`, `_compute` arguments, result dictionary keys, and test cases.
5. State which steps remain credentialed: Space creation, clone, commit, push, and model-card metadata updates.

Do not fabricate successful Hub publication when credentials or network were intentionally avoided.
