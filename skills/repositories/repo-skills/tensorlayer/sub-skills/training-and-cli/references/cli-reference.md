# CLI Reference

## Verified APIs

- `tl.utils.fit(network, train_op, cost, X_train, y_train, acc=None, batch_size=100, n_epoch=100, print_freq=5, X_val=None, y_val=None, eval_train=True, tensorboard_dir=None, tensorboard_epoch_freq=5, tensorboard_weight_histograms=True, tensorboard_graph_vis=True)`
- `tl.utils.test(network, acc, X_test, y_test, batch_size, cost=None)`
- `tl.utils.predict(network, X, batch_size=None)`
- `build_arg_parser(parser)`
- `Trainer(training_dataset, build_training_func, optimizer, optimizer_args, batch_size=32, prefetch_size=None, checkpoint_dir=None, scaling_learning_rate=True, log_step_size=1, validation_dataset=None, build_validation_func=None, max_iteration=inf)`

## Usage notes

- `fit` is the high-level supervised training helper used by the examples.
- `test` and `predict` operate on the same `Model` object after training.
- `build_arg_parser` underlies the `tensorlayer.cli` command-line entry point.
- `Trainer` is the distributed-training interface; it is optional for CPU-only workflows and may require Horovod/OpenMPI in real deployments.

## Evidence summary

This page distills TensorLayer's public training tutorials, CLI parser implementation, and distributed-trainer documentation into the verified API notes above. The bundled smoke uses synthetic data and does not require source examples.
