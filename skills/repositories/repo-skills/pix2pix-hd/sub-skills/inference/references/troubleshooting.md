# Inference Troubleshooting

This page collects the failure modes that are most likely to appear when running or adapting pix2pixHD inference commands.

## Fast diagnosis table

| Symptom | Likely cause | What to check | Recovery |
| --- | --- | --- | --- |
| `Generator must exist!` or a missing checkpoint traceback | Wrong `--name`, wrong `--which_epoch`, or the checkpoint file is absent | `checkpoints_dir/name/which_epoch_net_G.pth` | Run `scripts/check_checkpoint.py` first; then fix the experiment name, epoch label, or checkpoint location |
| HTML page is not where you expected | `results_dir`, `name`, `phase`, or `which_epoch` differs from the command you imagined | `results_dir/name/phase_which_epoch/index.html` | Open the HTML under the full expanded path; the images live in the sibling `images/` folder |
| `ImportError` for `dominate`, `scipy`, `Pillow`, or similar small HTML deps | The result-rendering stack is missing | `util/html.py` imports `dominate`; `util/visualizer.py` imports `scipy.misc` | Install the lightweight HTML dependencies before retrying the normal inference path |
| The command uses `--use_encoded_image` but behaves like label-only inference | Feature mode was not enabled | `instance_feat` or `label_feat` must be on for feature-guided inference | Add a feature flag and re-run; `use_encoded_image` only changes how the feature map is produced |
| Feature-conditioned inference cannot find the clustered feature file | `cluster_path` is missing or written under a different experiment name | `checkpoints_dir/name/cluster_path` | Re-run `encode_features.py` from the matching experiment or point `cluster_path` at the correct `.npy` file |
| `--load_features` cannot find feature maps | The `phase_feat` folder has not been created yet | `dataroot/phase_feat` | Generate the feature-map folder first; this path belongs to the feature workflow, not the plain label-only recipe |
| The copied `scripts/test_1024p_feat.sh` fails to parse | The source shell script has a legacy typo | It contains `---netG` instead of `--netG` | Correct the flag in the adapted command; do not copy the typo into the helper output |
| `--export_onnx` fails immediately | The output file does not end with `.onnx` or the checkpoint is missing | The export path and checkpoint path | Rename the export target with the `.onnx` suffix and preflight the checkpoint |
| `--engine` or `--onnx` dies with TensorRT / pycuda import errors | The optional vendor stack is absent | `run_engine.py` imports TensorRT and `pycuda` at module import time | Fall back to standard PyTorch inference and treat the accelerator path as unavailable |
| `--engine` / `--onnx` reaches HTML saving and then fails with a `NoneType` error | The legacy helper does not return a synthesized tensor | `run_engine.py` time-inference helpers | Treat the optional accelerator path as reference-only until the helper is repaired |

## Checkpoint-first recovery order

1. Confirm the experiment name and epoch label.
2. Confirm the generator checkpoint path.
3. Confirm the feature cache only if the command uses feature conditioning.
4. Confirm the results root if the HTML page is in the wrong place.
5. Only after those checks, look at optional ONNX/TensorRT behavior.

## Clean fallback rule

If the optional accelerator path is unavailable, do **not** claim that the standard CUDA path is broken. Use the standard `test.py` synthesis flow and keep the vendor-specific limitation separate.

## Notes on missing `dominate`

The bundled HTML writer imports `dominate` directly. If that package is absent, the standard inference path can still be recovered by installing the lightweight HTML dependencies and re-running the command. This is a small dependency issue, not a model-quality issue.
