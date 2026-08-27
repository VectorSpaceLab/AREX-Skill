# Inference and evaluation troubleshooting

- **checkpoint cannot restore:** match model family, TensorFlow graph, point
  count, and variable names; use the checkpoint prefix rather than a folder.
- **RGB mode has no output for some frames:** provide the matching index file;
  the source fills empty result files so evaluator coverage remains complete.
- **scores become `-inf`/NaN:** inspect empty segmentation masks and probability
  normalization before editing the evaluator.
- **result validator reports malformed rows:** fix field count, finite values,
  ordered 2D boxes, and frame filename; do not run AP on malformed data.
- **evaluator will not execute:** rebuild its C++ source for the host and check
  permissions; never assume the bundled historical binary is portable.
- **v2 import fails before restore:** custom operators are missing or ABI-
  incompatible; return to the runtime gate.
- **AP differs from a reported benchmark:** verify split, detector inputs,
  checkpoint, class whitelist, difficulty settings, and result coordinate
  conventions before attributing the gap to the model.
