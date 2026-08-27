# Structured datasets troubleshooting

- If `fd.run(annotations=...)` fails, check the dataframe column names first.
- For labeled-image workflows, keep one row per image and make `filename` resolve to a real file.
- For bbox workflows, keep the coordinate columns consistent and choose the bbox data type explicitly when needed.
- If a bbox gallery fails only with `draw_bbox=True`, rerun the gallery without `draw_bbox` to separate the analysis result from optional crop/bbox rendering.
- For notebook-guided source examples, check the source-specific package, cache, and network or credential setup before assuming fastdup is at fault.
- If a source adapter requires a package that is not installed, fall back to a manually built dataframe.
- CVAT and LabelImg exports need a writable output directory and readable source images.
- If the Hugging Face convenience wrapper raises a circular import during import or construction, use the manual annotation path instead.
