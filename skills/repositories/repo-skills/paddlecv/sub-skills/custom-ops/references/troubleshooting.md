# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Module class already registered` | A second custom class reused an existing Python class name. | Rename the class or remove the duplicate registration. |
| `The module ... is not registered` | The file that defines the custom operator was never imported. | Import the module before building the config or starting the pipeline. |
| `The output key in op ... is inconsistent` | The operator returned a dict whose keys do not match `get_output_keys()`. | Make the runtime dict keys and declared output keys identical. |
| `Input: ... could not be found from the last ops` | The YAML points to a missing prior output name. | Fix the `Inputs` chain and verify the previous op's outputs. |
| `Illegal input:` from `check_name.py` | The graph references an input key that no op produces. | Update the config or choose the correct connector/output route. |
| `OCSORTTracker` or tracker imports fail | Optional tracker dependencies are missing. | Install the tracker dependency set used by the connector. |
| Keypoint drawing fails | Visualization helpers such as `matplotlib` are missing. | Install the visualization dependency before using keypoint outputs. |

## Fast recovery sequence
1. Run `scripts/check_name.py` on the config.
2. Confirm the class is imported and decorated.
3. Compare the YAML `Inputs` values with the previous op's `get_output_keys()`.
4. Re-run the relevant unittest config family.
