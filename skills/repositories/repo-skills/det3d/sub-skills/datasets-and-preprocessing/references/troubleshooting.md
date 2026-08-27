# Dataset Troubleshooting

- **Missing `infos`/`dbinfos` file**: run the matching preparation for the same
  dataset version, split, and sweep count; do not hand-create an empty pickle.
- **File-not-found under a valid root**: compare the config's `data_root` and
  annotation paths with the actual layout, including case and version names.
- **SDK import error**: check the selected dataset's optional SDK and its
  compatibility with Python, NumPy, Shapely, and protobuf.
- **Empty samples or zero classes**: inspect split files, class filters, label
  names, and whether the chosen split actually contains annotations.
- **Shape/coordinate failures**: verify calibration, axis/order conventions,
  point feature count, range, voxel size, and box dimensions together.
- **Out-of-disk or slow conversion**: stop before partial output is treated as a
  valid dataset; use a fresh output directory after checking free space.
- **GUI/display errors during visualization**: data preparation itself should
  stay headless; route display issues to `visualization-and-analysis`.
