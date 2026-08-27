# Model-conversion troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for `onnx`, `onnxslim`, `onnxruntime`, or `torch` | Export environment is missing the verified Python stack | Install the bundled Ultralytics inspection stack before retrying |
| The exporter says the weights file is invalid | Wrong checkpoint path or the file does not exist | Recheck the path and rerun with `-w /path/to/model.pt` |
| `labels.txt` is not created | The checkpoint did not carry class-name metadata | Confirm the model family supports exporter label generation and rerun from the correct checkpoint |
| Dynamic and static batch options conflict | `--dynamic` and a static `--batch` setting were combined | Pick one path and rerun the exporter |
| Export output does not match the DeepStream config | Wrong family or wrong input size | Compare the ONNX output and the family matrix, then switch to the matching config template |
| Exporter needs a legacy upstream package | The family is reference-only in this skill | Install the documented upstream repo and treat the matrix as the source of truth |

## Escalation rules

- If the family is bundled, fix the Python stack and retry.
- If the family is reference-only, do not pretend it is bundled; route to the external upstream stack.
- If the resulting ONNX file is correct but deployment still fails, switch to the deployment sub-skill.
