---
name: cleanlab
description: "Routes cleanlab data-centric AI workflows for finding label
  errors, dataset issues, outliers, annotator quality, and task-specific
  label-quality problems."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# cleanlab

Use this repo skill when a task involves the `cleanlab` Python package or the broader cleanlab workflow vocabulary: data-centric AI, label errors, noisy labels, label quality, dataset health, Datalab audits, CleanLearning, outliers, near duplicates, non-IID checks, annotator quality, or task-specific label issue detection.

cleanlab is API-first. It does not expose a package-specific command-line interface in this checkout; route future agents to Python APIs and the bundled smoke scripts.

## Install and quick verification

For normal use:

```bash
python -m pip install cleanlab
```

For Datalab or image issue workflows:

```bash
python -m pip install "cleanlab[datalab]"
python -m pip install "cleanlab[image]"
# or all stable optional extras:
python -m pip install "cleanlab[all]"
```

For a local checkout when developing or validating this exact repo version:

```bash
python -m pip install -e ".[all]"
```

Then run the bundled root check when you need a safe import smoke test:

```bash
python scripts/check_install.py --include-optional
```

Read [`references/troubleshooting.md`](references/troubleshooting.md) if installation, optional dependencies, imports, model probabilities, or shape validation fail. Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is stale for another checkout.

## Route map

| Task signal | Read this sub-skill | Why |
| --- | --- | --- |
| Broad audit of one dataset; `Datalab`, `find_issues`, `report`, `get_issues`, issue summaries, custom issue managers, image issue checks | [`sub-skills/datalab/SKILL.md`](sub-skills/datalab/SKILL.md) | Datalab orchestrates multiple issue families and report tables. |
| Standard single-label binary/multiclass noisy-label cleanup; `CleanLearning`; `cleanlab.filter`, `count`, `rank`, `dataset`; data valuation; synthetic noise | [`sub-skills/classification/SKILL.md`](sub-skills/classification/SKILL.md) | Main direct API route for multiclass label quality and robust learning. |
| Multiple annotators, consensus labels, annotator quality, active learning / relabeling priorities | [`sub-skills/multiannotator/SKILL.md`](sub-skills/multiannotator/SKILL.md) | Multiannotator APIs combine raw annotations with model probabilities. |
| Outlier or OOD scoring from feature embeddings or `pred_probs` alone | [`sub-skills/outlier/SKILL.md`](sub-skills/outlier/SKILL.md) | `OutOfDistribution` returns score vectors for atypical examples. |
| Multi-label classification labels as list-of-lists; regression target label issues | [`sub-skills/tabular-label-issues/SKILL.md`](sub-skills/tabular-label-issues/SKILL.md) | Stable nonstandard tabular label workflows with distinct formats. |
| Token classification, object detection, semantic segmentation label issues, structured outputs, bounding boxes, masks | [`sub-skills/structured-label-issues/SKILL.md`](sub-skills/structured-label-issues/SKILL.md) | Nested token lists, object boxes, and pixel masks need task-specific APIs. |
| Explicit `cleanlab.experimental` use, low-memory batched helper, span classification wrapper, PyTorch/CIFAR/MNIST/co-teaching examples | [`sub-skills/experimental/SKILL.md`](sub-skills/experimental/SKILL.md) | Experimental helpers are unstable or optional; prefer stable routes first. |

## Operating rules

- Prefer out-of-sample model probabilities. For label-error workflows, `pred_probs` should be aligned to the same rows as `labels` and should come from held-out data, cross-validation, or a model trained elsewhere.
- Validate shapes before running expensive workflows: classification `(N, K)` probabilities, multilabel `(N, K)` independent probabilities, token lists per sentence, object-detection box arrays, and segmentation `(N, K, H, W)` probabilities.
- Use Datalab for a broad issue audit and direct module APIs for focused label-quality or scoring tasks.
- Treat experimental helpers as opt-in. Do not install `torch`, `torchvision`, or `skorch` unless the user explicitly chooses those optional deep-learning examples.
- If a workflow needs image-specific Datalab checks, install the image extra or all extras and verify `cleanvision` imports.
- The generated references and scripts are self-contained. Do not instruct future agents to open this repo's original docs, tests, notebooks, or source scripts for normal operation.

## Shared runtime files

- Read [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting package install/import, optional dependency, API input, and stale-version recovery guidance.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) to compare a future checkout against the commit and evidence used to generate this skill.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) is structured metadata consumed by DisCo's repo-skills router import transaction.
- Run [`scripts/check_install.py`](scripts/check_install.py) to verify the installed package, stable submodules, and optional extras before using deeper sub-skills.

## Good first branch decisions

- If the prompt says "find all issues in my dataset" or mentions `lab.report()`, start with Datalab.
- If it says "mislabeled examples" for a normal classifier and already has `pred_probs`, start with classification.
- If it says "bad annotators", "consensus", or "which examples should be relabeled", start with multiannotator.
- If it says "OOD", "outlier score", or "feature embeddings look atypical", start with outlier unless the user also wants a broad Datalab audit.
- If it says "multilabel", "regression target issue", or "numeric labels look wrong", start with tabular label issues.
- If it says "token classification", "NER", "bounding boxes", "object detection", "semantic segmentation", or "pixel masks", start with structured label issues.
