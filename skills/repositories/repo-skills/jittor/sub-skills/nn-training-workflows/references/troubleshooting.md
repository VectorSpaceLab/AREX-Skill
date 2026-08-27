# Troubleshooting: training workflows

Read this when a Jittor model trains incorrectly, the loss does not move, or a checkpoint/state restore behaves oddly.

## 1. The model has no parameters

**Symptoms**
- `parameters()` returns an empty list.
- The optimizer refuses to initialize.

**Likely causes**
- The model stored plain Python values instead of Jittor `Var` state.
- The module forgot to assign trainable layers or variables on `self`.

**Next step**
- Put trainable tensors on the module instance so Jittor can discover them.
- Re-check with the bundled smoke script before changing the rest of the training loop.

## 2. `forward` exists, but training does nothing

**Symptoms**
- The model can be called, but the intended method is never used.
- The optimizer steps, yet the output barely changes.

**Likely causes**
- The main method is named `forward` instead of `execute`.
- The right variables are not in the computation path.

**Next step**
- Rename the main path to `execute`.
- Confirm the trainable state is actually used in the output.

## 3. Loss shape or target mismatch

**Symptoms**
- Broadcasting or reduction assertions.
- Classification loss complains about the target shape or class count.

**Likely causes**
- The target tensor shape does not match the criterion's expected contract.
- A scalar loss was never reduced before gradient extraction.

**Next step**
- Print the tensor shapes before the loss.
- Reduce the loss to a scalar before calling `step`, `backward`, or `jt.grad`.

## 4. The loss never decreases

**Symptoms**
- A few training steps run, but the loss stays flat.

**Likely causes**
- The learning rate is too large or too small.
- The optimizer is attached to the wrong parameter list.
- The model is in the wrong mode.

**Next step**
- Run the tiny regression smoke and confirm that a known-good convex problem decreases.
- Verify `train()` is active during optimization and `eval()` is only used when you are measuring or validating.

## 5. Gradient accumulation is wrong

**Symptoms**
- Accumulated steps over-update or under-update the model.

**Likely causes**
- The loss was not scaled by the number of accumulation steps.
- `backward` and `step` were mixed in the wrong order.

**Next step**
- Use the recipe in `references/training-recipes.md` exactly once before adding extra complexity.

## 6. NaN or Inf appears during training

**Symptoms**
- The output becomes numerically unstable.
- The model suddenly produces invalid values.

**Likely causes**
- The problem is numerical, not structural.
- A debug-friendly lazy-execution path is hiding the first bad op.

**Next step**
- Localize with `jt.flag_scope(lazy_execution=0)` and `trace_py_var=3` from the runtime troubleshooting reference.
- If needed, add `JT_CHECK_NAN=1` for the failing run.

## 7. Checkpoint restore or `state_dict` mismatch

**Symptoms**
- `load_state_dict` skips entries or the restored model behaves differently.

**Likely causes**
- Layer names changed.
- Parameter shapes changed.
- A saved state from another architecture is being loaded.

**Next step**
- Compare the keys from the source and target `state_dict`.
- Treat mismatches as a migration issue to resolve explicitly.

## 8. Memory keeps growing

**Symptoms**
- Each iteration uses more memory than the last.

**Likely causes**
- You are storing tensor outputs instead of scalar summaries.
- Old graphs are still referenced from Python.

**Next step**
- Avoid keeping full graph outputs around when only the numeric value is needed.
- Use the core troubleshooting guidance for graph ownership and cleanup.

## Fast recovery order

1. Verify `execute` is implemented.
2. Verify the right parameters are on the model.
3. Verify the loss is scalar and the shapes are correct.
4. Verify `train()` and `eval()` are being used intentionally.
5. Verify the state dict keys match before blaming the optimizer.