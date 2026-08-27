# PC-Agent Action and Perception Notes

PC-Agent is a desktop-control stack, not the same as GUI-Owl desktop.

## Perception knobs

- `--use_som`: enable set-of-mark visual annotations for action planning.
- `--draw_text_box`: overlay text boxes on SoM output.
- `--use_a11y`: include OS accessibility information where available.
- `--use_perception_info`: choose whether OCR/A11y information is provided to the model.
- `--ocr_api`: use hosted OCR API or local/fallback OCR depending on runtime setup.

## Coordinate and font knobs

- `--ratio`: aligns screenshot coordinates with OS coordinate space. Mac Retina often needs `2.0`; Windows often uses `1.0`.
- `--font_path`: controls text overlay drawing. Missing font files can break or degrade SoM screenshots.
- `--mac`: current PC-Agent selects Mac keybindings with `1` and Windows-like behavior with `0`.
- `run_v1.py --pc_type mac|windows` performs a similar split for v1.

## Debugging offset clicks

1. Confirm screenshot resolution and actual screen scaling.
2. Adjust `--ratio` before changing model prompts.
3. Verify font path if SoM boxes are misdrawn.
4. Toggle A11y/perception info to determine whether OCR/accessibility text is misleading the planner.
5. Keep a short `--num_step_limit` while debugging.
