# Native, Node.js, ASE, and dpdata APIs

This reference helps agents choose a DeePMD-kit integration surface outside direct Python array inference.

## API Selection

| User need | Preferred surface | Why |
| --- | --- | --- |
| C++ application with compatible compiler/runtime | C++ `deepmd::DeepPot` | Fast, natural C++ vectors, full native API surface. |
| Stable ABI boundary or non-C++ host | C ABI | Avoids C++ compiler ABI sensitivity. |
| C++ ergonomics with C ABI stability | Header-only C++ wrapper | Wraps the C API with C++ containers. |
| JavaScript caller | Node.js package | Exposes native wrapper to Node code. |
| ASE workflow | `deepmd.calculator.DP` | Acts as an ASE calculator for `Atoms`. |
| dpdata workflow | dpdata driver `dp` | Adds predicted energies, forces, and virials to dpdata systems. |

For Python `DeepPot.eval`, `eval_descriptor`, and `calc_model_devi` array work, route to the inference-model-ops sibling sub-skill instead.

## C++ `DeepPot`

Minimal C++ inference pattern:

```cpp
#include "deepmd/DeepPot.h"

int main() {
  deepmd::DeepPot dp("graph.pb");
  std::vector<double> coord = {1.0, 0.0, 0.0, 0.0, 0.0, 1.5, 1.0, 0.0, 3.0};
  std::vector<double> cell = {10.0, 0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 10.0};
  std::vector<int> atype = {1, 0, 1};
  double energy = 0.0;
  std::vector<double> force;
  std::vector<double> virial;
  dp.compute(energy, force, virial, coord, atype, cell);
}
```

Compile pattern:

```bash
g++ infer_water.cpp \
  -I${DEEPMD_ROOT}/include \
  -L${DEEPMD_ROOT}/lib \
  -L${BACKEND_ROOT}/lib \
  -Wl,--no-as-needed \
  -ldeepmd_cc -lstdc++ -ltensorflow_cc \
  -Wl,-rpath=${DEEPMD_ROOT}/lib \
  -Wl,-rpath=${BACKEND_ROOT}/lib \
  -o infer_water
```

Adjust backend libraries for the model/backend in use. If linking succeeds but runtime loading fails, inspect shared-library search paths rather than changing the model inputs first.

## C ABI

Minimal C inference pattern:

```c
#include <stdio.h>
#include <stdlib.h>
#include "deepmd/c_api.h"

int main() {
  const char *model = "graph.pb";
  double coord[] = {1.0, 0.0, 0.0, 0.0, 0.0, 1.5, 1.0, 0.0, 3.0};
  double cell[] = {10.0, 0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 10.0};
  int atype[] = {1, 0, 1};
  double energy = 0.0;
  double force[9];
  double virial[9];
  double atom_energy[3];
  double atom_virial[27];
  DP_DeepPot *dp = DP_NewDeepPot(model);
  DP_DeepPotCompute(dp, 3, coord, atype, cell, &energy, force, virial, atom_energy, atom_virial);
  printf("energy: %f\n", energy);
  DP_DeleteDeepPot(dp);
}
```

Compile pattern:

```bash
gcc infer_water.c \
  -I${DEEPMD_ROOT}/include \
  -L${DEEPMD_ROOT}/lib \
  -L${BACKEND_ROOT}/lib \
  -Wl,--no-as-needed \
  -ldeepmd_c \
  -Wl,-rpath=${DEEPMD_ROOT}/lib \
  -Wl,-rpath=${BACKEND_ROOT}/lib \
  -o infer_water
```

Use the C ABI when packaging a library for users who may have different C++ compilers.

## Header-Only C++ Wrapper

The header-only interface includes `deepmd/deepmd.hpp` and is built on the C ABI:

```cpp
#include "deepmd/deepmd.hpp"

int main() {
  deepmd::hpp::DeepPot dp("graph.pb");
  std::vector<double> coord = {1.0, 0.0, 0.0, 0.0, 0.0, 1.5, 1.0, 0.0, 3.0};
  std::vector<double> cell = {10.0, 0.0, 0.0, 0.0, 10.0, 0.0, 0.0, 0.0, 10.0};
  std::vector<int> atype = {1, 0, 1};
  double energy = 0.0;
  std::vector<double> force;
  std::vector<double> virial;
  dp.compute(energy, force, virial, coord, atype, cell);
}
```

