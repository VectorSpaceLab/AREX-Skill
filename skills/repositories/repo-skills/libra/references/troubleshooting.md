# Libra troubleshooting

## Import fails: `SettingWithCopyWarning`

Symptom:

```text
ImportError: cannot import name 'SettingWithCopyWarning' from 'pandas.core.common'
```

Cause: Libra imports a pandas private symbol that was removed from `pandas.core.common`.

Fix on modern pandas. When running a one-off snippet, add `skills/disco/libra/scripts` to `PYTHONPATH` or use one of the bundled helper scripts directly:

```python
from libra_compat import apply
apply()

from libra import client
apply()  # queries.py resets FutureWarning handling during import
```

Or manually:

```python
import pandas.core.common as common
from pandas.errors import SettingWithCopyWarning
common.SettingWithCopyWarning = SettingWithCopyWarning
import warnings
warnings.simplefilter("ignore", FutureWarning)
```

If strict unmodified import is required, use an older Python 3.8/pandas stack instead of modern pandas.

## FutureWarning aborts during preprocessing

Libra configures `warnings.simplefilter(action='error', category=FutureWarning)` in `queries.py`. Pandas 1.5 emits a deprecation warning for `data.dtypes.iteritems()`, which then becomes an exception. Apply the warning shim in `scripts/libra_compat.py` after importing Libra and before running queries, or use older pandas.

## NLTK download blocked by proxy/pathsec

Symptom:

```text
Security Violation [pathsec.urlopen]: refusing a proxied fetch ...
```

`client.__init__` tries to download NLTK corpora. In automated checks that do not need NLP corpora, you can monkey-patch the method before constructing clients:

```python
from libra_compat import apply
apply()
from libra import client
apply()
client.required_installations = lambda self: None
```

For real NLP usage, pre-download `punkt`, `averaged_perceptron_tagger`, `averaged_perceptron_tagger_eng`, `stopwords`, and `wordnet`, or set `NLTK_ALLOW_PROXIED_URLOPEN=1` only in a trusted proxy environment.

## TensorFlowJS import errors

The repo imports `tensorflowjs` at module import time through `feedforward_nn.py`. Common incompatibilities:

- `tensorflowjs==3.21.0` conflicts with modern TensorFlow because it pins old protobuf.
- `tensorflowjs==4.12.0` can fail importing `shape_poly` with newer JAX.
- `tensorflowjs==4.22.0` imported successfully in the modern inspection environment with TensorFlow 2.15.1 and JAX 0.4.34.
- For a TensorFlow 2.5-era stack, `tensorflowjs==3.13.0` was the compatible dry-run candidate.

Do not leave `tensorflowjs` unpinned when preparing a fresh environment.

## TensorFlow sees no GPU

A host can show GPUs in `nvidia-smi` while TensorFlow reports no GPU because CUDA runtime libraries are absent or mismatched. Check:

```python
import tensorflow as tf
print(tf.config.list_physical_devices('GPU'))
```

If this returns `[]`, keep `gpu=False`, use tiny CPU smoke tests, and mark GPU-specific claims unverified.

## Target column detection is wrong

Libra extracts target words from the instruction and then picks the dataset column with minimum Levenshtein distance. Make the instruction look like the target column:

- Better: `predict ocean proximity`
- Better when columns use underscores: `predict ocean_proximity`
- Risky: `tell me which neighborhoods are near the water`

For NLP/image workflows, use explicit `label_column` or `image_column` when available.

## Save/export side effects

Watch these side effects before running on valuable directories:

- `regression_query_ann` defaults `save_model=True` and writes `model*.json`/`weights*.h5` to `save_path` unless disabled. On modern Keras this default can fail after training with a `Layer ModuleWrapper ... must override get_config()` serialization error; pass `save_model=False` for smoke tests and non-save workflows.
- `convolutional_query` creates or removes `proc_training_set` and `proc_testing_set` when preprocessing images.
- `convolutional_query(save_as_tfjs=True)` writes `tfjsmodel` in the current working directory; `save_as_tflite=True` writes `model.tflite`.
- `gan_query` creates `proc_training_set` and writes generated images under `generated_images` relative to the data path.
- `tune()` writes Keras Tuner directories such as `my_dir` unless changed.
- `plots(..., save=True)` writes PNG files in the current directory.
- `dashboard()` launches `streamlit run` and the source hardcodes `/libra/dashboard/LibEDA.py`, which may not exist outside the original container layout.

Prefer temporary output directories for smoke tests.
