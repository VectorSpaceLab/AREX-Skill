# AIX360 Installation and Runtime Troubleshooting

## Purpose

Use this reference for failures that affect several AIX360 routes. For
algorithm-specific symptoms, continue to the troubleshooting reference in the
owning sub-skill.

## Diagnose before changing dependencies

Run the bundled checker against the modules required by the selected workflow:

```bash
python scripts/check_environment.py --group base
python scripts/check_environment.py --group local-black-box
python scripts/check_environment.py --group time-series
python scripts/check_environment.py --json
```

The script performs imports and metadata checks only. It does not download data,
load remote weights, train models, or assert that an optional algorithm has
completed a numerical workflow.

## `import aix360` works but an algorithm import fails

**Likely cause:** the base distribution intentionally installs only NumPy,
pandas, scikit-learn, and matplotlib. Most explainers have their own optional
extra.

**Recovery:**

1. Identify the owning sub-skill and exact module.
2. Create or use an isolated environment for that algorithm family.
3. Install one documented extra, such as `aix360[lime]`, `aix360[tslime]`, or
   `aix360[rbm]`.
4. Re-run the environment checker for that group and a tiny fixture from the
   owning sub-skill.
5. Do not infer that every algorithm is now available.

## Dependency resolver conflicts across extras

AIX360 0.3.0 records historical pins for several families:

- `contrastive` and `profwt`: Keras 2.3.1 and TensorFlow 1.14;
- historical `shap`: Keras 2.3.1 and TensorFlow 1.14;
- `nncontrastive`: TensorFlow 2.9.3;
- several rule/prototype/time-series extras: NumPy or pandas upper bounds;
- `gce`: an old `numba` ceiling;
- `matching`: a Git-based `otoc` dependency;
- `imd`: Graphviz and `pygraphviz` for visualization;
- `glance`: tightly pinned NumPy/pandas/scikit-learn plus DiCE, igraph, and
  XGBoost.

Do not solve all families in one environment. Build separate environments by
workflow and use a Python version supported by that extra. If a historical
TensorFlow wheel is unavailable for the platform/Python combination, treat the
route as unavailable rather than weakening the pin and claiming compatibility.

## `pkg_resources` failure or warning through `xport`

ProtoDash and some CDC/MEPS data paths can import `xport`, whose historical
release uses `pkg_resources`. New setuptools releases may remove or deprecate
that API.

- If the symptom is `ModuleNotFoundError: No module named 'pkg_resources'`, use
  an isolated environment with a setuptools release that still provides it.
- If the import only warns about deprecation, record the warning and run the
  intended tiny fixture before accepting the environment.
- Do not pin the global Python or another project's environment to repair this
  compatibility issue.

## NumPy, pandas, or scikit-learn API drift

Symptoms include removed aliases, changed one-hot encoder arguments, object
versus dense array differences, or stricter feature-name validation. These are
common when an old AIX360 algorithm is combined with a much newer scientific
Python stack.

Use the versions constrained by the selected extra. If no constraint exists,
prefer the package's tested Python era and verify the exact algorithm with a
tiny fixture. Do not patch inputs until you know whether the error is schema
misuse or dependency drift.

## Solver and compiled-system failures

Rule/prototype/certification paths may need CVXPY solvers, `ecos`, Graphviz,
`pygraphviz`, or other compiled libraries.

- Inspect installed CVXPY solvers before fitting a rule model.
- Treat visualization as optional when model fitting/explanation succeeds but
  Graphviz rendering fails.
- For `pygraphviz`, install compatible Graphviz system libraries in the
  environment rather than suppressing the import error.
- Never report a solver result if the optimization status is infeasible,
  unbounded, failed, or missing.

## Dataset constructor starts a download

Several dataset classes download when expected local files are absent. In an
offline or controlled environment:

1. stop before calling the download path;
2. read the dataset contract in `datasets-and-metrics`;
3. run its bundled local directory checker;
4. place authorized data in the documented layout or provide a tiny local
   fixture;
5. keep network and licensing decisions explicit.

A missing dataset is not an instruction to bypass license terms, disable TLS,
or fetch an unverified mirror.

## Model callable or shape failures

Common symptoms are indexing errors, `axis` errors, class-name mismatches, or an
explanation with the wrong feature/time dimension.

- Test the model on a small batch before constructing an explainer.
- Record input shape, output shape, dtype, class order, and whether outputs are
  labels, scores, or probabilities.
- Preserve the batch axis even for one observation.
- Use the local-black-box model-output checker for classifiers, and the
  time-series data-format contract for temporal models.
- Align coefficient/saliency vectors to the exact transformed feature space,
  not the raw column count.

## Numerical output contains NaN, all-zero weights, or unstable values

Check for constant columns, an inappropriate baseline, insufficient
perturbations/samples, an insensitive model around the query, singular local
fits, and solver failure. Set a random seed where supported, compare a tiny
controlled model, and report instability rather than interpreting noise.

## When to stop

Stop and ask for a decision or a compatible environment when the only next step
requires credentials, a restricted dataset, a large download, model training,
legacy wheels unavailable for the host, unsupported GPU/accelerator claims, or
system package changes. Do not turn those conditions into a silent fallback or
an unverified success claim.
