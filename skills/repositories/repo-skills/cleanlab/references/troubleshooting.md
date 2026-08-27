# cleanlab troubleshooting quick reference

Use this page for cross-cutting failures before entering a specific sub-skill. Each sub-skill also has narrower troubleshooting notes for its own data formats and APIs.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: cleanlab` | Package is not installed in the active Python environment. | Run `python -m pip install cleanlab`, then verify with `python scripts/check_install.py`. |
| `ImportError` for `Datalab` extras or image issue managers | Optional dependencies are missing. | Install `python -m pip install "cleanlab[datalab]"`, `"cleanlab[image]"`, or `"cleanlab[all]"` depending on the task. |
| `cleanvision` missing for image issue workflows | Image-specific Datalab checks rely on cleanvision. | Install the image extra and rerun `python scripts/check_install.py --include-optional`. |
| `datasets` import fails for Datalab examples | Some Datalab workflows use Hugging Face `datasets`, but plain array/DataFrame workflows do not. | Install all extras or rewrite the workflow around in-memory arrays / pandas DataFrames. |
| `torch`, `torchvision`, or `skorch` missing | Experimental deep-learning helpers are optional and not part of stable cleanlab workflows. | Only install these if the user explicitly asks for the experimental PyTorch/CIFAR/MNIST/co-teaching route. |

## No package CLI

cleanlab is operated through Python APIs. If a user asks for a command-line invocation, translate the task into a small Python script or notebook cell that calls `Datalab`, `CleanLearning`, `filter.find_label_issues`, `OutOfDistribution`, or the appropriate task-specific submodule.

## Data and probability validation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `pred_probs` row count differs from `labels` | Model probabilities are not aligned with the examples. | Rebuild the probability array so rows match the input labels exactly. |
| `pred_probs` rows do not sum to 1 for single-label classification | Scores are logits or one-vs-rest outputs rather than calibrated class probabilities. | Apply softmax/calibration or use a model API that returns `predict_proba`. |
| `labels` contain classes absent from `pred_probs` columns | Class indexing is inconsistent. | Re-encode labels as contiguous class indices and ensure column order matches those indices. |
| Label issue ranking looks too optimistic | Probabilities were generated in-sample from the same examples used for training. | Prefer cross-validation, held-out predictions, or an external model. |
| Datalab issue tables are empty | The requested issue type was incompatible with available inputs or all examples scored above threshold. | Check `issue_types`, supplied inputs, and call `show_all_issues=True` when printing a report. |

## Choosing the wrong abstraction

- Use [`../sub-skills/datalab/SKILL.md`](../sub-skills/datalab/SKILL.md) for broad audits with multiple issue types or a report-oriented workflow.
- Use [`../sub-skills/classification/SKILL.md`](../sub-skills/classification/SKILL.md) for direct single-label classification label-quality APIs and `CleanLearning`.
- Use [`../sub-skills/outlier/SKILL.md`](../sub-skills/outlier/SKILL.md) when the task only needs OOD/outlier scores from features or probabilities.
- Use [`../sub-skills/structured-label-issues/SKILL.md`](../sub-skills/structured-label-issues/SKILL.md) for NER/token, object-detection, and segmentation label issues.

## Stale skill checks

Before using this skill against a substantially newer cleanlab checkout, read [`repo-provenance.md`](repo-provenance.md). Refresh the skill if public API names, optional extras, Datalab issue types, or task-specific modules changed after the recorded commit/tag.

## Minimal verification command

```bash
python scripts/check_install.py --include-optional
```

If that passes but a deeper workflow fails, run the relevant sub-skill smoke script named in that sub-skill's `Read/run next` section.
