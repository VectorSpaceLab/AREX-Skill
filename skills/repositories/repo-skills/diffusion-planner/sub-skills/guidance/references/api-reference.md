# Guidance API and tensor contract

This reference is distilled from the repository's guidance tutorial,
`guidance_wrapper.py`, `collision.py`, `decoder.py`, normalizer classes, and
DPM-Solver adapter. It describes the observed implementation, including
important edge cases that an extension should guard rather than silently
assuming away.

## 1. Sampler-to-guidance call

The decoder constructs DPM-Solver with:

- `classifier_fn=self._guidance_fn`;
- `guidance_type="classifier"` when a guidance wrapper is configured;
- `guidance_scale=0.5`;
- `classifier_kwargs` containing `model`, `model_condition`, `inputs`,
  `observation_normalizer`, and `state_normalizer`.

The DPM adapter calls the classifier under `torch.enable_grad()` with:

```python
energy = classifier_fn(x_in, t_input, condition, **classifier_kwargs)
grad = torch.autograd.grad(energy.sum(), x_in)[0]
```

Consequences:

- `cond`/`condition` is normally `None` for this planner.
- `x_in` is a flattened tensor with shape `[B, P, (T + 1) * 4]` at the
  sampler boundary. `P = 1 + predicted_neighbor_num`.
- `t_input` is a tensor of continuous diffusion times, normally `[B]`, in the
  sampler's approximately `[0, 1]` interval.
- The returned value must be a finite `torch.Tensor`; a scalar or a `[B]`
  tensor is compatible with `.sum()`, but a per-element tensor should only be
  returned when its sum has the intended optimization meaning.
- The result must retain a path to the differentiable sampler input. Returning
  `torch.tensor(existing_value)`, `.detach()`, a Python float, or a value
  computed entirely from detached inputs breaks guidance or makes its gradient
  zero.

The live callable signatures are:

```text
GuidanceWrapper()
GuidanceWrapper.__call__(self, x_in, t_input, cond, *args, **kwargs)
collision_guidance_fn(x, t, cond, inputs, *args, **kwargs) -> torch.Tensor
batch_signed_distance_rect(rect1, rect2)
center_rect_to_points(rect)
VPSDE_linear(beta_max=20.0, beta_min=0.1)
VPSDE_linear.sde(self, x, t)
VPSDE_linear.marginal_prob_std(self, t)
dpm_sampler(model, x_T, other_model_params={}, diffusion_steps=10,
            noise_schedule_params={}, model_wrapper_params={},
            dpm_solver_params={}, sample_params={})
```

## 2. Custom function contract

The tutorial presents this public shape:

```python
import torch

def my_guidance_fn(x, t, cond, inputs) -> torch.Tensor:
    # x: physical-unit state; preserve its graph where guidance is needed.
    # t: diffusion time; cond: usually None.
    # inputs: inverse-normalized observation dictionary.
    reward = ...
    return reward
```

The wrapper actually calls the function as
`guidance_fn(x_in, t_input, cond, **kwargs)`. Therefore use either the exact
`inputs` parameter name or an explicit compatibility signature such as:

```python
def my_guidance_fn(x, t, cond, inputs, *args, **kwargs) -> torch.Tensor:
    ...
```

A robust function should:

1. Assert or document the expected rank and feature order before indexing.
2. Keep all tensors on `x.device` and use a compatible floating dtype.
3. Return a scalar or `[B]` finite energy with a deliberate sign convention.
4. Preserve autograd through the position/state coordinates that the reward
   should influence.
5. Use `torch.isfinite` checks during development and provide a zero-energy
   fallback with graph connectivity for an intentionally empty mask, for
   example `x[..., 0].sum(dim=(-1, -2)) * 0.0`.
6. Avoid in-place writes to `x` or to shared `inputs`; clone before modifying.

The sign is not abstract: the DPM adapter subtracts
`guidance_scale * sigma_t * grad` from the model's predicted noise. Validate
whether increasing your returned energy moves samples toward or away from the
desired behavior with a tiny synthetic case before a closed-loop run.

## 3. What `GuidanceWrapper` does

The current implementation has this sequence:

1. Reads `state_normalizer`, `observation_normalizer`, `model`, and
   `model_condition` from keyword arguments.
2. Reshapes the sampler state as `[B, P, -1, 4]` and calls the model:
   `model(x_in, t_input, **model_condition)`.
3. Forms a detached model correction, `model_output.detach() -
   x_in.detach()`, zeros its current-state slot (`[:, :, 0]`), and adds it to
   `x_in`. This keeps the current state fixed while retaining an identity
   gradient path through the sampler input.
4. Applies `state_normalizer.inverse` to the reshaped state.
5. Replaces `kwargs["inputs"]` with
   `observation_normalizer.inverse(kwargs["inputs"])`.
6. Sums the registered guidance function outputs and asserts that the sum has
   no NaNs.

The custom function therefore receives:

