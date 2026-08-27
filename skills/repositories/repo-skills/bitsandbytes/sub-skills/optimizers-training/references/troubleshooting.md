# Optimizer Troubleshooting

## Purpose

Use this reference when a bitsandbytes optimizer trains incorrectly, gives no memory savings, ignores an override, fails on CPU/GPU/XPU, or has checkpoint/state issues.

## No Memory Savings

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `Adam8bit` runs but memory looks the same as 32-bit Adam. | Most trainable tensors are below `min_8bit_size=4096`. | Count parameter sizes; small tensors intentionally stay 32-bit. For diagnostics only, lower `min_8bit_size`, or for production raise it to preserve more 32-bit stability. |
| Optimizer state shrinks but peak memory barely changes. | Activations, gradients, model weights, dataloader buffers, or temporary tensors dominate peak memory. | Profile peak memory around forward/backward/step separately. 8-bit optimizers only reduce optimizer-state memory proportional to parameters. |
| Paged optimizer does not reduce memory. | Paging activates only under memory pressure and requires supported accelerator behavior. | Compare paged and non-paged runs under the same accelerator and model size; do not expect CPU-only savings. |

## Override Does Not Apply

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Embedding or layer norm still appears to use 8-bit state. | `GlobalOptimManager.register_parameters()` was not called before moving parameters to accelerator or before optimizer state setup. | Recreate the model, register parameters while they are still on CPU, move to accelerator, construct optimizer, then call `override_config()` for the exact parameter objects. |
| Override silently affects the wrong thing. | The code overrides a stale parameter object after the module replaced a `Parameter`. | Print or compare `id(parameter)` for the module parameter and optimizer parameter list; override the exact object used by the optimizer. |
| Multiple overrides are inconsistent. | Mixed use of single-key and dictionary overrides, or duplicate module-local overrides. | Prefer one override block using `key_value_dict={"optim_bits": 32}` for all stability-sensitive parameters. Keep module-local `register_module_override()` configs close to parameter creation. |

## CPU-Only or Native Method Failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| A CPU smoke imports bitsandbytes but optimizer step fails with a native-method or backend error. | Installed package lacks the backend needed for that optimizer path or the local build does not include CPU optimizer kernels. | Route install/backend diagnosis to `../../installation-diagnostics/`; run its import/backend checks before changing training code. |
| A user expects GPU memory savings from a CPU run. | CPU smoke tests only validate API and training-loop integration. | Explain that memory-saving claims are for accelerator optimizer-state memory; use accelerator-specific profiling for savings. |
| Paged optimizer raises accelerator availability errors. | `Paged*` workflow is being run without CUDA/XPU support or required memory APIs. | Switch to non-paged optimizer for CPU or install/use a supported accelerator backend. |

## State Dict and Resume Issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `load_state_dict()` loads but the next step fails. | Optimizer state tensors are on the wrong device or model parameters were reconstructed differently. | Recreate the optimizer after creating the model, load model state first, load optimizer state, move any needed tensors to the target device, then validate with one tiny step. |
| Checkpoint has missing optimizer state for some parameters. | No optimizer step was run before saving, or parameters were frozen/excluded. | Run one forward/backward/step before expecting populated optimizer state. Confirm the optimizer was constructed with the intended trainable parameters. |
| Small parameter states are float32 in an 8-bit checkpoint. | `min_8bit_size` kept them 32-bit. | Treat as expected unless the tensor size exceeds the threshold or an override changed `optim_bits`. |

## Stability Problems

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| NLP finetuning diverges after switching to 8-bit optimizer states. | Embeddings or normalization parameters may be stability-sensitive. | Use `bnb.nn.StableEmbedding` for token embeddings and/or override embeddings, layer norm weights, layer norm biases, and other sensitive parameters to `optim_bits=32`. |
| Loss is noisy or worse than a 32-bit baseline. | The training recipe may be sensitive to optimizer state quantization, threshold choices, or learning rate. | First reproduce with `Adam32bit` or `AdamW32bit`; then use selective `GlobalOptimManager` overrides before changing learning-rate schedules. |
| `amsgrad=True` fails on `Adam8bit` or `AdamW8bit`. | Dedicated 8-bit Adam/AdamW classes reject AMSGrad. | Use `amsgrad=False`, or choose a 32-bit optimizer if AMSGrad is required. |

## Validation Checklist

1. Run `scripts/cpu-optimizer-smoke.py --optimizer adam8bit --steps 3` for a quick import and loop check.
2. Confirm the user selected the optimizer family that matches the original recipe (`AdamW`, `Adam`, `Lion`, or AdEMAMix).
3. Check `min_8bit_size` before concluding that quantization failed.
4. Check `GlobalOptimManager` registration order and exact parameter identity.
5. For paged optimizers, confirm supported accelerator availability and compare under identical model/batch conditions.
6. If errors mention import, native libraries, CUDA, ROCm, XPU, CPU kernels, or missing binaries, route to `../../installation-diagnostics/`.
