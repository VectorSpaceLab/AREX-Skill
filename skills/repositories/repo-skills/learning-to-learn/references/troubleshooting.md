# Cross-cutting Troubleshooting

## TensorFlow 2.x or missing `tf.contrib`

Symptom: imports fail with `No module named tensorflow.contrib`, `module 'tensorflow' has no attribute 'flags'`, or similar errors.

Cause: the repository uses TensorFlow 1.x APIs, including `tf.flags`, `tf.app`, `tf.train.QueueRunner`, `tf.contrib.learn`, and graph sessions.

Recovery:

1. Use a Python version and dependency set that supports TensorFlow 1.x.
2. Install `tensorflow==1.15.*`, `dm-sonnet==1.*`, and `protobuf<3.20`.
3. Re-run the root environment checker before attempting CLI or graph debugging.

## Protobuf descriptor error on TensorFlow import

Symptom: TensorFlow import fails with `Descriptors cannot not be created directly`.

Cause: TensorFlow 1.15 generated protobuf files are incompatible with newer protobuf 4.x runtimes.

Recovery: install `protobuf<3.20` in the runtime environment, then rerun the import check.

## Sonnet API mismatch

Symptom: missing `snt.AbstractModule`, `snt.RNNCore`, `snt.nets.MLP`, or `snt.nets.ConvNet2D`.

Cause: the code targets Sonnet 1.x. Sonnet 2.x has a different API.

Recovery: use `dm-sonnet==1.*` with TensorFlow 1.x.

## Source modules cannot be imported

Symptom: `No module named meta`, `No module named networks`, or `No module named problems`.

Cause: the repository is a script/module checkout, not a package with setup metadata.

Recovery:

- Run commands from a checkout/source tree containing the root modules, or add that source tree to `PYTHONPATH` for runtime inspection.
- For bundled helpers, pass `--repo-root` when the helper needs to import or run source modules.

## Data-backed problems perform side effects

Symptoms: unexpected dataset download, CIFAR archive extraction, TensorFlow queue runners, or cache files.

Cause: `mnist` loads MNIST data in the factory; `cifar10` downloads/extracts CIFAR-10 when its path is absent and creates input queues.

Recovery:

- Use `simple`, `simple-multi`, or `quadratic` for safe smoke checks.
- Use data-backed problems only when dataset/cache writes are acceptable.
- Keep data and queue setup outside any custom `make_loss` passed into `MetaOptimizer`.

## Saved optimizer confusion

Symptom: treating `.l2l` files like TensorFlow checkpoints fails.

Cause: `.l2l` files are pickle payloads produced by `networks.save` and loaded as initializers by `networks.factory`.

Recovery:

1. Ensure the save directory contains one `.l2l` file per optimizer id.
2. Wire each file through the matching network config `net_path`.
3. Rebuild the graph before loading; do not use TensorFlow checkpoint restore APIs for `.l2l` files.

## Deprecation warnings

TensorFlow 1.x emits warnings about deprecated symbols under modern runtimes. If imports, graph construction, and tiny CPU smokes pass, these warnings are expected and not a skill failure.
