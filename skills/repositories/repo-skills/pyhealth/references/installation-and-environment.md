# Installation and environment

Read this before installing PyHealth or deciding whether a workflow is safe to
run. The generated skill is public guidance; do not copy local environment
paths into experiments or reports.

## Supported baseline

PyHealth 2.0.1 declares Python `>=3.12,<3.14` and depends on PyTorch,
torchvision, Transformers, PEFT, Accelerate, RDKit, OGB, scikit-learn, MNE,
NumPy, pandas/Polars, PyArrow, Dask, LitData, Pydantic, and related utilities.
The smallest useful package install is:

```bash
python -m pip install pyhealth
```

Optional groups are deliberately separate:

```bash
python -m pip install 'pyhealth[graph]'  # torch-geometric
python -m pip install 'pyhealth[nlp]'    # rapidfuzz, rouge_score, nltk
```

The project also documents pixi environments for development. Use the public
package install for a Researcher workflow unless a reproducible checkout-level
build is specifically requested.

## Device choice

`Trainer(model, device=None)` selects CUDA when `torch.cuda.is_available()` is
true and otherwise uses CPU. For deterministic routing, pass `device="cpu"` or
`device="cuda"` explicitly and check the result before training. A CUDA
workflow needs a matching PyTorch wheel, driver, and enough VRAM; a CPU smoke
is not evidence that a CUDA model path works. MPS/ROCm are not required by the
core package route and need independent PyTorch validation.

Safe probes:

```python
import torch
print(torch.__version__, torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
```

## Data and model resources

Dataset classes accept local roots and, for selected synthetic/public examples,
URLs. A successful constructor is not proof that a dataset is licensed,
complete, de-identified, or available to the user. Pretrained Transformers,
OpenAI, medical-code mapping caches, and NLTK resources may fetch external
artifacts. Separate package import, local schema validation, and resource
acquisition into different steps.

Before a real run, record: source/version and license; local root; expected
files/tables; credentials/DUA status; cache destination; patient split policy;
model weights; device; output/checkpoint directory; and a bounded stop condition.
