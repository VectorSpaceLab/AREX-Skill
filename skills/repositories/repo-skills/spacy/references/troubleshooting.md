# Cross-Cutting Troubleshooting

## Purpose

Use this file for install/import/model/backend problems that cut across multiple spaCy workflows. Workflow-specific details live in the nearest sub-skill troubleshooting reference.

## Common symptoms

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'spacy'` | spaCy is not installed in the active Python environment | Switch to the correct environment or install the public package, then run the `install-and-inspect` healthcheck. |
| `ImportError`, `undefined symbol`, or `numpy.dtype size changed` | ABI mismatch from a stale or incompatible compiled install | Reinstall spaCy and compiled dependencies in a clean supported Python environment. |
| `python -m spacy --help` works but `spacy` is not found | Console-script PATH shadowing | Use `python -m spacy` or fix the active environment's PATH. |
| `OSError: [E050] Can't find model ...` | A pretrained pipeline package or local pipeline path is missing | Install the model package only if the workflow truly needs pretrained components. |
| `python -m spacy validate` reports incompatible pipelines | Installed pipeline packages are stale relative to the spaCy version | Update or reinstall the listed model packages. |
| `spacy.prefer_gpu()` is false | Optional GPU/Apple backend is unavailable | Continue on CPU unless the user made acceleration a hard requirement. |
| A workflow asks for `lookups`, `transformers`, `ja`, `ko`, or `th` | Optional extras are missing | Install only the extra the user needs; do not claim the base install failed. |

## Recovery order

1. Verify the active Python can import `spacy`.
2. Run the `install-and-inspect` healthcheck script.
3. Confirm whether the problem is a missing model package, an optional extra, a backend choice, or a workflow-specific config/data issue.
4. Route deeper issues to the owning sub-skill.

## When to stop

Stop when the user needs a pretrained model package, a specific backend wheel, or a different environment manager that is not already available. Those are environment-selection issues, not root skill issues.
