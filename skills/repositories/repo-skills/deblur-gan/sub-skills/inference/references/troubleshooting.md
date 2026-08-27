# Inference troubleshooting

## Common failures

### Missing checkpoint

**Symptom**: the run fails while loading `latest_net_G.pth` or the requested epoch label.

**Likely cause**: the checkpoint directory, experiment name, or epoch name does not match the saved model tree.

**Fix**:
- Check the `checkpoints/<name>/` directory.
- Use the correct `--name` and `--which_epoch` values.
- Verify that the generator weights file is present.

### Wrong dataset mode

**Symptom**: the model factory asserts or the loader returns the wrong fields.

**Likely cause**: the command is not using `model=test` with `dataset_mode=single`.

**Fix**:
- Set `--model test`.
- Set `--dataset_mode single`.
- Point `--dataroot` at a folder of standalone images.

### External `ssim` import failure

**Symptom**: the source `test.py` crashes immediately with an import error for `ssim`.

**Likely cause**: the repository imports an external package that is not guaranteed to be installed.

**Fix**:
- Use the bundled wrapper, which follows the local `util.metrics.SSIM` route.
- If you must run the source script verbatim, install the extra package separately.

### visdom import failure

**Symptom**: the run fails when `Visualizer` tries to import visdom.

**Likely cause**: display mode is enabled but visdom is not installed.

**Fix**:
- Keep the bundled wrapper's headless default.
- Or install visdom if you really need interactive plotting.

### CPU inference needs an explicit flag

**Symptom**: the run tries to use CUDA on a machine where you only want CPU inference.

**Likely cause**: the default GPU id is still active.

**Fix**:
- Pass `--gpu_ids -1`.
- Confirm that the model still loads and writes outputs under the results directory.

### Results directory or log directory does not exist

**Symptom**: the visualizer cannot open its log file or the HTML output is not written.

**Likely cause**: the output tree has not been created yet.

**Fix**:
- Create the checkpoint and results directories first.
- The bundled wrapper does this for the checkpoint directory and writes the HTML tree itself.

## What to do next

- For dataset issues, jump back to the data-preparation sub-skill.
- For training or checkpoint generation, jump to the training sub-skill.
- For a quick sanity check, use the root environment helper.
