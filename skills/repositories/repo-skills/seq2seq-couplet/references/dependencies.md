# Dependencies

## Purpose

Read this before installing or refreshing the runtime environment. The project
is a TensorFlow 1.15-era repository, so the verified dependency set is older
than a modern TensorFlow/Keras stack and needs a few pins to stay importable.

## Verified baseline

| Component | Verified version | Why it matters |
| --- | --- | --- |
| Python | 3.7.x | The verified runtime stack was built and smoke-tested on Python 3.7. |
| TensorFlow | 1.15.0 | Core model runtime for `model.py` and `seq2seq.py`. |
| Flask | 2.0.3 | HTTP surface used by the inference wrapper. |
| Flask-Cors | 3.0.10 | CORS support for the Flask API wrapper. |
| gevent | 22.10.2 | WSGI server runtime used by the legacy service wrapper. |
| greenlet | 2.0.2 | gevent runtime dependency. |
| numpy | 1.18.5 | TensorFlow 1.15 graph construction is compatible with this older NumPy; newer NumPy 1.20+ can break the beam-search graph. |
| tensorboard | 1.15.0 | Logging/summary support used by the training loop. |
| protobuf | 3.20.3 | Required pin to keep TensorFlow 1.15 importable. |

## Installation guidance

Install the verified runtime set into a private Python 3.7 environment. The
bundled `scripts/install_runtime_deps.py` installs the exact package list that
was verified for this skill, including the protobuf and NumPy compatibility
pins.

If you prefer to install manually, use the same package set and keep the
protobuf pin at `3.20.3` or lower. TensorFlow 1.15 fails during import with
newer protobuf descriptor code. Keep NumPy at `1.18.5` for the bundled smoke
workflows; NumPy 1.20+ can trigger symbolic-tensor conversion errors while
building the TensorFlow 1.15 beam-search graph.

## Legacy GPU note

The original repository also ships a CUDA-oriented container recipe. That path
assumes legacy TensorFlow 1.15 GPU libraries, specifically CUDA 10.0 and cuDNN
7. The bundled skill does not require that stack, and the verified runtime was
CPU-usable even though the TensorFlow wheel itself reported CUDA support.

If you do want GPU acceleration, you need a matching legacy wheel/toolkit
combination and the older CUDA libraries that TensorFlow 1.15 expects. Do not
count a successful CPU import as GPU verification.

## Practical install order

1. Create or activate a Python 3.7 environment.
2. Install the verified package set with `scripts/install_runtime_deps.py`.
3. Run `scripts/check_env.py`.
4. Only after that, run the training or inference smoke scripts.

## Why the extra protobuf pin exists

The training and inference modules import TensorFlow through the `tf.contrib`
and `tf.train` APIs. Without the protobuf pin, TensorFlow 1.15 can fail before
any model code runs with an error that mentions protobuf descriptors being
created directly. The skill treats that as an install-time failure, not a model
bug.
