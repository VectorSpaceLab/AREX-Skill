# Troubleshooting

## Common provider and file-layout problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No training files` | The glob pattern found no data files | Check the path and the data suffix/mask suffix pair. |
| Mask files are not recognized | The mask suffix does not match the file naming convention | Keep the default `_mask.tif` convention unless you override it consistently. |
| `ValueError: low >= high` in toy generation | The toy image is smaller than the requested border and circle radius range | Increase `nx`/`ny` or reduce `border`. |
| Binary `SimpleDataProvider` labels broadcast incorrectly | A two-class `SimpleDataProvider` path was given one-hot labels instead of a binary mask | Pass a binary mask for the two-class case, or switch to a multi-class one-hot layout. |
| `np.bool` or other legacy NumPy issues | The code path was exercised with a much newer NumPy stack | Keep the legacy TensorFlow 1.x compatibility set used by the inspected environment. |
| HDF5 key errors for launcher-style workflows | The file layout does not match the expected dataset names | Recreate the `data`/`mask` or `image`/`segmaps/*` layout first. |
| `PIL`, `h5py`, or `scipy` is missing | Launcher dependencies were not installed | Install the workflow-specific dependency before retrying. |

## Practical tips

- Use the synthetic smoke helper before debugging a custom dataset.
- If you only need the provider contract, stay on the NumPy or toy-generator path and avoid external data.
- When a custom provider has its own normalization or clipping rules, document them next to the data layout so future users do not guess.
- Keep the launcher data layout description separate from the model graph; the input contract changes more often than the network.
