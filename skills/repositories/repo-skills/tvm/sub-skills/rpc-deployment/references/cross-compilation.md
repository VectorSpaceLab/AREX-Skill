# Cross-Compilation and Remote Execution

## Core flow

TVM RPC separates local compilation from remote execution:

1. Build/install enough TVM runtime on the target device to load and run modules.
2. Compile on the local host with a target matching the remote architecture.
3. Export the compiled artifact, often a `lib.tar` for tutorial-style flows.
4. Connect to the remote via direct RPC server or tracker-managed session.
5. Upload the artifact, load it remotely, create remote tensors, run, and
   optionally measure with `time_evaluator`.

For a local tutorial smoke, `target="llvm"` and `rpc.LocalSession()` avoid
network/device assumptions. For a real Raspberry Pi or ARM board, use a target
triple such as an ARM Linux triple and tune CPU attributes to the board.

## Target checklist

Before compiling, record:

- target kind (`llvm`, `cuda`, `opencl`, etc.),
- target triple and CPU attributes for cross-compiled CPU targets,
- whether the target runtime can load the exported artifact format,
- remote device type (`remote.cpu()`, `remote.cuda()`, OpenCL, etc.),
- toolchain used by `export_library`,
- whether the module contains host code, device code, or both.

A mismatch between local target and remote runtime may appear only after upload
or `load_module`, so keep the compiled artifact and command log.

## Minimal module pattern

```python
import numpy as np
import tvm
from tvm import rpc, te
from tvm.support import utils

n = tvm.runtime.convert(1024)
A = te.placeholder((n,), name="A")
B = te.compute((n,), lambda i: A[i] + 1.0, name="B")
mod = tvm.IRModule.from_expr(te.create_prim_func([A, B]).with_attr("global_symbol", "add_one"))
f = tvm.compile(mod, target="llvm")
temp = utils.tempdir()
path = temp.relpath("lib.tar")
f.export_library(path)
remote = rpc.LocalSession()  # replace with rpc.connect(...) for a real server
remote.upload(path)
f_remote = remote.load_module("lib.tar")
dev = remote.cpu()
a = tvm.runtime.tensor(np.ones(1024, dtype="float32"), dev)
b = tvm.runtime.tensor(np.zeros(1024, dtype="float32"), dev)
f_remote(a, b)
```

## Relationship to other sub-skills

- Relax workflows compile an executable before export; route high-level IR
  import and pipelines to relax-compile.
- S-TIR meta-schedule can use an RPC runner; route runner/service setup here
  and tuning choices back to s-tir-tuning.
- TIRx kernels may be exported and run through RPC after codegen, but backend
  and kernel legality remain tirx-kernels concerns.
