# Troubleshooting and recovery

## Optional or legacy TensorFlow/Keras stack

The `contrastive` extra pins historical `tensorflow==1.14` and
`keras==2.3.1`, with additional old-version constraints such as
`protobuf<3.20` and `h5py<3`. These dependencies are not part of a modern
CPU inspection environment and were not verified here. A missing TensorFlow or
Keras import means the CEM/CEM-MAF path is unverified; it is not evidence that
the algorithm is broken.

Recovery:

1. Isolate the historical stack in a separate environment matching its Python
   and binary constraints. Do not downgrade the shared environment.
2. Probe imports and load a caller-owned tiny compatible model before using
   any large image model. If the old stack cannot be resolved, stop at API and
   contract documentation and use GLANCE/Ecertify/other CPU-safe alternatives
   where they answer the task.
3. Do not claim GPU execution. On old TensorFlow/CUDA combinations, device
   placement can produce NaNs or SGEMM failures; the CEM-MAF device arguments
   can pin selected operations to CPU as a workaround, but no hardware result
   is implied.

## Missing `otoc` Git dependency

OTMatching imports its search backend lazily, so basic package import can look
healthy while `explain_instance` fails when `otoc` is requested. The matching
extra installs `otoc` from a Git source; network restrictions, compiler
requirements, or an incompatible current revision can prevent installation.

Recovery:

- Keep the exact matching arrays and constraints as a reproducible local
  fixture. Verify shape/marginals and report `otoc` as an unresolved required
  dependency for actual alternate-search execution.
- Do not replace OTMatching with an unconstrained nearest-neighbor method and
  call it equivalent. If a compatible pinned OT backend is approved, validate
  it in a separate environment and re-run the matching acceptance checks.
- A missing backend is not fixed by lowering `search_node_limit`; dependency
  resolution must happen first.

## Invalid bounds, actionability, or target class

Symptoms include out-of-domain candidates, no favorable predictions, empty
candidate frames, or a certificate that starts at `-1`.

Recovery:

- For CEM, validate `mode` as `PP` or `PN`, class ordering, one-hot target
  construction, image range, channel layout, and `offset`. CEM uses the
  original predicted class rather than an arbitrary target class.
- For GLANCE, ensure the model returns a one-dimensional binary prediction and
  that favorable is `1`. Supply explicit numeric/categorical lists and apply
  immutable/bounds checks after each candidate. `feat_to_vary` is not enforced
  by `NearestNeighborMethod`; do not treat its output as actionable without a
  post-check.
- For Ecertify, ensure `quality(x)` is a finite scalar at least `theta`, use
  `ub > lb`, and keep the region in the intended feature coordinates. The
  implementation returns `-1` when the center fails the threshold. It does
  not know feature-specific bounds or legal categorical values.
- For OTMatching, verify nonnegative plans, equal total marginal mass, and
  2-tuples in `search_match_pos_filter`. Reject or repair the input plan
  before searching rather than accepting a visually plausible plot.

Never silently widen a bound, change an immutable feature, or switch target
classes to obtain a result. Report infeasibility when the requested constraints
leave no valid candidate.

## Model probability/output interface mismatch

CEM's historical wrapper requires batch predictions and a graph-compatible
symbolic call. A scalar, class-ID array, missing `predictsym`, missing class
count, wrong input shape, or different class ordering can fail during graph
construction or make the loss meaningless. Use a tiny model adapter that
exposes the expected methods and verify:

- `predict(x)` has shape `(batch, n_classes)`;
- `predict_long(x)` agrees with `argmax(predict(x))` and class ordering;
- `predictsym(tensor)` is differentiable and returns `(batch, n_classes)`;
- the preprocessing applied to `predict` and `predictsym` is identical.

Ecertify has no fixed model interface: its `quality` callable must combine the
black-box output and explanation output. For classifiers, explicitly select a
class probability; do not pass `predict()` class IDs to a fidelity function
that expects a continuous score. GLANCE expects `predict(DataFrame)` and
favorable value `1`, not probabilities. OTMatching does not accept a model at
all.

## Network-bound models, data, or embeddings

CEM-MAF examples use pretrained classifier, attribute, GAN, image, and latent
assets. Matching examples may use external token embeddings and a transport
solver. Ecertify examples may load a tabular dataset and LIME/SHAP. These are
inputs, not safe defaults.

Recovery:

- In a network-disabled run, use a tiny caller-owned fixture and document the
  asset as unavailable. Do not invoke downloader utilities or infer a success
  from a cached file.
- If an asset is supplied, verify its expected shape, preprocessing, class
  count, and integrity before optimization. Preserve the original model's
  license/provenance outside this skill's runtime files.
- Dataset-loader ownership belongs to
  [../../datasets-and-metrics/SKILL.md](../../datasets-and-metrics/SKILL.md); keep
  this route focused on the algorithm after data preparation.

## Expensive image training or optimization

CEM and especially CEM-MAF run iterative gradient optimization, binary-search
loss constants, segmentation, attribute classifiers, and possibly a GAN. The
notebook-scale settings can take substantial CPU/GPU time and may require
large model assets.

Recovery:

1. Do not use image training or a full download as a smoke test.
2. First validate imports, signatures, one prepared input, and a very small
   iteration budget. Mark the result as shape-only if the target class was not
   reached.
3. Increase iterations/search steps only after a valid class-change/retention
   check. Record failures, NaNs, and device placement; do not reinterpret an
   all-zero or unchanged image as a successful PP/PN.

## GLANCE cost and candidate failures

`build_dist_func_dataframe` divides each numeric range by `n_bins`; a constant
column can create invalid distances. `DiceMethod` requires `dice_ml`, and
`C_GLANCE` string selectors require a training frame with `target`. Local
methods may return fewer candidates, while C-GLANCE drops clusters with no
counterfactuals and can raise when all centroid searches are empty.

Recovery:

- Check all columns exist, numeric/categorical lists are disjoint, numeric
  ranges are nonzero, and the training outcome is encoded as expected.
- Reduce cluster counts and requested local candidates for a tiny fixture.
- Try a CPU nearest-neighbor or random-sampling path to separate a data/model
  infeasibility from a DiCE dependency failure.
- Treat raw GLANCE `cost` as a sum over successful cases. Compute a mean only
  after checking the effectiveness count is nonzero.

## Certification and search budget

Ecertify consumes approximately `Z * Q` quality queries per run, multiplied by
`numruns` in the wrapper. Some strategies divide the budget internally and
small `Q` values can make the search invalid or uninformative. OTMatching's
node/depth limits similarly trade coverage for runtime.

Recovery: start with a deterministic tiny budget only to validate the call
contract; then choose a budget from the acceptance tolerance. Report the
strategy, query budget, number of runs, random behavior, and confidence/EVT
interpretation with the width. A finite returned width is not proof that no
lower-quality point exists outside the sampled/search region.

## Dependency-stack separation

Do not combine the historical TensorFlow/Keras CEM stack, the Git-backed OT
stack, and unrelated modern extras merely to make one environment import
more names. If pins conflict, maintain separate environments and verify each
capability with its own fixture. In the current inspection environment,
TensorFlow/Keras, `zoopt`, `otoc`, and `dice_ml` were unavailable; those
failures are explicit verification limits, while source-level API contracts
and lightweight NumPy/pandas helpers remain documented.
