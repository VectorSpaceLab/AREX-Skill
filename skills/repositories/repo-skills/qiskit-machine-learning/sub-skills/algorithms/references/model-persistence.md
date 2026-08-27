# Model persistence

`TrainableModel`, `QSVC`, `QSVR`, and `PegasosQSVC` expose the public
`SerializableModelMixin`. Prefer the current methods:

```python
model.to_dill("model_state.dill")
loaded = type(model).from_dill("model_state.dill")
```

The legacy `save` and `load` names delegate to these methods but are deprecated
in the current release. Keep the file extension explicit if your artifact
registry relies on one; the method writes exactly the filename supplied.

## What is saved

Dill serializes the model object and its parameters, including fitted weights,
optimizer state held by the model, label encoders, circuits, and referenced
primitive objects. A loaded model can therefore preserve the primitive instance
that was serialized. This is useful when continuing a cloud-backed experiment,
but it also means:

- treat a dill file as trusted executable content; never load an untrusted file;
- restore in a compatible Python, Qiskit, Qiskit Machine Learning, NumPy,
  scikit-learn, and dill environment;
- record the package/runtime versions, circuit definition, preprocessing,
  labels, primitive/backend, shots or precision, pass manager, loss, optimizer,
  and random-seed policy next to the file;
- do not assume a cloud session, credential, backend handle, or remote job can
  be reconstructed on another machine;
- verify predictions immediately after loading before further fitting.

`from_dill` checks that the deserialized object is an instance of the class on
which it was called and raises `TypeError` otherwise. This catches loading a
VQC file through an unrelated model class, but it is not a security boundary or
an API-version compatibility check.

## Save/load validation sequence

1. Fit the model and save a small fixed probe set and its predictions (or a
   deterministic score) outside the dill file.
2. Call `to_dill` with a user-owned path and confirm the file exists.
3. Load through the corresponding class, for example `VQC.from_dill` or
   `QSVR.from_dill`.
4. Re-run `predict` on the probe set and compare with an appropriate numerical
   tolerance. For classifiers compare labels and, where relevant, probability
   arrays. For regressors compare floating predictions.
5. Only then set `warm_start=True`, replace the optimizer, or replace the
   primitive. A changed primitive is a new runtime experiment and must be
   compatible with the circuit, measurements, observable, layout, and output
   semantics.

## Continuing training

The persistence tutorial saves a VQC after a bounded first run, reloads it,
sets `warm_start=True`, swaps to a second compatible sampler, and attaches a
new bounded optimizer before fitting again. The prior optimizer's final point
is used as the next initial point. Use the same feature/label encoding and
class count. If the circuit or output width changed, construct a new model
rather than forcing a warm start.

For an estimator or sampler supplied by a vendor/runtime, prefer a documented
session/lifecycle handle and an explicit compatible pass manager. Loading a
serialized primitive may retain stale service state; replacing it after load
is safer only when the replacement's interface and backend layout match.

## Hybrid models

A PyTorch model containing `TorchConnector` is not persisted with this dill
workflow. Recreate the QNN and enclosing `torch.nn.Module`, then use PyTorch's
`state_dict` save/load procedure; route connector/autograd details to
`data-circuits-connectors`. Keep the QNN circuit and preprocessing identical
when reconstructing the module.
