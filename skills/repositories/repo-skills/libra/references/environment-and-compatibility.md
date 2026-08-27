# Environment and compatibility notes

Libra is a legacy TensorFlow/Keras-era project. The declared requirements are not directly reproducible on modern Python without adjustments: `requirements.txt` includes `tensorflow-gpu==2.5.2`, `keras==2.4.3`, unconstrained `tensorflowjs`, `sklearn`, `streamlit==0.64.0`, `altair==4.1.0`, and `keras-tuner`, while the source mixes `tensorflow.keras`, standalone `keras`, `tensorflowjs`, `kerastuner`, old pandas private imports, and old scikit-learn APIs.

## Verified inspection stack

A private inspection environment was prepared with Python 3.11 and these important packages:

- `tensorflow==2.15.1`
- `tensorflowjs==4.22.0`
- `keras==2.15.0`
- `tf-keras==2.15.1`
- `keras-preprocessing==1.1.2`
- `keras-tuner==1.4.8` (provides the `kerastuner` compatibility import used by the repo)
- `pandas==1.5.3`
- `scikit-learn==1.1.3` (keeps `OneHotEncoder.get_feature_names` and `plot_confusion_matrix` available)
- `transformers==4.38.2`
- `xgboost`, `opencv-python`, `prince`, `spacy`, `textblob`, `autocorrect`, `jellyfish`, `nltk`, `matplotlib`, `seaborn`, `colorama`

`pip check` reported no broken requirements in that inspection environment. Direct unshimmed `import libra` still fails on modern pandas because the source does `from pandas.core.common import SettingWithCopyWarning`, which pandas no longer exposes. With `scripts/libra_compat.py` applied around the import, import and client method inspection succeeded.

## Required modern-stack shims

On pandas versions where `pandas.core.common.SettingWithCopyWarning` is absent, patch before importing `libra`. If you will run query methods, apply the warning filter again after import because `libra/queries.py` sets `FutureWarning` to errors during import. When running a one-off snippet, add the bundled `skills/disco/libra/scripts` directory to `PYTHONPATH` or call the helper scripts directly:

```python
from libra_compat import apply
apply()
from libra import client
apply()  # restore FutureWarning suppression after queries.py changed it
```

The FutureWarning filter matters because pandas 1.5 emits a `Series.iteritems()` deprecation warning from Libra's preprocessing path.

Prefer importing `apply()` from bundled `scripts/libra_compat.py` when using this skill's helper scripts.

## Legacy-stack alternative

If a task must test the unmodified repo without shims, a Python 3.8-era environment is more faithful. A plausible starting point is:

- Python 3.8
- `pandas==1.1.5` (contains `pandas.core.common.SettingWithCopyWarning`)
- `scikit-learn==0.24.2` or another pre-removal version with `get_feature_names` and `plot_confusion_matrix`
- `tensorflow==2.5.2`
- `tensorflowjs==3.13.0` (newer TFJS 4.x pulls JAX/TensorFlow-Decision-Forests dependencies that are not compatible with old TensorFlow)
- `keras==2.4.3`, `keras-preprocessing==1.1.2`, `keras-tuner==1.0.4` or another version that provides `kerastuner`

The repository's raw `requirements.txt` should not be installed blindly.

## Backend status

- Host hardware probe: A100 GPUs were visible via `nvidia-smi` during construction.
- TensorFlow probe in the Python 3.11 inspection environment: `tf.config.list_physical_devices('GPU')` returned `[]`; TensorFlow logged missing CUDA libraries.
- Treat CPU workflows as the verified baseline. Treat CUDA/GPU execution for `gpu=True`, heavy image captioning, CNN training, and large transformer workflows as optional and unverified unless the active environment proves TensorFlow sees GPUs.

## Network/download behavior

Libra may download during normal use:

- `client.__init__` calls `nltk.download('punkt')`, `nltk.download('averaged_perceptron_tagger')`, and `nltk.download('stopwords')`.
- TextBlob/POS tagging may need additional NLTK data on newer NLTK releases.
- Summarization, text generation, NER, and image captioning load HuggingFace or TensorFlow/Keras pretrained models.
- `libra.datasets.load` downloads remote dataset archives.

In proxied environments, newer NLTK can refuse downloads with a pathsec SSRF warning. Pre-download corpora from a trusted environment, or set `NLTK_ALLOW_PROXIED_URLOPEN=1` only if the proxy is trusted.