Compile against `-ldeepmd_c` rather than `-ldeepmd_cc`.

Custom neighbor-list calls use `InputNlist`, `convert_nlist`, and overloads that pass the neighbor list into `compute`. Use that path when the host code already owns neighbor-list construction, such as in MD engine coupling.

## Model Deviation and Advanced Inputs in Native Code

Native C++ tests cover:

- `DeepPotModelDevi` and `DeepSpinModelDevi` for model deviation.
- `fparam` and `aparam` arrays for frame and atom parameters.
- Mixed-type and multi-frame calls.
- Custom neighbor lists for host-code integration.
- Charge/spin-aware overloads for PyTorch and PyTorch-exportable backends.

When debugging advanced native calls, check these invariants first:

- Coordinate arrays are flat `natoms * 3` or `nframes * natoms * 3` values.
- Cell arrays are flat `9` or `nframes * 9` values.
- Atom type indexes match the model's training type map, not necessarily LAMMPS one-based type IDs.
- `fparam`, `aparam`, and `charge_spin` lengths match model metadata.
- Empty `charge_spin` only works when the model stores a default charge/spin vector.

## Node.js Interface

Node.js uses the installed `deepmd-kit` package and native vector wrapper classes:

```js
const deepmd = require("deepmd-kit");

const dp = new deepmd.DeepPot("graph.pb");
const coord = [1, 0, 0, 0, 0, 1.5, 1, 0, 3];
const atype = [1, 0, 1];
const cell = [10, 0, 0, 0, 10, 0, 0, 0, 10];

const vCoord = new deepmd.vectord(coord.length);
const vAtype = new deepmd.vectori(atype.length);
const vCell = new deepmd.vectord(cell.length);
for (let i = 0; i < coord.length; i++) vCoord.set(i, coord[i]);
for (let i = 0; i < atype.length; i++) vAtype.set(i, atype[i]);
for (let i = 0; i < cell.length; i++) vCell.set(i, cell[i]);

let energy = 0.0;
const forces = new deepmd.vectord();
const virials = new deepmd.vectord();
energy = dp.compute(energy, forces, virials, vCoord, vAtype, vCell);
console.log("energy:", energy);
```

Build-source notes:

- Node.js, SWIG, and `node-gyp` are required for source builds.
- CMake must enable the Node.js interface and know the Node.js include directory.
- After the CMake install generates Node wrapper artifacts, install/link the package from the Node.js source directory.

## ASE Calculator

ASE integration uses `deepmd.calculator.DP`:

```python
from ase import Atoms
from deepmd.calculator import DP

water = Atoms(
    "H2O",
    positions=[(0.7601, 1.9270, 1.0), (1.9575, 1.0, 1.0), (1.0, 1.0, 1.0)],
    cell=[100, 100, 100],
    calculator=DP(model="frozen_model.pb"),
)
print(water.get_potential_energy())
print(water.get_forces())
```

Use the appropriate model artifact for the backend, for example TensorFlow `.pb`, PyTorch `.pth`, or Paddle JSON when available.

## dpdata Driver

DeePMD-kit registers a dpdata driver named `dp`:

```python
import dpdata

dsys = dpdata.LabeledSystem("OUTCAR")
dp_sys = dsys.predict("frozen_model_compressed.pb", driver="dp")
```

The predicted system contains inferred energies, forces, and virials. Use this when converting or labeling datasets inside dpdata workflows.

## Debugging Native Integrations

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Header not found | DeePMD include directory missing | Add the installed include directory to compiler flags. |
| `-ldeepmd_c` or `-ldeepmd_cc` not found | Library directory missing | Add the installed library directory to link flags. |
| Program links but cannot load shared library | Runtime path missing | Add an rpath or set the runtime library search path for DeePMD and backend libraries. |
| Backend not built error | Model backend unavailable in the native build | Rebuild/install with the backend needed by the model. |
| Charge/spin length error | Runtime `charge_spin` vector length does not match metadata | Pass exactly one frame's charge/spin length or per-frame values as required. |
| Wrong energies or type-related errors | Atom type indexes mismatch | Reconcile zero-based DeePMD type indexes, model type map, and any one-based engine type IDs. |
| Node `require` fails | Node wrapper not installed or linked | Install the package or build the Node wrapper with the matching native libraries. |
