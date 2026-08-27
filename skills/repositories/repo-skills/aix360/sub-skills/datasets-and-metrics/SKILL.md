---
name: datasets-and-metrics
description: "Guides AIX360 dataset acquisition, local-path validation,
  preprocessing contracts, explanation-quality metrics, and offline
  troubleshooting for HELOC, COMPAS, CDC, MEPS, Ford, Sunspots, CIFAR, MNIST,
  CelebA, eSNLI, and related datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AIX360 datasets and metrics

Use this route when the task involves an AIX360 dataset, a local data directory,
preprocessing, faithfulness, monotonicity, or explanation-quality checks. It
covers data contracts and evaluation inputs; route model fitting, explainer
construction, and explanation generation to the algorithm-owning sub-skill.
Do not treat the dataset classes as download managers in an offline run.

## Route quickly

- Read [data-formats.md](references/data-formats.md) before choosing a class,
  file layout, preprocessing callback, or array shape.
- Read [api-reference.md](references/api-reference.md) for constructor and
  return contracts, including classes that are importable only from their
  defining module in this release.
- Read [workflows.md](references/workflows.md) for local-only validation,
  preprocessing, and metric recipes.
- Read [troubleshooting.md](references/troubleshooting.md) when a constructor
  tries to download, an optional dependency is absent, or a metric returns an
  unexpected value.
- Run [check_dataset_contract.py](scripts/check_dataset_contract.py) with
  `--help` first. Use its dataset checks against a user-supplied local
  directory; it never downloads or instantiates a network-capable dataset
  class.

## Safe operating procedure

1. Identify the dataset class and its exact raw or processed file contract.
2. Obtain permission/licensing for the dataset independently. Do not fabricate
   a fixture as a substitute for a licensed benchmark.
3. Put data in a user-controlled directory and validate it with the bundled
   checker. Use `--no-network` (the default) and fix structural failures first.
4. If the class has a local-path constructor, pass `dirpath` explicitly. A
   path argument does not imply offline behavior for classes whose constructor
   still downloads missing files.
5. Apply the documented preprocessing callback, retaining feature names and
   target alignment. Record any row filtering, sentinel conversion, encoding,
   normalization, or split seed.
6. Before evaluating an explanation, make `x`, `coefs`, and `base` refer to the
   same feature order and length. For a sparse explanation, zero-fill a full
   coefficient vector rather than passing only selected weights.
7. Evaluate one row at a time with a model exposing `predict_proba`. Check
   finite outputs and interpretation direction before aggregating cases.

## Dataset decision points

- Use HELOC, COMPAS, Adult, and MEPS for tabular CSV workflows; their
  constructors expect fixed filenames and generally fail rather than infer a
  different layout.
- Use TED when a deterministic packaged synthetic CSV is sufficient. Its
  `load_file` contract separates feature columns, `Y`, and `E`.
- Use MNIST, Fashion-MNIST, CIFAR, or CelebA for image workflows only when the
  required local files and framework dependencies are already available.
- Use Ford, Sunspot, or Climate for time-series workflows; preserve the
  returned sequence/window conventions instead of flattening silently.
- Use CDC only when the NHANES XPT files, conversion dependency, and data-use
  expectations are understood. Its constructor performs a multi-file download
  when files are missing.
- Use eSNLI only with a local JSONL file at the class's expected location; the
  class has no `dirpath` parameter in this release.

## Metric guardrails

`faithfulness_metric(model, x, coefs, base)` returns a scalar correlation-like
score. It removes each feature by replacing it with `base` and compares the
resulting predicted-class probabilities with `coefs`; higher positive values
are generally better, but constant inputs can produce `nan`.

`monotonicity_metric(model, x, coefs, base)` returns a boolean. It starts at
`base`, adds features in ascending **signed** coefficient order, and requires
predicted-class probabilities to be non-decreasing. This is not an absolute-
importance sort and is not a global model monotonicity proof.

Both functions use `model.predict_proba`, select the class predicted on `x`,
and reshape `x` to one row. They are local diagnostics, not causal or fairness
claims. See [api-reference.md](references/api-reference.md) for exact details.

## Boundaries

This route does not fit a classifier, train a neural network, call an explainer,
or reproduce a full notebook. Hand those tasks to the relevant algorithm
sub-skill. Dataset downloads, license forms, external R/SPSS conversion, large
archives, and GPU/framework setup are documented limitations; the bundled
checker provides a no-network structural alternative, not a downloader.
