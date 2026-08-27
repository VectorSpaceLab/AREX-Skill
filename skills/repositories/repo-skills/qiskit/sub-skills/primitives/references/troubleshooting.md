# Primitive troubleshooting

## The result key is not the one you expected

**Symptom**: the sampler result has a different `DataBin` field name than the examples.

**Cause**: the key name follows the measured classical register name, not a fixed hard-coded value.

**Fix**: inspect `result[0].data.keys()` first and then access the matching key.

## The sampler returns empty or confusing counts

**Symptom**: sampling works but the counts do not make sense.

**Cause**: the circuit was not measured, or the measurement layout does not match the interpretation you expected.

**Fix**: make the measurement explicit and use a small circuit first to verify the bit ordering.

## The estimator shape does not match the parameter sweep

**Symptom**: expectation values have a shape that is different from the observable or parameter input.

**Cause**: the PUB structure broadcasts parameter values and observables.

**Fix**: make the sweep dimensions explicit and use an `EstimatorPub` if the convenience tuple form is too implicit.

## The primitive job result type is unfamiliar

**Symptom**: `run()` returns a job but the nested result objects look new.

**Cause**: the v2 primitives return container classes rather than a simple flat list.

**Fix**: inspect `PrimitiveResult`, `PubResult`, and the container fields before assuming the older result shape.

## Sampling and estimation use different circuit forms

**Symptom**: the same circuit cannot be reused for both primitives without changing it.

**Cause**: sampling typically needs measurements, while estimators use an unmeasured circuit and an observable.

**Fix**: keep one abstract circuit and derive the measured version only for the sampler path.
