---
name: install-build
description: "Guides Apache TVM source/PyPI installation, CMake/LLVM builds,
  import validation, backend probes, and focused test selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Install and Build TVM

Use this route when the task is to install Apache TVM, configure/build a
checkout, validate which libraries Python loads, or choose the smallest native
test after a change.

## Route

1. Decide whether the task needs the PyPI wheel or a source checkout. Use the
   source path when changing C++/Python code or enabling custom backends.
2. Read [`references/build-and-test.md`](references/build-and-test.md) for the
   build matrix and focused commands.
3. Build with CMake/Ninja and a supported LLVM toolchain. Keep `python/` on
   `PYTHONPATH`; do not use editable TVM/tvm-ffi installs for multi-checkout
   development.
4. Run [`scripts/check_tvm_install.py`](scripts/check_tvm_install.py) before
   broader tests. It reports version, loaded libraries, `libinfo()`, and
   backend readiness without changing the checkout.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) for
   stale imports, missing `tvm-ffi`, LLVM/linker failures, or optional extras.

## Minimal source workflow

```bash
# From a TVM checkout with submodules initialized.
git submodule update --init --recursive
mkdir -p build
cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DTVM_BUILD_PYTHON_MODULE=ON \
  -DUSE_LLVM="llvm-config --ignore-libllvm --link-static" \
  -DUSE_RPC=ON -DUSE_CUDA=OFF
cmake --build build --parallel
export PYTHONPATH="$PWD/python${PYTHONPATH:+:$PYTHONPATH}"
export TVM_LIBRARY_PATH="$PWD/build/lib"
python -c 'import tvm; print(tvm.__version__); print(tvm.support.libinfo())'
```

Adjust `USE_CUDA`, `USE_ROCM`, `USE_VULKAN`, `USE_METAL`, or optional library
flags only after the matching toolkit, headers, driver, and runtime have been
verified. A successful CMake build does not prove a device backend works.

## Boundaries

- Relax module compilation: [`../relax-compile/SKILL.md`](../relax-compile/SKILL.md).
- TIRx authoring and GPU-specific tests: [`../tirx-kernels/SKILL.md`](../tirx-kernels/SKILL.md).
- S-TIR/meta-schedule: [`../s-tir-tuning/SKILL.md`](../s-tir-tuning/SKILL.md).
- RPC service lifecycle and remote execution: [`../rpc-deployment/SKILL.md`](../rpc-deployment/SKILL.md).
