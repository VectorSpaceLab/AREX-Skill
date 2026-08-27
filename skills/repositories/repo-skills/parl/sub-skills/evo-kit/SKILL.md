---
name: evo-kit
description: "Build, inspect, and safely use PARL EvoKit, the optional C++
  evolution-strategy toolkit with Torch or PaddleLite prediction backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PARL EvoKit

Use this sub-skill when a task involves PARL's optional C++ EvoKit toolkit: `ESAgent` sampling/update loops, `SamplingInfo` records, C++ build prerequisites, Torch/libtorch versus PaddleLite backend selection, or safe interpretation of EvoKit build helpers.

Do not use this sub-skill for ordinary Python PARL `Model` / `Algorithm` / `Agent` code, xparl cluster orchestration, or selecting a full Python RL recipe. For high-level RL recipe structure, consult the sibling `algorithm-recipes` skill conceptually; EvoKit-specific work here is C++ ES toolkit work.

## Operating workflow

1. **Confirm EvoKit is actually needed.** EvoKit is a C++ evolution-strategy toolkit for parameter perturbation, evaluation, and parameter updates. If the task only asks for a Python PARL algorithm, stay with the Python PARL skills instead.
2. **Choose one prediction backend.** Use Torch when the model is a C++ `torch::nn::Module` and a local `libtorch/` tree is available. Use PaddleLite when the model is an exported Paddle inference model and a local `inference_lite_lib/` tree is available. Do not enable both backends in one EvoKit build.
3. **Check local prerequisites before building.** Run the bundled checker from a repository checkout or a copied EvoKit tree:

   ```bash
   python scripts/check_evokit_prereqs.py --project-root <evokit-root> --backend torch
   ```

   Replace `torch` with `paddle` when using PaddleLite, or use `auto` to accept either backend directory.
4. **Model the ESAgent loop explicitly.** The original agent owns the current parameters, sampling method, and optimizer. Clone sampling agents, call `add_noise` only on clones, evaluate each noisy clone, keep each `SamplingInfo` paired with its reward, then call `update` on the original agent. The update reconstructs perturbations from `SamplingInfo` keys and applies the optimizer to the original parameters.
5. **Handle online/offline runs as data contracts.** Online sampling should persist `SamplingInfo` plus reward records in the same order used for offline update. Offline update should reload the current model/solver state, parse the records, call `update`, and save the next model/solver state.
6. **Avoid unsafe build shortcuts by default.** Treat upstream shell helpers as examples only: they may remove build directories, install into the source tree, unzip bundled data, download libtorch, and run demos. Prefer an explicit local prerequisite check and a controlled manual CMake build in a disposable checkout or dedicated build directory.
7. **Escalate by symptom.** Use `references/build-and-api.md` for API/build planning and `references/troubleshooting.md` for protobuf, backend library, CMake, gflags/glog/OpenMP, and ESAgent misuse errors.

## Verification status

This sub-skill is source-evidence backed. The bundled checker was written to inspect local prerequisites without downloads or builds. EvoKit itself was not fully compiled during skill construction because the optional C++ backend libraries are environment-specific.

## Reference map

- `references/build-and-api.md` — distilled EvoKit C++ API concepts, config schema, Torch/PaddleLite choices, and safe build outline.
- `references/troubleshooting.md` — fixes and safety notes for protobuf/protoc, backend libraries, gflags/glog/OpenMP, build helper side effects, CMake cleanup, and ESAgent loop mistakes.
- `scripts/check_evokit_prereqs.py` — deterministic local prerequisite checker; it prints missing items and never downloads, builds, deletes, or writes project files.
