# Tabular compatibility notes

## Verified modern inspection stack

The following combination was verified during construction and is the best reference for modern smoke checks:
- Python 3.11
- `pandas==1.5.3`
- `scikit-learn==1.1.3`
- `tensorflow==2.15.1`
- `tensorflowjs==4.22.0`
- `keras==2.15.0`
- `tf-keras==2.15.1`
- `keras-preprocessing==1.1.2`
- `keras-tuner==1.4.8`

## Why these versions matter

- `pandas==1.5.3` still works with the bundled compatibility shim but needs the `SettingWithCopyWarning` patch.
- `scikit-learn==1.1.3` still exposes the older `OneHotEncoder.get_feature_names()` behavior used by Libra.
- `tensorflowjs==3.21.0` conflicted with the modern TensorFlow candidate during dry-run exploration.

## Minimal import pattern

Use the bundled shim before importing Libra on modern pandas. When running a one-off snippet, add the root `scripts/` directory to `PYTHONPATH` first so `libra_compat` can be imported:

```bash
PYTHONPATH=skills/disco/libra/scripts python - <<'PY'
from libra_compat import apply
apply()
from libra import client
apply()
PY
```

## Legacy alternative

If you must reproduce the original stack more faithfully, use the older Python 3.8-era environment noted in the root compatibility reference rather than the raw `requirements.txt`.
