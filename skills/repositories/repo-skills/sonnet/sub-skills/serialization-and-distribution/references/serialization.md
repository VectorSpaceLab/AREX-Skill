# Serialization, Export, XLA, and Mixed Precision

## Checkpoint roundtrip

Build modules before saving so variables exist:

```python
model = snt.nets.MLP([8, 1])
model(tf.ones([1, 4]))
ckpt = tf.train.Checkpoint(model=model)
path = ckpt.save(prefix)
# restore into a newly built same-shaped module
restored = snt.nets.MLP([8, 1])
restored(tf.ones([1, 4]))
tf.train.Checkpoint(model=restored).restore(path).assert_existing_objects_matched()
```

Include optimizer objects after the first step when resuming training because slot variables are created lazily.

## SavedModel export

Wrap a built Sonnet module in a `tf.Module` or pass a `tf.function` signature. `tf.saved_model.load` returns a generic restored object/signature, not necessarily the original Python `snt.Module` subclass.

## Pickle and Keras caveats

TensorFlow checkpoints and SavedModel are preferred. Python pickle is brittle across code versions. Sonnet modules are not Keras `Layer` objects and do not support Keras `compile`/`fit` semantics by default.

## XLA and mixed precision

`tf.function(jit_compile=True)` can compile compatible Sonnet calls, but XLA support depends on TensorFlow ops and device runtime. Mixed precision is configured through Sonnet/TensorFlow policies and must be validated numerically for the task.
