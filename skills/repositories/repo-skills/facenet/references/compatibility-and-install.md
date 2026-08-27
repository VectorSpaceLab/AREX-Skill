# Compatibility and installation notes

Facenet is an older source-style TensorFlow project. Most confusing failures come from treating it like a modern packaged library.

## Dependency baseline

The repository documents:

- TensorFlow `1.7`
- Python `2.7` and `3.5` CI
- `scipy`, `scikit-learn`, `opencv-python`, `h5py`, `matplotlib`, `Pillow`, `requests`, and `psutil`
- `PYTHONPATH` containing the Facenet source modules, model modules, and alignment modules

For practical inspection on modern systems, a later TensorFlow 1.x build such as `tensorflow==1.15.*` is often easier to obtain and still provides the APIs used by this repo: `tf.Graph`, `tf.Session`, queues, `tf.train`, and `tensorflow.contrib.slim`. Use an isolated environment and a compatible dependency set, for example:

```bash
python -m pip install "tensorflow==1.15.*" "numpy<1.19" "scipy<1.6" "scikit-learn<1" "opencv-python<4.3" "h5py<3" matplotlib Pillow requests psutil "protobuf<3.20"
```

The repository's exact `requirements.txt` pins TensorFlow 1.7 and may require an archived Python 2.7/3.5 environment; do not silently claim that a modern TensorFlow 2.x install is equivalent.

## Import layout

The repo does not define package metadata or console entry points. In a working environment, these imports should succeed:

```bash
python - <<'PY'
import tensorflow as tf
import facenet
import lfw
import align.detect_face
import models.inception_resnet_v1
print(tf.__version__)
print(facenet.prewhiten.__name__)
PY
```

If the imports fail, add the Facenet `src` tree to the module search path for that environment, or use an equivalent source-style install mechanism. For contributed scripts, the `contributed` module directory must also be importable.

## TensorFlow version hazards

- TensorFlow 2.x removes or changes many APIs this repo uses. Disable eager mode and use compatibility APIs only if a task explicitly involves porting; for normal usage prefer a real TF1 environment.
- TensorFlow 1.x can fail with modern `protobuf` packages. If import raises `Descriptors cannot be created directly`, install a compatible `protobuf<3.20` in that environment.
- `tensorflow.contrib.slim` is required by the model definitions. Missing `tf.contrib` means the environment is not suitable for unmodified Facenet training/model construction.

## SciPy image I/O hazards

Several source scripts use removed `scipy.misc` helpers such as `imread`, `imresize`, and `imsave`. Older SciPy releases included them; newer SciPy releases may require patching or replacing these calls with Pillow/OpenCV equivalents when modernizing the repo.

## GPU expectations

CUDA is an accelerator, not a semantic requirement for the selected workflows. CPU can validate imports, parsers, losses, metrics, model graph construction, and tiny examples, but full training and large LFW/pretrained inference are slow on CPU. Only require a CUDA environment when the user explicitly asks for GPU execution or performance.

## Smoke check

Run the bundled checker:

```bash
python scripts/check_facenet_environment.py --json
```

It verifies importability and reports dependency versions without running downloads, training, webcam capture, or full model inference.
