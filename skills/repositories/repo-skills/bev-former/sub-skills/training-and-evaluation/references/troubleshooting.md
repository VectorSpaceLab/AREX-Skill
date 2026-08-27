# Troubleshooting

## Common failures and what they mean

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `tools/test.py` fails in non-distributed mode | This repo disables the non-distributed eval branch. | Use the distributed launcher with `--nproc_per_node=1` or more. Do not suggest a single-process shortcut. |
| `ModuleNotFoundError` for `projects.mmdet3d_plugin` or registry errors | Plugin import path or legacy OpenMMLab stack is wrong. | Check that the config sets `plugin=True` and `plugin_dir='projects/mmdet3d_plugin/'`, and route install/import issues to `installation-and-configs`. |
| `NCCL` or CUDA init errors | GPU visibility, driver, or backend mismatch. | Confirm visible GPUs, matching CUDA/PyTorch/mmcv builds, and NCCL availability before composing the command. |
| `resume_from` appears to be ignored | The path does not exist. | `tools/train.py` only applies `resume_from` when the file exists. Verify the path before handoff. |
| `--eval` and `--format-only` together | Unsupported option pair. | Choose one operation mode only. |
| `--out` rejected | Output file extension is wrong. | Use `.pkl` or `.pickle`. |
| `--cfg-options` parse failure | Incorrect quoting or nested list syntax. | Use `KEY=VALUE` tokens and quote lists/tuples such as `key="[a,b]"` or `key="[(a,b),(c,d)]"`. |
| Eval command has no checkpoint | The composer requires a real checkpoint path. | Point to a downloaded model zoo checkpoint or a finished training checkpoint. `load_from` is not a substitute for eval. |
| FP16 launch looks wrong | A non-fp16 config was paired with the fp16 entrypoint. | Use the `projects/configs/bevformer_fp16/` family and keep the fp16 runner blocks in place. |
| Training stops before any data work | The data layout is incomplete. | Route to `dataset-preparation` and validate the nuScenes/CAN-bus tree instead of retrying training. |

## Quick gate checklist
- Is the command distributed? It should be.
- Is the config path valid and does it already carry the needed plugin/import blocks?
- Is a real checkpoint available for eval?
- Are CUDA and NCCL available on the target machine?
- Are you trying to fix data layout or config structure? If yes, route away.
