# Compatibility and runtime constraints

zi2zi is a legacy research-code repository. Treat dependency and backend
selection as part of the workflow, not as boilerplate.

## Python and package family

The original scripts use Python 2 idioms and TensorFlow 1 APIs:

- `cPickle` and `cStringIO` are imported by the data pipeline.
- `reload(sys)` and `sys.setdefaultencoding("utf-8")` appear in preprocessing.
- `tf.Session`, `tf.app.run`, placeholders, variable scopes, and `tf.contrib`
  are used throughout the model.
- `scipy.misc.imread`, `scipy.misc.imresize`, and `scipy.misc.imsave` are used
  for image I/O and are absent from modern SciPy releases.

Use a legacy environment for original zi2zi scripts. A typical Conda direction
is Python 2.7 with TensorFlow 1.15, NumPy 1.16, SciPy 1.2, Pillow 6.x, and
imageio 2.6-era packages. Prefer a disposable environment over modifying a
user's base or current Python environment.

## TensorFlow and CUDA

The README lists CUDA and cuDNN as requirements for practical training. The
training loop uses TensorFlow sessions and can consume large GPU memory. When
answering user tasks:

- Do not promise TensorFlow 2 compatibility.
- Do not treat a Python import as proof that full CUDA training works.
- Confirm the user has a compatible TensorFlow 1.x GPU build, CUDA/cuDNN stack,
  and free GPU memory before launching training or checkpoint inference.
- On modern GPUs and drivers, old TensorFlow 1.x CUDA 10-era builds may import
  but fail or hang during device initialization. If that happens, prefer a
  legacy-compatible container/environment, hide CUDA for CPU-only graph checks,
  or narrow the task to command planning and data validation.

CPU checks are useful for parser help, data packaging, and static graph
construction, but CPU is not a practical substitute for full GAN training.

## Data and checkpoint prerequisites

- `font2img.py` requires readable source and target font files and a charset
  choice. Built-in choices are `CN`, `CN_T`, `JP`, and `KR`; a one-line custom
  text file can also provide characters.
- `package.py` expects rendered `*.jpg` files whose basename starts with an
  integer label followed by an underscore, for example `0_0000.jpg`.
- `train.py` expects `train.obj` and `val.obj` under the experiment data
  directory.
- `infer.py` and `export.py` expect a TensorFlow checkpoint directory readable
  by `tf.train.get_checkpoint_state`.
- The skill does not bundle fonts, datasets, or checkpoints. Network downloads
  of pretrained models should be explicit user decisions.

## Safe default checks

Safe checks that usually do not require datasets or checkpoints:

```sh
python font2img.py --help
python package.py --help
python train.py --help
python infer.py --help
python export.py --help
```

A more involved but still dataset-free check is a TensorFlow graph construction
with CUDA hidden. This validates imports and graph definitions without starting
training. Use it only in a legacy TensorFlow 1 environment.

## Modernization caveats

If a user asks to modernize the code, separate the maintenance task from normal
zi2zi operation. Known modernization issues include Python 3 pickle/string
handling, replacing `scipy.misc` image functions, TensorFlow 2 eager-mode
incompatibility, `tf.contrib` removal, checkpoint variable compatibility, and
CUDA wheel availability. This skill can identify those surfaces but does not
claim a tested migration path.
