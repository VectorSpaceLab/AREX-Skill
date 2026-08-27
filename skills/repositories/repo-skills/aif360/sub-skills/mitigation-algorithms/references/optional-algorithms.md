# Optional Mitigation Algorithms and Extras

AIF360 0.6.1 base CPU imports were verified during construction. Optional extras were intentionally not installed, so the workflows below are **optional/unverified** until the user's runtime installs the named extra and passes a tiny algorithm-specific smoke.

## Extra matrix

| Extra / dependency | AIF360 capability | Install hint | Status in this skill |
| --- | --- | --- | --- |
| `OptimPreproc` / `cvxpy>=1.0` | `OptimPreproc` with `OptTools` optimized preprocessing | `pip install 'aif360[OptimPreproc]'` | Optional/unverified; solver path not tested. |
| `DisparateImpactRemover` / `BlackBoxAuditing` | `DisparateImpactRemover` feature repair | `pip install 'aif360[DisparateImpactRemover]'` | Optional/unverified. |
| `LFR` / `torch` | LFR-related package extra, especially sklearn learned fair representations | `pip install 'aif360[LFR]'` | Optional/unverified; smoke legacy and sklearn routes separately. |
| `AdversarialDebiasing` / `tensorflow>=1.13.1` | Legacy and sklearn adversarial debiasing; intersectional adversarial branch | `pip install 'aif360[AdversarialDebiasing]'` | Optional/unverified; TensorFlow v1 compatibility required. |
| `Reductions` / `fairlearn~=0.7` | `ExponentiatedGradientReduction`, `GridSearchReduction` | `pip install 'aif360[Reductions]'` | Optional/unverified. |
| `ART` / `adversarial-robustness-toolbox>=1.0.0` | `ARTClassifier` wrapper | `pip install 'aif360[ART]'` | Optional/unverified; ART model backend also required. |
| No dedicated extra for `IntersectionalFairness` | `IntersectionalFairness` composite helper | Install algorithm-specific extras; verify TensorFlow and progress utilities manually | Optional/unverified; use only for explicit intersectional mitigation. |
| `FairAdapt` / `rpy2` | sklearn FairAdapt route | `pip install 'aif360[FairAdapt]'` | Route to sklearn-interface; optional/unverified. |
| `inFairness` / `skorch`, `inFairness>=0.2.2` | sklearn SenSeI/SenSR route | `pip install 'aif360[inFairness]'` | Route to sklearn-interface; optional/unverified. |
| `OptimalTransport` / `pot` | OT metric support | `pip install 'aif360[OptimalTransport]'` | Route to datasets-and-metrics; optional/unverified. |
| `FACTS` / `mlxtend`, `colorama`, `tqdm` | FACTS detector route | `pip install 'aif360[FACTS]'` | Route to detectors-and-explainers; optional/unverified. |

Prefer one named extra per requested workflow. Do not install `aif360[all]` unless the user explicitly asks for broad notebook-like functionality.

## Common missing-extra signals

- `No module named 'tensorflow': AdversarialDebiasing will be unavailable. To install, run: pip install 'aif360[AdversarialDebiasing]'`
- `No module named 'fairlearn': ExponentiatedGradientReduction will be unavailable. To install, run: pip install 'aif360[Reductions]'`
- `No module named 'fairlearn': GridSearchReduction will be unavailable. To install, run: pip install 'aif360[Reductions]'`
- `No module named 'inFairness': SenSeI and SenSR will be unavailable. To install, run: pip install 'aif360[inFairness]'`
- `ModuleNotFoundError: No module named 'BlackBoxAuditing'` when constructing `DisparateImpactRemover`.
- `ModuleNotFoundError: No module named 'cvxpy'` when importing or using `OptTools` for `OptimPreproc`.
- ART-related import errors when the user supplies or builds the external classifier passed to `ARTClassifier`.

These warnings do not mean base datasets, metrics, Reweighing, core postprocessors, or deterministic reranking are broken.

## Smoke strategy before claiming support

1. Install the smallest named extra in an isolated environment.
2. Run a direct import for the AIF360 class and the backend dependency.
3. Run a tiny in-memory dataset smoke with low iterations/epochs/grid sizes.
4. Validate at least one utility metric and one fairness metric.
5. Report exact scope: base verified, optional dependency installed and smoke-tested, optional/unverified, or not selected.

Class-specific smoke notes:

- `OptimPreproc`: import `OptTools`, use a tiny categorical dataset and minimal `clist`/`dlist`; solver success is required before full data.
- `DisparateImpactRemover`: test `repair_level=0.0` and `1.0` on a tiny numeric feature dataset; verify protected column preservation.
- `LFR`: set small `k`, `maxiter`, and `maxfun`; verify output shapes, not quality.
- `AdversarialDebiasing`: disable eager execution under TensorFlow 2, use a fresh session/scope, and set tiny `num_epochs`.
- `ExponentiatedGradientReduction`/`GridSearchReduction`: use an estimator with `sample_weight`; confirm constraints are supported by installed fairlearn.
- `ARTClassifier`: validate the ART classifier independently before wrapping; fairness must be measured separately.
- `IntersectionalFairness`: verify import first, then a tiny `StructuredDataset` with multiple protected attributes; avoid multi-worker/full data until smoke passes.
