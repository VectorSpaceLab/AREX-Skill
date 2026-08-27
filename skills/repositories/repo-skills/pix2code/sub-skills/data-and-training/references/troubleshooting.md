# Data and Training Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AssertionError` or mismatched counts during split | The distribution does not divide the number of paired samples into an integer training/eval split. | Choose a distribution that yields an integral sample count or adjust the fixture size. |
| Missing `.png` or `.npz` siblings | Basenames are unpaired. | Add the missing image or DSL file before validation or conversion. |
| `opencv-python` import failure | The environment lacks a compatible OpenCV wheel. | Install a nearby compatible wheel or use Conda's OpenCV package. Record the substitution. |
| `tensorflow` / `keras` import failure | The legacy TensorFlow/Keras stack is absent or shadowed by a modern one. | Use the legacy inspection environment and avoid claiming training verification until the import succeeds. |
| Training appears to hang or consume too much memory | Full in-memory training is too large for the host. | Switch to generator mode and use the preprocessed `.npz` path. |
| Original `build_datasets.py` fails with Python 3 division issues | The historical script was written for older Python semantics. | Use the bundled helper, which validates counts explicitly and uses modern integer-safe logic. |
