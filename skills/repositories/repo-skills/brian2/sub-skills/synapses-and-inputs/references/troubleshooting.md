# Synapses and inputs troubleshooting

## Install/import and optional dependencies

- **`import brian2` fails:** verify the installed package is Brian2 2.9.0 and
  Python meets the package baseline, then use the configuration route's
  environment diagnostic. Do not infer that optional SciPy, Matplotlib, or
  compiler packages are required for the runtime NumPy smoke.
- **A code-generation backend fails while the model is valid:** switch only
  the diagnostic run to the supported runtime/NumPy target and hand compiler,
  Cython, and standalone concerns to `code-generation`. Do not rewrite a
  synaptic model to hide a backend failure.
- **Optional package missing:** Poisson/synapse core classes do not require
  plotting or data-analysis packages. Install an optional dependency only when
  the selected feature actually imports it; record the omission rather than
  treating it as a connectivity error.

## Data and configuration

- **Unit/dimension error in `w`, `delay`, `rate`, or `weight`:** inspect the
  target variable's declared unit. `delay` and spike times need seconds,
  Poisson rates need Hz, and `PoissonInput.weight` must match its target.
  Route equation-string dimension details to `units-and-equations`.
- **TimedArray shape/dt mismatch:** values must be 1-D or 2-D with time first;
  use `stim(t)` for 1-D and `stim(t, i)` for 2-D. Confirm the index is within
  the second axis and align sample `dt` to the consuming group clock; Brian
  uses held samples, not interpolation. If the group has a larger `dt` than the
  array and the ratio is non-integer, code generation raises a `ValueError`.
  If the group `dt` is smaller but the ratio is non-integer, the array is not
  locally constant for exact integration. Values clamp outside the sampled
  interval.
- **Changed `dt` after `PoissonInput` creation:** recreate the input with the
  target's new clock; the input stores the original target `dt` and rejects a
  later change.
- **Unexpected delay timing:** delays are quantized to the source pathway
  clock. Pick an integer-multiple delay or use a finer source clock; account
  for scheduling slots when comparing monitor output.

## API misuse

- **“Synapses ... has not created synapses” or assignment error:** construction
  only defines the object. Call `S.connect(...)` before assigning `S.w`,
  `S.delay`, indexing, or running a pathway. If an empty object is deliberate,
  deactivate it rather than running it as a functional pathway.
- **Indexing before connections:** `S[... ]`, `S.i[:]`, and synaptic state
  require existing edges. Build the complete graph first. Recreate a stored
  synaptic subgroup after adding edges.
- **Pre/post naming confusion:** use `v_post` for target writes and
  `x_pre`/`x_post` for connected variables. `on_pre` is source-event code;
  `on_post` is target-event code. Deprecated `pre`/`post` constructor aliases
  should be replaced with `on_pre`/`on_post`.
- **Missing event or threshold:** a pathway's source must define the selected
  event. For default `spike`, ensure the source is a spike source with a
  threshold/event; a plain group without one cannot drive `on_pre`.
- **Invalid connect form:** do not combine `condition` with `i`/`j`; paired
  array indices must be integer and broadcastable 1-D; generator syntax belongs
  in `i=` or `j=`, not as a condition. Use `skip_if_invalid=True` only for
  string-generated out-of-range pairs.
- **Parallel index failure:** third-axis indexing needs
  `multisynaptic_index=...`; without it, use raw synapse indices or pair
  indexing.

## Event-driven, delay, and input failures

- **Event-driven eligibility/dependency error:** automatic event-driven
  integration is for independent one-dimensional linear equations. Remove
  incompatible dependencies, mark the equation clock-driven, or implement a
  tested explicit elapsed-time update.
- **Invalid delay:** provide a scalar quantity with seconds dimensions, or set
  per-synapse values after `connect`. A delay mapping may name only existing
  pathways. A negative or non-time value is not a valid propagation delay.
- **High Poisson rate relative to `dt`:** `PoissonGroup` uses a Bernoulli-like
  `rand() < rates*dt` threshold and cannot represent multiple spikes from one
  unit in a step. Split the rate across units or choose `PoissonInput` when
  identities are unnecessary.
- **SpikeGenerator replay shifted or missing:** keep `indices` and `times`
  equal-length, nonnegative, and unitful; use `set_spikes` between runs; offset
  replay times by the current run start. Events earlier than the current time
  are ignored. Avoid two spikes for one neuron in one `dt` bin and ensure a
  periodic schedule has an integer-multiple period.

## Workflow failures

- **Weights changed but no target effect:** verify the source emitted the event,
  the pathway is attached to the intended event, `connect` created the expected
  edges, and `on_pre` writes the correct `_post` variable. Then test with one
  source, one edge, zero delay, and a deterministic spike.
- **STDP appears insensitive:** confirm traces are initialized, event order and
  relative timing are intentional, weights are not clipped immediately, and
  pre/post code is attached to the desired populations. Event-driven traces are
  not continuously updated monitor signals.
- **Summed target wrong or construction fails:** target parameter must exist,
  have matching dimensions, and have only one summed updater. Split multiple
  sources into distinct target accumulators and combine them in the target
  model.
- **Explicit `Network` misses input operation:** include `run_regularly`,
  `run_at`, or network-operation objects in the explicit network. Standalone
  compatibility is a code-generation concern.
