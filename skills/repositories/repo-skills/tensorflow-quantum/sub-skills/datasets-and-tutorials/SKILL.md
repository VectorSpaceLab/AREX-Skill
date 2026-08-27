---
name: datasets-and-tutorials
description: "Route TFQ dataset helpers and notebook-style workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Datasets and Tutorials

Use this skill for TensorFlow Quantum prompts about dataset loaders, tuple outputs, and the small notebook-derived recipes used in the public tutorials.

## Route here when the user asks about
- `tfq.datasets.excited_cluster_states`
- `tfq.datasets.tfi_chain`
- `tfq.datasets.xxz_chain`
- tuple contents such as `circuits`, `labels`, `pauli_sums`, and `SpinSystemInfo`
- notebook snippets from `hello_many_worlds`, `gradients`, `noise`, `qcnn`, `quantum_data`, `quantum_reinforcement_learning`, and `research_tools`

## Do not use this skill for
- low-level tensor/backend mechanics; hand off to `tensor-ops-and-execution`
- broader Keras layer design beyond the notebook recipes here; hand off to `keras-quantum-layers`
- full notebook validation or maintainer scrubbing as a default runtime step
- Bazel/source-build or benchmark workflows

## Read first
- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`

## Fast answer rule
If the prompt is short and factual, answer from the API reference. If it asks for a tiny worked example, use the workflow snippets. If it reports a failure, use troubleshooting before changing the recipe.

## Shared smoke helper
For a tiny packaged import and round-trip check, run `python scripts/tfq_smoke_check.py --quick --datasets` from the root `tensorflow-quantum` skill directory instead of running whole notebooks.

## Evidence anchors
- Public package docs and tutorials distilled into this sub-skill's bundled
  references.
- The installed-package inspection used during construction to confirm the
  public TFQ dataset signatures and the tiny cluster-state smoke behavior.
- The source repository tests that establish dataset shapes, errors, and
  download behavior, summarized here rather than referenced directly at runtime.
