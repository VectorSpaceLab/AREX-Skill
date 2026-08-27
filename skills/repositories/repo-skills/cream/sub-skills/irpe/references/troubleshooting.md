# iRPE Troubleshooting

## `rpe_ops` warning or missing extension

**Symptom:** A warning says the `rpe_ops` module is not built.

**Likely cause:** The optional C++/CUDA extension was not compiled.

**Recovery:**

- Use `../../../scripts/check_custom_ops.py --path <rpe-ops-dir>` to check the build status.
- Continue with the Python implementation if you only need inspection or a small smoke check.
- Build the extension only when you need the accelerated path.

## RPE config mismatch

**Symptom:** The model behaves incorrectly after wiring the RPE block.

**Likely cause:** The `ratio`, `method`, `mode`, `shared_head`, `skip`, or `rpe_on` fields do not match the intended branch.

**Recovery:**

- Generate the config snippet with `../scripts/build_irpe_config.py`.
- Compare the resulting snippet with the workflow reference.
- Keep the DeiT and DETR settings distinct.

## Sequence-shape errors

**Symptom:** The forward pass fails with a tensor-shape mismatch around attention or RPE.

**Likely cause:** The model's head dimension, number of heads, or token layout does not match the RPE wiring.

**Recovery:**

- Check the model's `head_dim` and `num_heads` assumptions before building RPE modules.
- Remember that class-token presence changes the token count.
- Re-check the branch-specific example in the workflow reference.

## Dataset layout problems

**Symptom:** The command cannot find ImageNet or COCO paths.

**Likely cause:** The dataset root was not provided in the expected layout.

**Recovery:**

- Run `../../../scripts/check_dataset_layout.py --kind imagenet1k --root <imagenet-root>` for DeiT.
- Run `../../../scripts/check_dataset_layout.py --kind coco2017 --root <coco-root>` for DETR.

## DETR launcher issues

**Symptom:** The DETR command fails immediately because the RPE flag or distributed setup is wrong.

**Likely cause:** The command used the wrong launcher or omitted a required path.

**Recovery:**

- Use the launcher template from `references/workflows.md`.
- Confirm `--enc_rpe2d` and `--coco_path` before rerunning.
