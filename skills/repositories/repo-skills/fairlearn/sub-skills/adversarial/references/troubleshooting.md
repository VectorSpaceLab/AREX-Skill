# Adversarial troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| RuntimeError says to install `torch`, `tensorflow`, or `torch or tensorflow` | No selected backend is importable. | Install the backend explicitly or switch to an installed backend. Run root `scripts/check_install.py --include-optional`. |
| `ValueError: Cuda is not available` | `cuda` was requested but PyTorch cannot see CUDA. | Use CPU (`cuda=None`) or fix the CUDA/PyTorch environment; verify with `torch.cuda.is_available()`. |
| `Expected 'X' to be a two-dimensional array` | `X` is an image/text tensor or nested data with rank other than 2. | Flatten or featurize inputs into a 2D numeric matrix before `fit`. |
| Unknown activation string error | List model builder received an unsupported activation keyword. | Use supported strings such as `relu`, `leaky_relu`, `sigmoid`, `softmax`, `tanh`, `gelu`, `elu`, or `selu`, or pass activation instances. |
| Error about list model with non-keyword loss | A list model was paired with a callable/custom loss that prevents shape/activation inference. | Use explicit backend-native model objects or use auto-inferred loss strings. |
| PyTorch BCE error about target/input range | Custom binary model outputs are not in `[0, 1]`. | Add a final `torch.nn.Sigmoid()` to binary predictor/adversary outputs or use the list model builder. |
| Callback error says returned non-boolean | Callback returned a metric, array, or `None` unexpectedly. | Return `True` to stop or `False` to continue. |
| Training collapses to one prediction class | Adversarial mode collapse, high learning rate, too strong adversary, or poor preprocessing. | Lower learning rate, use one hidden layer, add validation callbacks, tune `alpha`, and check input scaling. |
| Equalized-odds model shape mismatch | Adversary input for equalized odds includes true labels as well as predictor output. | Use Fairlearn's list builder or define explicit adversary input shape accordingly. |
| User wants tabular sklearn mitigation, not neural models | Wrong mitigation family. | Route to `../reductions/` or `../postprocessing/`. |

## Minimal PyTorch diagnostic

```python
import torch
print(torch.__version__)
print(torch.cuda.is_available())
from fairlearn.adversarial import AdversarialFairnessClassifier
```

Then run:

```bash
python sub-skills/adversarial/scripts/smoke_torch_adversarial.py
```

Add `--cuda cuda:0` only after the CPU smoke passes and CUDA is available.
