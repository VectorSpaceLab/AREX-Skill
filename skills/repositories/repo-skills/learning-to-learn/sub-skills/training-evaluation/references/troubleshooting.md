# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Folder <save_path> already exists` | `train.py` only creates a brand-new save directory. | Use a fresh directory or delete the old one before rerunning. |
| No `.l2l` file is found for L2L evaluation | `evaluate.py --optimizer=L2L --path=...` expects a directory that already contains the saved optimizer files. | Point `--path` at the directory produced by `train.py` and verify the expected file names such as `cw.l2l`. |
| Adam looks "reset" every epoch | The evaluation loop reinitializes the optimizee and the Adam slots at each epoch. | That is expected for this CLI. It is a baseline, not a warm-started optimizer. |
| Some steps seem to be missing | `num_steps // unroll_length` truncates remainder steps in training. | Choose values that divide evenly, or accept the dropped remainder. |
| MNIST/CIFAR starts downloading or queueing | Those problems use dataset loading and TensorFlow queue machinery. | Avoid them for smoke runs; consult `../problem-factories/SKILL.md` before using them intentionally, and pass the helper's `--allow-data` guard only when you really want that path. |
| TensorFlow or Sonnet imports fail | Wrong runtime, often TensorFlow 2.x or missing Sonnet 1.x / protobuf compatibility. | Use the TF1-compatible environment described in the repo evidence: TensorFlow 1.15, Sonnet 1.x, and protobuf < 3.20. |
| `tf.contrib` or legacy `tf.app.run` warnings appear | Expected under the legacy TensorFlow 1.x stack. | Treat the warnings as normal unless the script exits nonzero. |
| `evaluate.py --optimizer=Adam` seems to use `path` | `path` is not used for Adam weights, but it still affects MNIST/CIFAR mode selection through `util.get_config(...)`. | Leave `path` unset for Adam smokes unless you deliberately want the test-mode data path. |
