# EvoKit build and API reference

EvoKit is PARL's optional C++ toolkit for evolution-strategy (ES) parameter search. It combines a sampling method, an optimizer, and a prediction backend so that a model can be perturbed online, evaluated in an environment or product system, and updated offline from recorded perturbation metadata and rewards.

## Scope and evidence-backed capabilities

- The public concept is an `ESAgent` that clones sampling agents, applies parameter noise, predicts with noisy parameters, and updates the original parameters from `SamplingInfo` plus reward vectors.
- The documented design mentions several evolution algorithms, but the inspected public headers and protobuf schema expose Gaussian sampling and cached Gaussian sampling as the concrete local sampling methods.
- Optimizer support is represented by the generic `Optimizer` base plus SGD/Momentum-style and Adam implementations/configuration fields.
- Backends are mutually exclusive at build time: Torch/libtorch or PaddleLite. The CMake logic rejects builds with neither backend selected and also rejects builds with both selected.

## Core configuration schema

EvoKit uses a proto2 configuration package named `evo_kit`.

Important messages and fields:

- `EvoKitConfig`
  - `seed`: random seed, default `18`.
  - `buffer_size`: general sampling buffer size, default `100000`.
  - `gaussian_sampling`: nested Gaussian configuration.
  - `optimizer`: nested optimizer configuration.
  - `async_es`: nested asynchronous PaddleLite ES configuration.
- `GaussianSamplingConfig`
  - `std`: perturbation standard deviation, default `1.0`.
  - `cached`: whether cached noise is used, default `false`.
  - `cache_size`: cached noise size, default `100000`.
- `OptimizerConfig`
  - `type`: optimizer name, default `SGD`.
  - `base_lr`: base learning rate, default `1e-3`.
  - `momentum`: momentum value, default `0.9`.
  - `beta1`, `beta2`, `epsilon`: Adam parameters.
- `SamplingInfo`
  - `key`: repeated integer keys used to reconstruct sampled noise.
  - `model_iter_id`: model iteration identifier for asynchronous/offline flows.
- `AsyncESConfig`
  - `model_warehouse`: model directory sequence root, default `./model_warehouse`.
  - `model_md5`: saved model identifiers.
  - `max_to_keep`: retention count, default `5`.
  - `model_iter_id`: current model iteration id, default `0`.

Because the schema is proto2, generated C++ sources must be produced by a compatible `protoc`, and the compiled program must link against a compatible protobuf runtime.

## ESAgent conceptual loop

The safe mental model is:

1. Create an original agent from the model and EvoKit config.
2. Clone one or more sampling agents from the original.
3. For each sampling agent:
   - call `add_noise(SamplingInfo&)` on the clone;
   - run model/environment evaluation with the noisy clone;
   - store the returned `SamplingInfo` and the matching scalar reward.
4. Call `update(vector<SamplingInfo>&, vector<float>&)` on the original agent.
5. Repeat until the reward target or iteration budget is reached.

Important invariants:

- `add_noise` belongs on cloned sampling agents, not on the original agent.
- `update` belongs on the original agent, not on a cloned sampling agent.
- The `SamplingInfo` vector and reward vector must have the same length and preserve pairwise ordering.
- Offline updates depend on being able to reconstruct the same noise from `SamplingInfo.key`; do not discard or reorder keys.
- Parallel evaluation is optional. If OpenMP is unavailable, the loop can be made serial while preserving the same data contract.

## Torch backend API shape

The Torch backend is templated on a C++ model type:

```c++
std::shared_ptr<Model> model = std::make_shared<Model>(obs_dim, act_dim);
std::shared_ptr<evo_kit::ESAgent<Model>> agent =
    std::make_shared<evo_kit::ESAgent<Model>>(model, "config.prototxt");

auto sampling_agent = agent->clone();
evo_kit::SamplingInfo info;
sampling_agent->add_noise(info);
torch::Tensor action_scores = sampling_agent->predict(obs_tensor);
agent->update(noisy_infos, rewards);
```

Key Torch-specific behavior:

- The model type must provide `forward` and be cloneable in the way the agent expects.
- `predict` forwards through the current model for the original agent and through the perturbed sampling model for cloned agents.
- `update` iterates named Torch parameters and applies the configured optimizer step by parameter name.
- Use this backend when the project already owns a C++ Torch model and a local `libtorch/` distribution.

## PaddleLite backend API shape

The PaddleLite backend works with exported Paddle inference model directories:

```c++
std::shared_ptr<evo_kit::ESAgent> agent =
    std::make_shared<evo_kit::ESAgent>("model_dir", "config.prototxt");

auto sampling_agent = agent->clone();
evo_kit::SamplingInfo info;
sampling_agent->add_noise(info);
std::shared_ptr<evo_kit::PaddlePredictor> predictor = sampling_agent->get_predictor();
agent->update(noisy_infos, rewards);
```

Key PaddleLite-specific behavior:

- Use `get_predictor()` to access the current or noisy `PaddlePredictor` and run inference.
- Use this backend when the model is exported for PaddleLite and a local `inference_lite_lib/` distribution is available.
- `AsyncESAgent` extends the PaddleLite agent for asynchronous online/offline update flows. It tracks model warehouse state, model iteration ids, and previous model parameters, and may update the configuration as iterations advance.

## Online/offline ES workflow

A product-style workflow separates initialization, online sampling, and offline update:

1. **Initialize solver/model state once.** Load the config and model, initialize or load solver state, and persist the initial state.
2. **Online sampling.** Load current state, clone sampling agents, call `add_noise`, evaluate each noisy clone, and persist `(reward, serialized SamplingInfo)` records.
3. **Offline update.** Load current state and sampling records, parse each `SamplingInfo`, call `update`, and save the next model/solver state.

Safety requirements:

- Store record sizes and validate them before parsing serialized `SamplingInfo` bytes.
- Keep reward values and `SamplingInfo` messages paired.
- Include the model iteration id in asynchronous flows so stale samples are interpreted against the correct model sequence.

## Build prerequisites and backend choice

Minimum local prerequisites for planning:

- `cmake` for configuration and build generation.
- `g++` or a compatible C++11 compiler.
- `protoc` plus a compatible protobuf C++ library.
- `gflags`, `glog`, `pthread`, and OpenMP support when using the parallel demos or default link configuration.
- Exactly one backend library tree:
  - `libtorch/` for Torch.
  - `inference_lite_lib/` for PaddleLite.

Run the bundled prerequisite checker before any build attempt:

```bash
python ../scripts/check_evokit_prereqs.py --project-root <evokit-root> --backend auto
```

## Safe manual build outline

Avoid blind execution of helper scripts. A controlled manual build should:

1. Work in a disposable checkout or clean copy.
2. Generate protobuf C++ sources for the EvoKit proto package.
3. Configure CMake with exactly one backend flag:
   - `-DWITH_TORCH=ON`, or
   - `-DWITH_PADDLE=ON`.
4. Build with an explicit job limit suited to the machine.
5. Treat installation output as source-tree-local unless the CMake install prefix is overridden.
6. Build and run demos only after confirming the required backend library and runtime library paths are local and intentional.

The upstream helper behavior includes directory removal, source-tree installation, optional unzipping, optional network download, and demo execution. Those side effects make the helpers unsuitable as default validation commands.
