# Dynamics modeling troubleshooting

Start with a tiny CPU tensor and inspect `module.in_features`, `module.out_features`, and every tensor's `shape`, `dtype`, and `device`. Do not debug a full trajectory or a trainer until the one-step model works.

## Dimension and rank failures

| Symptom | Likely cause | Repair |
|---|---|---|
| `mat1 and mat2 shapes cannot be multiplied` in `MLP`/`Linear` | The summed width of multiple inputs does not equal `insize`, or state/control widths were concatenated before passing to a block that already concatenates them. | For `net(x, u)`, construct `net(nx + nu, outsize)` and pass `x: [B, nx]`, `u: [B, nu]`. For `net(torch.cat([x, u], -1))`, construct the same width but pass one tensor. Do one convention, not both. |
| Output has the wrong feature width | `outsize` is the derivative/state width, not the total state-plus-input width. | Set an ODE RHS to `insize=nx+nu, outsize=nx`; verify `rhs(x, u).shape == [B, nx]`. |
| `ODESystem` rejects the input rank | Its `forward` requires a rank-2 `x`. | Flatten or select a single time slice before invoking the RHS. A trajectory `[B, T, nx]` needs a rollout wrapper or a loop; it is not a direct `ODESystem` input. |
| RNN assertion about rank or hidden sizes | The custom lower-level RNN expects `[T, B, D]`; block wrappers expect `[B, T, D]`. All hidden sizes must be equal. | Use the correct interface and explicitly permute only once. Reset the block between independent open-loop sequences. |
| `Poly2`/`BasisLinear` width mismatch | The expanded width is `D + D(D+1)/2`, not `D`. | Inspect `Poly2()(torch.zeros(1, D)).shape[-1]` and use that width in custom downstream layers. |
| KAN window error for 2-D inputs | `num_domains` is not a perfect square, or the input has more than two coordinates. | Use one domain, a square number of domains such as 4 or 9, or a different block. The current window helper is only 1-D/2-D. |
| Networked ODE indexes the wrong state | `pins` are agent-index pairs while `map` values are tensor-column indices. | Build `map = map_from_agents(agents)`, inspect it, then set each interaction's `feature_name` and `pins` consistently. |
| DAE update changes rank or drops algebraic state columns | An algebraic solver returned only the derived variables. | Clone the full `[B, nx]` state and replace algebraic columns in place/out-of-place. The next differential module must receive the complete state. |

`Block.forward` concatenates all positional tensor inputs on the final dimension. It does not broadcast batch sizes or repair rank-3 sequence tensors.

## PINN/autograd failures

### Detached coordinates

If `torch.autograd.grad(y, x, ...)` reports that a tensor was not used or has no gradient, check all of the following:

1. `x` and `t` were created with `requires_grad_(True)` before the network call.
2. No `.detach()`, `.numpy()`, `torch.tensor(existing_tensor)`, or `torch.no_grad()` occurred between coordinate creation and residual evaluation.
3. The network actually consumes that coordinate column. A coordinate omitted from the input cannot have a derivative.
4. Use `create_graph=True` for every derivative needed to form a higher derivative or backpropagate a residual into parameters.
5. Use `retain_graph=True` when taking multiple derivatives from the same output graph, or recompute the forward pass.

For multiple outputs, `grad(y, x, grad_outputs=torch.ones_like(y))` produces a summed vector-Jacobian product. Compute the component-specific derivative or a Jacobian if the PDE requires separate output components.

Symbolic PINN expressions also need gradient-enabled inference. The model graph should be configured with `grad_inference=True`; do not evaluate the residual-only path under `no_grad`.

## Integrator and solver issues

### Fixed-step methods

`Euler`, `Euler_Trap`, `RK2`, `RK4`, and related methods make one update of size `h`. A large `h` can produce unstable or inaccurate trajectories even when the RHS shape is correct. Start with a small known test such as `dx/dt=-x`, compare one step to the expected sign/magnitude, and only then choose a physical step.

`MultiStep_PredictorCorrector` requires a four-sample history `[B, 4, nx]`; it is not interchangeable with one-step methods. `LeapFrog` and `Yoshida4` require `[B, 2*nx]` packed position/velocity state and are for second-order dynamics.

### `DiffEqIntegrator`

`DiffEqIntegrator` calls TorchDiffEq's adjoint integrator over `[0, h]`. The wrapper accepts a solver `method` but does not expose `rtol` and `atol` in its constructor. Use one of its documented method names (`euler`, `rk4`, `dopri5`, `dopri8`, `bosh3`, `fehlberg2`, `adaptive_heun`, or the Adams variants). If a method is rejected, check the installed TorchDiffEq version and method/noise compatibility before changing the model.

