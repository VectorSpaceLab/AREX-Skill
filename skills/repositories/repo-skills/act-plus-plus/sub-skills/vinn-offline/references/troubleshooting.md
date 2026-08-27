# VINN troubleshooting

## Symptoms and recovery

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `IPython.embed()` opens during k selection | The raw `vinn_select_k.py` contains a debug stop. | Use the bundled non-interactive `select_k.py` helper instead. |
| `assert len(episode_idxs) == episode_idxs[-1] + 1` fails in feature caching | There are gaps in the episode numbering. | Rename or regenerate the dataset so that episode ids are dense from 0. |
| Feature files are missing for one camera | The checkpoint or dataset layout does not match the task's camera list. | Check the cached feature filenames and the dataset camera names before rerunning. |
| `CUDA available=False` or `.cuda()` errors | VINN scripts move features and cached tensors to GPU directly. | Move to a CUDA host or patch the workflow for CPU before claiming CPU support. |
| Feature files exist but k-selection fails on shape mismatch | The feature file layout or concatenation order does not match the expected `(T, 512)` per camera contract. | Inspect the cached feature HDF5 files and confirm the per-camera datasets are present. |
| `vinn_eval.py` tries to open a real robot environment | The source script hard-codes `real_robot = True`. | Treat eval as a Mobile ALOHA deployment step, not a standalone offline workflow. |

## Safe recovery order

1. Run [check_vinn_stack.py](../scripts/check_vinn_stack.py) to confirm imports and CUDA visibility.
2. Confirm the checkpoint filename pattern and dataset episode numbering.
3. Confirm the cache helper wrote one feature file per episode and camera.
4. Use the bundled non-interactive k-selection helper, not the raw source script.
