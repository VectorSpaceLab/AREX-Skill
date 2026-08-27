# Troubleshooting

Use this page when a catalog query does not narrow cleanly or when the selected entry does not fit the intended runtime.

## License gate

- The catalog does not grant usage rights.
- Before recommending a model for use or redistribution, check the target folder's license file(s) and any model-specific notes.
- If the license is missing, unclear, or incompatible with the intended use, stop and escalate instead of guessing.

## Common failures

| Symptom | Likely cause | Next step |
|---|---|---|
| No matches | The category string is too broad, the format flag is wrong, or the model family does not ship that artifact. | Re-run with the exact category string and a correct `--format` value, or broaden with `--contains`. |
| Too many matches | The search only used a family name or a backend flag. | Add `--category`, `--number`, `--directory`, or `--contains` to narrow the shortlist. |
| `--format OV` returns nothing | The family does not provide OpenVINO IR in the catalog. | Try a different family or a different artifact family; do not assume `OV` from the model name alone. |
| `--directory` fails but the folder is known | Some entries do not expose a directory field, or the user only knows the numeric prefix. | Use `--number` or `--name` instead. |
| The result looks right but the input size is unclear | The hint is stored in `remarks`, not in the directory name. | Re-run with `--contains 320x320`, `--contains 112x112`, or another size token from the remarks. |
| The model family seems to fit but the runtime does not | `OV`, `ONNX`, `TFJS`, `TF-TRT`, `CM`, and `TPU` are different artifact families with different execution paths. | Route to `../conversion-and-deployment/` for conversion/deployment questions or `../inference-demos/` for execution questions. |
| The entry is a good family match but still unsafe to use | The folder license has not been checked. | Apply the license gate first, then continue only if the terms are acceptable. |

## Format-meaning reminders

- `OV` means OpenVINO IR.
- `TPU` means an EdgeTPU-oriented artifact, not a generic TPU claim.
- `DQ` means dynamic range quantization, which is different from `INT8` and `WQ`.
- `TF-TRT` is a TensorFlow-TensorRT artifact, not a standalone ONNX or OpenVINO model.

## Recovery pattern

1. Re-check the exact catalog fields with the helper.
2. Confirm the license gate.
3. If the user only needs a shortlist, stay in this sub-skill.
4. If the user wants files or runtime behavior, hand off to the appropriate sibling sub-skill.
