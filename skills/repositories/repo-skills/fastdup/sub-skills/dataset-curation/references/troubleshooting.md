# Dataset curation troubleshooting

- If the run reports missing files, confirm that the filenames in the input dataframe match the actual image paths.
- If a gallery is empty, check the threshold and the fixture size.
- If `remove_duplicates` will touch real data, start with `dry_run=True` and inspect the planned deletions before allowing writes.
- If `remove_duplicates` seems to do nothing, inspect the connected components and lower the duplicate threshold.
- If corrupted images are expected, inspect the bad-image output such as `features.bad.csv` or the run-specific bad-file CSV before filtering the dataset.
- If feature loading fails, make sure the `d` value matches the saved binary width.
- If HTML generation is slow, reduce `num_images` or use `lazy_load=True`.