```text
x       [B, P, T+1, 4]   physical state, current slot at index 0
                         feature order: x, y, cos(heading), sin(heading)
t       [B]              diffusion time in the normal sampler path
cond    None (usual)     condition argument from DPM-Solver
inputs  dict[str,Tensor] inverse-normalized observations
```

`GuidanceWrapper` mutates only the local keyword dictionary's `inputs` value;
it does not make a defensive copy of every observation tensor. A custom
function must not mutate this dictionary or its tensors in place, because the
same model-condition data may be reused by the sampler.

The model correction requires a callable model accepting the keys in
`model_condition` (`cross_c`, `route_lanes`, and `neighbor_current_mask` in the
built-in decoder). A wrapper smoke test may use an identity model and identity
normalizers, but a real simulation must provide the decoder model and the
normalizer instances created by the planner configuration.

## 4. Normalization and physical units

`StateNormalizer.inverse(data)` computes `data * std + mean` with `mean` and
`std` moved to `data.device`. `ObservationNormalizer.inverse(data)` applies the
same transformation per configured feature and restores all-zero masked rows
to zero. Thus:

- Calculate geometry in the physical state/observation units after the
  wrapper's inverse calls.
- Do not inverse-normalize a second time in a custom function.
- Do not move inputs to CPU merely to use a geometry helper.
- Check that every configured standard deviation is finite and nonzero.
- Treat the current-state slot as a constraint, not a future action. The
  decoder later removes the current slot before returning the prediction.

The observation fields used by built-in collision guidance include:

```text
neighbor_current_mask  [B, P-1] boolean; True means no current neighbor
neighbor_agents_past   [B, P-1, past_steps, feature_dim]
```

The collision implementation reads the final history row at feature indices
`[7, 6]` for `[width, length]`. Preserve this source order when preparing a
compatible observation tensor; do not infer it from the `[x, y, cos, sin]`
state order.

## 5. Collision geometry

`center_rect_to_points(rect)` accepts `[B, 6]` rows:

```text
[x, y, cos_heading, sin_heading, length, width]
```

It returns `[B, 4, 2]` corners. The local half-extents are generated in this
order:

```text
(+length/2, +width/2), (-length/2, +width/2),
(-length/2, -width/2), (+length/2, -width/2)
```

and rotated by the heading matrix. `batch_signed_distance_rect(rect1, rect2)`
accepts two `[B, 4, 2]` corner tensors and returns `[B]`. It projects both
rectangles on the four edge-normal axes (a separating-axis test): positive
values represent separation and negative values overlap. Validate the sign
on the fixed smoke geometry rather than assuming a conventional distance
normalization.

The built-in collision function:

- gets the Pacifica ego length/width at module import;
- shifts the ego center by `COG_TO_REAR = 1.67` along its heading;
- adds `INFLATION = 1.0` to both rectangle dimensions;
- clips distance influence with `CLIP_DISTANCE = 1.0`;
- compares the ego against only neighbors selected by
  `~neighbor_current_mask`;
- detaches neighbor trajectories and heading components, so the intended
  gradient is primarily through the ego's position trajectory;
- uses a time gate intended for `0.005 < t < 0.1`; and
- smooths/rotates the position gradient before returning `3.0 * reward`.

The returned value is consequently a guidance energy built from a
collision-derived gradient, not simply the raw signed distance. Re-check its
sign and scale when composing another energy.

### Source edge cases to guard

The implementation has a few observable assumptions:

- The time gate is written with Python `and`. It is safe only for a scalar-like
  or one-element `t`; a multi-element batch can raise the ambiguous-bool error.
  A new function should use vectorized `torch.logical_and` and define the
  desired per-sample behavior.
- Heading normalization divides by the norm of detached `[cos, sin]`. A zero
  heading produces NaNs. Validate and normalize with an epsilon in a custom
  implementation.
- An all-True neighbor mask creates no valid ego/neighbor pairs. Empty
  reductions and downstream autograd can then return an unusable energy. Return
  a finite graph-connected zero for this explicit case.
- The source's tutorial says `x: [B * Pn+1, T+1, 4]`, but the live function
  operates on `[B, P, T+1, 4]`. Follow the live wrapper/decoder layout.

## 6. SDE and sampler interaction (only what guidance needs)

`VPSDE_linear` uses `beta_min=0.1`, `beta_max=20.0`, and `T=1.0`. Its
`marginal_prob_std(t)` is used by the DiT score parameterization and exposes the
same time range used by sampling. `dpm_sampler` defaults to ten diffusion
steps and uses DPM-Solver++ order 2 with `x_start` conversion for the built-in
DiT. In guided mode, every solver model evaluation can invoke the guidance
function, so keep guidance deterministic, finite, device-local, and cheap.

The solver is enclosed in `torch.no_grad()`, but its classifier adapter opens
`torch.enable_grad()` and differentiates the returned energy. Do not rely on a
surrounding training context to create the graph; do not wrap a guidance
calculation in `torch.no_grad()`.
