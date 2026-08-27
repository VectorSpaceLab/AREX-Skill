# Custom PyRegion regions

Use this reference when a user asks to create a custom region, wrap a simple transformation inside a NuPIC Network, or debug `Network.registerRegion(...)` / `py.<ClassName>` registration. The examples are self-contained templates for the user's project code; they do not depend on any source checkout example files.

Custom regions are part of the legacy Network API surface and therefore require a Python 2.7-compatible NuPIC runtime with `nupic.bindings`. If imports fail before your custom code is reached, see [`troubleshooting.md`](troubleshooting.md) and the root install/import guide at [`../../../references/troubleshooting.md`](../../../references/troubleshooting.md).

## Minimal identity region skeleton

Create an importable Python module in the user's project, for example `my_regions/identity_region.py` with an `__init__.py` next to it. Keep the module importable in the same Python process that constructs the Network.

```python
from __future__ import division

from nupic.bindings.regions.PyRegion import PyRegion


class IdentityRegion(PyRegion):
  """Copy a Real32 input vector to a Real32 output vector."""

  def __init__(self, dataWidth, gain=1.0):
    dataWidth = int(dataWidth)
    if dataWidth <= 0:
      raise ValueError("dataWidth must be > 0")
    self.dataWidth = dataWidth
    self.gain = float(gain)

  def initialize(self):
    """Called once during network.initialize()."""
    pass

  def compute(self, inputs, outputs):
    """Called once per Network iteration."""
    outputs["out"][:] = inputs["in"] * self.gain

  @classmethod
  def getSpec(cls):
    return {
      "description": cls.__doc__,
      "singleNodeOnly": True,
      "inputs": {
        "in": {
          "description": "Input vector.",
          "dataType": "Real32",
          "count": 0,
          "required": True,
          "regionLevel": False,
          "isDefaultInput": True,
          "requireSplitterMap": False,
        },
      },
      "outputs": {
        "out": {
          "description": "Output vector.",
          "dataType": "Real32",
          "count": 0,
          "regionLevel": True,
          "isDefaultOutput": True,
        },
      },
      "parameters": {
        "dataWidth": {
          "description": "Number of Real32 elements in output 'out'.",
          "dataType": "UInt32",
          "count": 1,
          "constraints": "",
          "accessMode": "Read",
        },
        "gain": {
          "description": "Multiplier applied during compute.",
          "dataType": "Real32",
          "count": 1,
          "constraints": "",
          "accessMode": "ReadWrite",
        },
      },
      "commands": {},
    }

  def getOutputElementCount(self, name):
    if name == "out":
      return self.dataWidth
    raise Exception("Unrecognized output: " + name)
```

Why each method exists:

- `__init__`: receives JSON-decoded create parameters from `network.addRegion(...)`. Validate types and sizes here.
- `initialize`: runs after links and buffers are prepared. Use it for setup that needs final dimensions or dependencies.
- `compute(inputs, outputs)`: reads named input arrays and writes named output arrays every `network.run(...)` iteration.
- `getSpec`: declares inputs, outputs, parameters, commands, default input/output flags, and data types used by the engine.
- `getOutputElementCount`: returns dynamic output width when a spec output has `count: 0`.

## Register and link the custom region

```python
import json
from nupic.engine import Network
from my_regions.identity_region import IdentityRegion

network = Network()
Network.registerRegion(IdentityRegion)

network.addRegion("identity", "py.IdentityRegion", json.dumps({
  "dataWidth": 128,
  "gain": 1.0,
}))
```

When linking after a `RecordSensor`, set `dataWidth` to the encoder width:

```python
sensorImpl = network.regions["sensor"].getSelf()
width = sensorImpl.encoder.getWidth()

Network.registerRegion(IdentityRegion)
network.addRegion("identity", "py.IdentityRegion", json.dumps({
  "dataWidth": width,
}))
network.link("sensor", "identity", "UniformLink", "",
             srcOutput="dataOut", destInput="in")
network.initialize()
network.run(1)
copy = network.regions["identity"].getOutputData("out")
```

If the custom region is inserted between SP and TM, link `SP.bottomUpOut -> identity.in` and `identity.out -> TM.bottomUpIn`, and set `dataWidth` to the SP output width/column count. For SP/TM parameter meaning, use [`../../htm-algorithms/`](../../htm-algorithms/).

## Spec field rules

| Spec field | Rule |
|---|---|
| `singleNodeOnly` | Use `True` for normal Python regions unless implementing old multi-node behavior intentionally. |
| `inputs` / `outputs` keys | These are the exact `srcOutput`/`destInput` names used by `network.link(...)`. Keep them short and stable. |
| `dataType` | Both sides of a link must match. `Real32` is the common SDR buffer type for Network examples. |
| `count` | Use fixed positive counts when known; use `0` plus `getOutputElementCount()` for dynamic outputs. |
| `required` | Required inputs must have links before `network.initialize()`. Optional inputs can be omitted. |
| `isDefaultInput` / `isDefaultOutput` | Default endpoints are used when `network.link(...)` omits explicit endpoint names. Still prefer explicit names while debugging. |
| `parameters` | Exposed via `region.getParameter(...)` and `region.setParameter(...)` according to `accessMode` and `dataType`. |

## Validation checklist

1. The class imports in the same Python process that constructs the Network.
2. `Network.registerRegion(IdentityRegion)` is called before `network.addRegion(..., "py.IdentityRegion", ...)`.
3. Constructor JSON contains every required `__init__` argument and values are already valid Python scalar types after JSON decoding.
4. `getSpec()` input/output names match the exact `srcOutput`/`destInput` names in `network.link(...)`.
5. For dynamic outputs, `getOutputElementCount("out")` returns a positive integer before `network.initialize()` allocates buffers.
6. `compute()` fills every output buffer it owns; do not leave stale values from a previous run unless that is intentional state.
7. If the region has mutable parameters, test `region.setParameter("gain", 2.0)` before `network.initialize()` and after initialization if the design allows runtime changes.

## Registration and import pitfalls

- The region type string is `py.<ClassName>`, not the module path. For `class IdentityRegion`, use `"py.IdentityRegion"`.
- Registration stores module and class name in the engine. The class must remain importable by that module name for serialization/reload and for future processes.
- If two custom classes share the same class name, registration can become ambiguous. Prefer unique class names per project or unregister stale test classes when appropriate with `Network.unregisterRegion("IdentityRegion")`.
- Do not append private checkout paths into reusable skill files. In user code, make the module importable through the user's normal package layout or a documented project-local `PYTHONPATH` choice.

## Serialization safety

Network bundles containing Python regions can include pickled Python state. Treat them as unsafe unless produced and consumed by trusted code in a controlled environment. Do not load a bundle from an untrusted source. For portable reproducibility, prefer a plain Python graph-construction function plus explicit parameters/data over sharing pickled Network bundles.

## Evidence provenance

This template distills the legacy custom identity-region pattern, `nupic.engine.Network.registerRegion`, and the `PyRegion` spec contract from NuPIC Network examples and region implementations. The skeleton above is intentionally self-contained for future agents and users.
