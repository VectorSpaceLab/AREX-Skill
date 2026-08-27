# EasyOCR DBNet Workflows

This reference covers the alternative DBNet detector and its DCN operator.

## 1. Runtime detector selection

The public `Reader` surface in this checkout exposes these detector choices:

- `craft` — default detector.
- `dbnet18` — alternative DBNet detector.

Example:

```python
import easyocr

reader = easyocr.Reader(['en'], detect_network='dbnet18')
```

If you only need a CPU smoke for the DBNet package itself, use the direct
constructor with lazy initialization:

```python
from easyocr.DBNet.DBNet import DBNet

obj = DBNet(initialize_model=False, device='cpu', verbose=0)
```

## 2. DBNet constructor surface

The DBNet class is available for lower-level checks with a signature similar to:

```python
DBNet(
    backbone='resnet18',
    weight_dir=None,
    weight_name='pretrained',
    initialize_model=True,
    dynamic_import_relative_path=None,
    device='cuda',
    verbose=0,
)
```

Use the constructor only when you need to inspect the DBNet backend itself or
when you are diagnosing detector startup issues.

## 3. DCN operator compilation

The DCN operator lives under the installed EasyOCR package in
`DBNet/assets/ops/dcn`.

Typical prerequisites:

- CPU build: GCC newer than 4.9.
- CUDA build: GCC newer than 4.9 plus a CUDA toolkit/NVCC install.
- If the installed torch wheel reports CUDA support but the host lacks `nvcc`,
  the build helper will refuse to run until the toolchain is fixed.

Recommended flow:

1. Run `scripts/compile_dcn.py --check-only` to inspect the current artifacts.
2. If the artifacts are missing, run `scripts/compile_dcn.py --build`.
3. Confirm that the expected `deform_conv_*` and `deform_pool_*` shared
   objects exist afterward.

## 4. Runtime expectations

- DBNet follows the device passed to its constructor.
- A device mismatch between the initialized model and the detection call is a
  runtime error.
- The CPU path is supported for import/init smokes and can be used when the
  user only needs to confirm availability.

## 5. When to escalate to troubleshooting

If compilation fails, the operator is missing, or the device mismatch persists,
read `references/troubleshooting.md` and then rerun the bundled helper.