The implementation constructs time points internally. If a custom RHS or device reports a time/device mismatch, first run a CPU float32 check, then ensure state, control, and any constants use a consistent dtype/device. For custom tolerance or time-grid control, call TorchDiffEq directly in application code or provide a small wrapper with an explicit contract rather than passing unsupported keyword arguments to `DiffEqIntegrator`.

### Missing optional packages

- The deterministic package declares TorchDiffEq and TorchSDE dependencies, but a minimal or partially installed environment may omit them.
- `neuromancer.dynamics.integrators` imports `torchdiffeq` and `torchsde` at module import time. Consequently, an import can fail before `Euler` is selected if either package is absent.
- `DiffEqIntegrator` requires TorchDiffEq; `BasicSDEIntegrator` and `LatentSDEIntegrator` require TorchSDE. Label these as optional deployment capabilities and install the package's declared dependency set in the target environment rather than silently replacing them with a different solver.
- The SDE classes follow TorchSDE's diagonal-Ito interface. Verify `noise_type`, `sde_type`, `f`, and `g` before invoking a solver. SDE output is `[T, B, nx]`, not `[B, T, nx]`.

Do not hide an import failure by claiming that deterministic ODE support was verified. Use `scripts/dynamics_smoke.py --help` in an incomplete environment and record the missing dependency; run `--run` only after the required package imports succeed.

## Time, device, and dtype mismatches

- Offline interpolation expects `t: [T, 1]`, `u: [T, nu]`, and query times in the same physical units. The implementation assumes uniform sampling and extrapolates outside the endpoints.
- Online interpolation expects `t/u/tq` with a two-point axis `[B, 2, ...]` and returns `[B, nu]`. A zero interval denominator creates invalid values.
- Keep `x`, controls, network parameters, interpolation values, and physical constants on the same device and with compatible floating dtype. Avoid Python/CPU tensors inside a CUDA forward path.
- The current SINDy `FunctionLibrary.evaluate` initializes its output on CPU; treat SINDy/library GPU use as unverified and use CPU unless this behavior is audited or patched.
- `GeneralNetworkedODE.intrinsic_physics` starts with an empty tensor before concatenation; CPU is the safe baseline. CUDA execution of networked physics is optional/unverified.
- CUDA training/inference and multi-GPU Lightning are not part of the required CPU verification. Do not infer GPU support from an importable CUDA-enabled PyTorch build.

## Physics and composition issues

`GeneralNetworkedODE` supports `inductive_bias='additive'` and `'compositional'`. `'general'` raises an explicit not-implemented exception. Unknown bias strings also raise. A coupling's `feature_name` must exist in the corresponding agent map; each pin must reference valid agent indices.

For `RCNode`, `DeltaTemp`, and `DeltaTempSwitch`, the implementation floors physical parameters with CPU-created scalar tensors. Keep the required CPU path as the publication baseline and audit scalar/device behavior before attempting accelerator execution.

For a hybrid ODE, honor the constructor's block assertions. A two-state hybrid model with a scalar learned term needs a block `[B, 2] -> [B, 1]`, not a full derivative block `[B, 2] -> [B, 2]`.

## FunctionEncoder failures

| Symptom | Repair |
|---|---|
| Representation has an unexpected leading dimension | `[N, D]` is treated as one function and returns `[K]`; `[F, N, D]` returns `[F, K]`. Add/remove the function batch intentionally. |
| `einsum` shape error in `predict` | Batched query input should be `[F, Q, D]` and representation `[F, K]`. A list of basis modules must all return `[F, Q, M]` before stacking. |
| Singular or unstable least-squares result | Use the default positive regularization or pass a nonnegative `lambd`; increase calibration points or improve basis diversity. Do not pass a negative `lambd`. |
| Gram matrix width is unexpected | There are `K` basis modules, so Gram shape is `[F, K, K]` (or `[K, K]` for one function after squeezing). |
| Average-function residual looks wrong | `average_function` is evaluated without gradient during representation computation and added back during prediction. Confirm its output shape `[F, N, M]`/`[F, Q, M]`. |

The FunctionEncoder contains no training loop. A correct forward pass does not mean its basis parameters have been fitted; route optimization to the training workflow.

## Native extensions and long-running examples

Structured maps and the butterfly/factor native extension are a separate route. Do not make this sub-skill depend on a compiler, CUDA toolkit, benchmark corpus, or native extension; use `torch.nn.Linear` for a portable construction and route map-specific work to `structured-operators`.

The ODE/PDE/DAE/SDE/function-encoder examples are teaching anchors, not safe smoke tests. Avoid network downloads, plotting-heavy notebooks, multi-thousand-epoch training, large trajectory generation, and external DAE data in a verification run. Replace them with the bounded checks in `scripts/dynamics_smoke.py` and the small fixtures in the workflows reference.
