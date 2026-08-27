# PARL backend selection and alias verification

PARL exposes `parl.Model`, `parl.Algorithm`, and `parl.Agent` as aliases for one selected deep-learning backend. Select and verify that backend before building framework code.

## Selection rules

PARL 2.2.1 uses these rules during `import parl`:

1. If `PARL_BACKEND` is set to a non-empty value, it must be exactly one of:
   - `torch`
   - `paddle`
   - `fluid`
2. If `PARL_BACKEND=torch`, PARL requires `torch` to be importable, then exposes Torch core classes.
3. If `PARL_BACKEND=paddle`, PARL imports the Paddle 2.x core classes and therefore requires a compatible `paddle` package.
4. If `PARL_BACKEND=fluid`, PARL imports the legacy Fluid core classes and therefore requires a Paddle release that still provides `paddle.fluid`.
5. If `PARL_BACKEND` is unset, PARL auto-detects installed frameworks and selects the first available backend in this order:
   - Paddle 2.x
   - legacy Fluid
   - Torch
6. If both Paddle and Torch are installed and `PARL_BACKEND` is unset, PARL selects Paddle by default. Set `PARL_BACKEND=torch` before import if the code is Torch-based.

The backend decision happens at import time. Changing `os.environ["PARL_BACKEND"]` after `import parl` does not rebuild aliases already imported in the process.

## Recommended import patterns

Shell process:

```bash
PARL_BACKEND=torch python train_or_check.py
```

Python entry point, before importing PARL or modules that import PARL:

```python
import os
os.environ.setdefault("PARL_BACKEND", "torch")
import parl
```

Notebook or long-running interpreter:

1. Restart the kernel/process.
2. Set `PARL_BACKEND` before the first `import parl`.
3. Re-run alias verification.

## Alias verification

A successful core import should expose all three aliases:

```python
import parl
print(parl.__version__)
print(parl.Model.__module__)
print(parl.Algorithm.__module__)
print(parl.Agent.__module__)
```

Expected module fragments:

| Backend | Expected alias module fragment |
| --- | --- |
| Torch | `parl.core.torch` |
| Paddle 2.x | `parl.core.paddle` |
| legacy Fluid | `parl.core.fluid` |

Use the bundled checker when available:

```bash
python ../scripts/check_parl_core.py --backend torch --torch-smoke auto
```

For Paddle or Fluid, replace the backend argument and omit the Torch smoke if those dependencies are not installed:

```bash
python ../scripts/check_parl_core.py --backend paddle --torch-smoke never
python ../scripts/check_parl_core.py --backend fluid --torch-smoke never
```

## Choosing a backend for new code

| Task shape | Preferred backend | Notes |
| --- | --- | --- |
| PyTorch model subclasses, PyTorch optimizers, `torch.Tensor` data | `torch` | Set `PARL_BACKEND=torch` before import. `parl.Model` is a `torch.nn.Module` subclass. |
| Paddle 2.x dynamic-graph code, `paddle.nn.Layer`, Paddle optimizers | `paddle` | `parl.Model` is a `paddle.nn.Layer` subclass. |
| Legacy static-graph examples that use `paddle.fluid`, `parl.layers`, and `build_program` | `fluid` | Requires a legacy Paddle package with Fluid support. Do not expect this to work with current Paddle-only installs. |
| xparl-only remote-class inspection without core models | Any installed backend, or special advanced core-skip flows | For remote execution details use `../../xparl-distributed/`; most model/algorithm tasks still need one backend. |

## Public verification status

A Torch CPU environment verified that `PARL_BACKEND=torch` resolves `parl.Model`, `parl.Algorithm`, and `parl.Agent` to Torch modules and that a tiny model can synchronize and set weights. Paddle and Fluid are optional dependencies and should be verified in the target environment before claiming runtime success for those backends.
