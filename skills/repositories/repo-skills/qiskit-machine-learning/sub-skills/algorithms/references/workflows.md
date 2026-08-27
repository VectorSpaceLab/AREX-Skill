# Algorithms workflows

These workflows use only public APIs. Keep the dataset, preprocessing, seed,
primitive, optimizer, and score in the experiment record.

## 1. Reproducible VQC classification

1. Install `qiskit-machine-learning` and compatible Qiskit/scikit-learn.
2. Set `qiskit_machine_learning.utils.algorithm_globals.random_seed` before
   constructing the model. Seed data splitting separately if using a classical
   splitter.
3. Prepare `X_train, X_test` as numeric arrays of shape `(N, D)` and labels as
   either a 1D array of class values or one-hot `(N, C)`. Scale data to the
   feature-map's useful angle range when the chosen encoding expects bounded
   features. The README's `ad_hoc_data` returns train/test arrays and one-hot
   labels; dataset generation itself belongs to `data-circuits-connectors`.
4. Make a `feature_map` with `D` data features and an ansatz with trainable
   parameters, or pass `num_qubits=D` and accept the defaults. Construct:

   ```python
   from qiskit_machine_learning.algorithms import VQC
   from qiskit_machine_learning.optimizers import COBYLA
   vqc = VQC(
       feature_map=feature_map,
       ansatz=ansatz,
       optimizer=COBYLA(maxiter=30),
       sampler=sampler,  # optional public Sampler V2
       callback=callback,  # optional (weights, objective_value)
   )
   ```

5. For the default VQC probability output, fit one-hot labels (shape
   `(N, 2)` for binary data), then call `score(X_test, y_test)` and
   `predict(X_test)`. If passing integer or string labels, allow VQC's public
   encoder to transform them and keep the same label vocabulary across fits.
6. Check `vqc.weights`, `vqc.fit_result`, prediction shape, and held-out score.
   An optimizer's objective value is not classification accuracy.

A tiny public sample is in `scripts/vqc_smoke.py`. It uses a deterministic
small ad-hoc recipe and a bounded optimizer; it is a smoke, not a quality
benchmark. Use `python /absolute/path/to/vqc_smoke.py --help` from any cwd.

## 2. VQR scalar regression

1. Prepare `X.shape == (N, D)` and numeric `y.shape == (N,)`. Scale inputs and,
   when necessary, targets to the range of the estimator observable.
2. Build `VQR` with a feature map/ansatz and a public V2 estimator. By default,
   VQR measures a Z tensor observable and uses `squared_error`; use
   `loss="absolute_error"` for outlier robustness or a public `Loss` object
   where its output shape matches the estimator output.
3. Fit, inspect `predict(X)` (often `(N, 1)`), and call `score(X, y)` for `R^2`.
   Flatten predictions only when comparing with a 1D target in external NumPy
   metrics; do not reshape targets to hide a QNN output mismatch.
4. If you need an arbitrary observable, pass a Qiskit `BaseOperator` matching
   the circuit qubits. With a pass manager, transpile the circuit and apply its
   layout to the observable; VQR's `pass_manager` handles the construction
   path, while a custom QNN workflow is owned by `qnn-gradients`.

## 3. Kernel classifiers and regressors

Use `kernels-fidelity` to construct and validate a fidelity kernel. Then attach
it to the model:

```python
qsvc = QSVC(quantum_kernel=qkernel, C=1.0)
qsvc.fit(X_train, y_train)       # X_train: (N, D), y_train: (N,)
labels = qsvc.predict(X_test)    # (M,)
accuracy = qsvc.score(X_test, y_test)

qsvr = QSVR(quantum_kernel=qkernel, C=1.0, epsilon=0.1)
qsvr.fit(X_train, y_train)       # y_train: (N,)
predictions = qsvr.predict(X_test)  # (M,)
```

For precomputed mode, evaluate the kernel before fitting:
`K_train = qkernel.evaluate(X_train, X_train)` and
`K_test = qkernel.evaluate(X_test, X_train)`. Fit with `K_train (N, N)` and
predict with `K_test (M, N)`. A matrix with `(M, M)` is only correct when the
prediction rows and training rows happen to be the same set; otherwise it is
a common silent semantic error.

For `PegasosQSVC`, construct `PegasosQSVC(quantum_kernel=qkernel, C=..., num_steps=...)`
for raw data, or `PegasosQSVC(precomputed=True, ...)` for matrices. Labels must
have exactly two unique values. It has no early stopping; bound `num_steps` for
experiments and inspect `decision_function`/`predict_proba` when diagnosing a
margin.

## 4. Callbacks, initial points, and warm starts

A model callback has exactly two parameters: the current weight array and a
floating objective value. Keep the callback side-effect small and append
values to a list for later plotting. Do not pass an optimizer-specific callback
without checking its arity; for example, a steppable optimizer callback may
receive more arguments.

`initial_point` must be aligned with the ansatz/QNN weight count. If it is
omitted, a random point is selected. With `warm_start=False`, each `fit`
starts afresh (unless an explicit initial point is set). With `warm_start=True`,
a later fit starts at the prior fitted point. Use this for incremental batches
with the same circuit and output width; VQC rejects a changed class count.

A safe continuation sequence is:

```python
model.to_dill("model.dill")
loaded = VQC.from_dill("model.dill")
loaded.warm_start = True
loaded.optimizer = COBYLA(maxiter=20)
# Replace the primitive only with an explicitly compatible public primitive.
loaded.fit(X_next, y_next)
```

Read [model-persistence.md](model-persistence.md) first; preserving a cloud
primitive inside dill is deliberate and may not be portable.

## 5. QBayesian inference

1. Build a circuit whose named registers each contain one qubit. Prepare the
   binary joint distribution using public Qiskit gates; register names become
   variable labels.
2. Construct `QBayesian(circuit, sampler=sampler, limit=10, threshold=0.9)`.
   Use a public sampler compatible with the target backend. A reference
   statevector sampler is suitable for a local smoke.
3. Call `rejection_sampling(evidence={})` for the unconditional joint
   distribution, or supply evidence such as `{"A": 1}`. Use
   `format_res=True` when variable-labelled keys are easier to inspect.
4. Call `inference(query={"B": 1}, evidence={"A": 1})` for a conditional
   probability. To reuse the last samples, omit evidence only after a prior
   rejection-sampling call. Verify `0 <= result <= 1`, inspect `samples`, and
   check `converged` for evidence runs.
5. Keep evidence values binary and labels exact. For a high-threshold,
   low-probability event, increase `limit` only with a deliberate runtime
   budget; an unconverged result is not an exact conditional probability.

## 6. V2 primitives and pass managers

V2 migration does not mean every primitive accepts an arbitrary circuit. If a
runtime primitive requires ISA circuits, construct a backend-specific pass
manager and pass it consistently to the algorithm or its underlying public
QNN/fidelity object. Sampler paths need measurements before transpilation;
Estimator paths need observables transformed with `observable.apply_layout(isa_qc.layout)`.
Use stable classical register names such as `meas` or `c` with Sampler V2.

Do not mix a V1-oriented recipe, a V2 primitive, and an untranspiled circuit by
accident. Start with a reference V2 primitive for local validation, then adapt
one backend at a time and record the backend/pass-manager pair.
