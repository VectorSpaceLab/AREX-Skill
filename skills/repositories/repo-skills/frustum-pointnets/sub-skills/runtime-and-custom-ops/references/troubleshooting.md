# Runtime troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: tensorflow` | wrong environment or package not installed | invoke the selected environment's Python, then run `python -m pip check` and the bundled diagnostic |
| `Descriptors cannot be created directly` | protobuf too new for TensorFlow 1.x generated protos | use a compatible protobuf (3.20.x or older for this baseline), then re-run import; do not edit generated protos first |
| `AttributeError: module tensorflow has no attribute contrib` | TensorFlow 2.x | use TensorFlow 1.x or perform a deliberate `tf.compat.v1` port; this repository is not automatically TF2-compatible |
| `No module named cPickle` | unpatched Python-2 import under Python 3 | apply the local `try/except ImportError` compatibility patch and record that the run is a patched port |
| custom wrapper cannot find `*_so.so` | operator has not been built or is in another directory | build the matching operator in an isolated environment and check the wrapper's sibling path |
| `.so` has undefined TensorFlow/CUDA symbols | wheel, CUDA, compiler, or C++ ABI mismatch | rebuild from the selected environment's discovered headers/libs; do not copy the historical absolute paths |
| GPU is listed by `nvidia-smi` but TensorFlow lists no GPU | missing/incompatible CUDA libraries or device visibility | inspect TensorFlow's startup log and library paths; CPU success does not clear the CUDA gate |
| Mayavi import/display fails over SSH | optional GUI backend unavailable | omit visualization, use a local GUI session, or use saved point-cloud artifacts; do not make it a core dependency |

Do not “fix” an old environment by globally upgrading TensorFlow, NumPy, or
protobuf. Create a separate prefix and preserve the exact versions used by a
successful check.
