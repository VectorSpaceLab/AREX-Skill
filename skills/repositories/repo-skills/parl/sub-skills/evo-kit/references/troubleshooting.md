# EvoKit troubleshooting

Use this guide when an EvoKit build, prerequisite check, or ESAgent integration fails. Prefer local inspection and minimal reproductions; do not run build helpers blindly.

## Protobuf2 and `protoc`

Symptoms:

- `protoc: command not found`.
- Missing generated files such as `evo_kit.pb.h` or `evo_kit.pb.cc`.
- Compile or link errors involving protobuf symbols.
- Runtime parse failures for serialized `SamplingInfo` records.

Actions:

1. Install or load a local `protoc` and protobuf C++ development runtime compatible with each other.
2. Remember that EvoKit's schema uses `syntax = "proto2"`; do not rewrite it as proto3 to silence tooling warnings.
3. Regenerate the C++ protobuf sources before compiling if generated files are absent or stale.
4. Ensure the compiler include path contains the generated protobuf header directory and the linker sees the matching protobuf library.
5. For offline logs, validate serialized message lengths before reading into fixed buffers and preserve `(reward, SamplingInfo)` ordering.

## Backend flag selection

Symptoms:

- CMake prints that at least one framework should be selected.
- CMake prints that more than one framework cannot be selected.
- Headers compile but backend-specific symbols are missing later.

Actions:

- Choose exactly one backend per build:
  - Torch: configure with `WITH_TORCH` enabled.
  - PaddleLite: configure with `WITH_PADDLE` enabled.
- Do not combine Torch and PaddleLite in a single EvoKit target.
- If both backends are needed for comparison, use separate clean build directories or separate checkouts.

## Missing `libtorch/` or `inference_lite_lib/`

Symptoms:

- Torch demo CMake cannot find Torch.
- PaddleLite headers such as `paddle_api.h` are missing.
- Linker errors reference Torch, PaddleLite, MKLML, or backend shared libraries.

Actions:

- For Torch, provide a local `libtorch/` tree matching the compiler ABI and C++ standard library expected by the project.
- For PaddleLite, provide a local `inference_lite_lib/` tree with C++ include and library subdirectories.
- Check the intended root with:

  ```bash
  python ../scripts/check_evokit_prereqs.py --project-root <evokit-root> --backend torch
  ```

  or:

  ```bash
  python ../scripts/check_evokit_prereqs.py --project-root <evokit-root> --backend paddle
  ```

- Do not let a build helper download backend libraries unless the user explicitly asked for that and accepts the network and disk side effects.

## `gflags`, `glog`, pthread, and OpenMP

Symptoms:

- Linker errors mention `gflags`, `glog`, or protobuf.
- Compile errors mention `omp.h`.
- Parallel code compiles but OpenMP pragmas are ignored or runtime behavior is unexpectedly serial.

Actions:

1. Install or expose local development packages for `gflags`, `glog`, protobuf, and pthread support.
2. Use a compiler/runtime pair with OpenMP support when running the parallel CartPole-style loop.
3. If OpenMP is unavailable, first reduce the ES loop to serial evaluation. Serial evaluation preserves the same `SamplingInfo`/reward/update contract and is easier to debug.
4. Keep optimizer and sampling failures separate from compiler dependency failures; verify that a tiny compile/link target can include `glog/logging.h`, `gflags/gflags.h`, and `omp.h` before debugging ES logic.

## Unsafe build helper side effects

The upstream shell helpers are examples, not safe default validation commands.

Observed helper side effects include:

- running another helper automatically;
- deleting a hard-coded `build` directory;
- generating protobuf sources in-place;
- invoking CMake and `make install` into a source-tree-local output directory;
- unzipping bundled model data;
- downloading libtorch when it is absent;
- copying installed libraries into a demo directory;
- building with a fixed high job count;
- running a demo executable after building.

Safer approach:

1. Run the bundled prerequisite checker first.
2. Work in a disposable checkout or clean copy.
3. Choose a controlled build directory and job count.
4. Disable network access and downloads unless explicitly requested.
5. Build the library before building or running demos.
6. Record only concise status, missing dependencies, and chosen backend in user-facing notes.

## CMake build directory cleanup

Symptoms:

- Reconfiguring from Torch to PaddleLite reuses stale CMake cache values.
- A helper deletes an unexpected `build` directory.
- Installed headers/libraries under a source-tree-local output directory do not match the current backend.

Actions:

- Prefer backend-specific build directories such as `build-torch` and `build-paddle`.
- Remove only directories you created for this build; never issue broad deletes from an uncertain working directory.
- If a helper hard-codes `build`, inspect the current directory before allowing any cleanup.
- If switching backends, clear the CMake cache and regenerate protobuf outputs deliberately.

## ESAgent loop mistakes

Symptoms:

- Logs say the original agent cannot call `add_noise`.
- Logs say a cloned agent cannot call `update`.
- Rewards improve inconsistently or offline update is unstable.
- Parameter-size warnings appear during optimizer updates.

Actions:

- Call `clone()` on the original agent before sampling.
- Call `add_noise(SamplingInfo&)` on each clone.
- Evaluate the noisy clone, not the original agent.
- Call `update(noisy_infos, rewards)` on the original agent only.
- Ensure every reward corresponds to the same index as its `SamplingInfo`.
- Do not reuse stale `SamplingInfo` against a different model iteration unless using the asynchronous flow that records `model_iter_id`.
- Recreate the same model architecture and parameter names before loading or updating saved state.

## Choosing Torch vs PaddleLite

Choose Torch when:

- the model is implemented as a C++ Torch module;
- a compatible local `libtorch/` distribution already exists;
- direct `torch::Tensor` prediction and Torch parameter iteration fit the task.

Choose PaddleLite when:

- the model is an exported Paddle inference model directory;
- a compatible local `inference_lite_lib/` distribution already exists;
- the task needs `PaddlePredictor` inference or the asynchronous `AsyncESAgent` flow.

Do not choose a backend based only on the Python training framework. Choose based on the C++ inference artifact and local backend library available to EvoKit.
