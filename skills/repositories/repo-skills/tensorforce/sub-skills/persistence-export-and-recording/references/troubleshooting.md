# Persistence Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Agent.load` cannot find files | Wrong directory/filename/format, or checkpoint suffix mismatch | Inspect directory contents; pass `filename`/`format` explicitly. |
| Loaded agent rejects environment | Saved spec states/actions/max timesteps differ from current environment | Load with a compatible environment or recreate the original spec. |
| NumPy/HDF5 load fails | Architecture does not match saved weights | Keep the agent JSON/spec with weights; avoid changing network/module config. |
| SavedModel loads but cannot train | SavedModel is act-only export | Use TensorFlow checkpoint/NumPy/HDF5 for continuing Tensorforce training. |
| HDF5 errors | Missing or incompatible h5py | Install a version compatible with the Python/TensorFlow environment. |
| Summary directory is empty | Run ended before a summary-triggering update, wrong labels, or close/flush missing | Use a longer bounded run, verify `summarizer` labels, and close runner/agent. |
| Recorder/pretrain shape errors | Recorded trace does not match current state/action specs | Regenerate traces with the same environment and preprocessing, or rebuild the agent spec. |
