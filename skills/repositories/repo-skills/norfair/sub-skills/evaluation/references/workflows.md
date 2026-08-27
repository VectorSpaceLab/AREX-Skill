# Norfair MOTChallenge evaluation workflows

Use this reference when the task is to score a tracker, parse MOTChallenge text files, save predictions or metrics, or compare Norfair with ByteTrack-style evaluation logic.

## 1. Score existing predictions on MOTChallenge data

Use this when you already have MOTChallenge-format prediction text files and want a summary score.

```bash
python scripts/motchallenge_eval.py \
  /path/to/MOT17/train \
  --predictions-root /path/to/run \
  --save-metrics
```

How it works:

1. The helper resolves the sequence folders under the dataset root.
2. For each sequence, it looks for a matching prediction file at either:
   - `/path/to/run/predictions/<sequence>.txt`
   - `/path/to/run/<sequence>.txt`
3. It loads the prediction rows into MOTChallenge matrices.
4. It calls `eval_motChallenge` to load `gt/gt.txt` and compute metrics.
5. It prints the rendered summary and writes `metrics.txt` when requested.

Useful options:

- `--select-sequences <name ...>` to score only a subset of sequences.
- `--strict` to fail instead of skipping missing prediction files.
- `--no-generate-overall` if you do not want the extra `OVERALL` row.

## 2. Save predictions while running a tracker

Use this when you are already inside a tracker loop and want MOTChallenge output files.

Minimal pattern:

```python
from norfair import metrics

predictions_text_file = metrics.PredictionsTextFile(
    input_path=sequence_path,
    save_path=output_root,
    information_file=info_file,
)
accumulator = metrics.Accumulators()
accumulator.create_accumulator(sequence_path, info_file)

for frame_detections in detections_by_frame:
    tracked_objects = tracker.update(detections=frame_detections)
    predictions_text_file.update(predictions=tracked_objects)
    accumulator.update(predictions=tracked_objects)

accumulator.compute_metrics()
accumulator.save_metrics(save_path=output_root)
```

What gets written:

- Predictions: `<output-root>/predictions/<sequence>.txt`
- Metrics: `<output-root>/metrics.txt`

Important: call `update` once per frame so the accumulator can finalize the sequence.

## 3. Parse MOTChallenge detections or text rows

Use this when you need the raw MOTChallenge detections without computing metrics yet.

### Detection file parsing

```python
from norfair import metrics

info = metrics.InformationFile("/path/to/seqinfo.ini")
parser = metrics.DetectionFileParser("/path/to/sequence", information_file=info)
for frame_detections in parser:
    ...
```

This reads `det/det.txt`, sorts by frame, converts boxes to corner coordinates, and yields Norfair `Detection` objects frame by frame.

### In-memory MOTChallenge matrices

If you already have rows in memory, use `load_motchallenge(matrix_data)` to turn them into the DataFrame shape expected by `motmetrics`.

That is useful when you want to compare two evaluation variants without re-reading the text files.

## 4. Compare Norfair with ByteTrack-style evaluation logic

This sub-skill keeps the evaluation contract in MOTChallenge box space. The main distinction is the tracker state representation upstream of evaluation.

Distilled comparison notes:

- The XYAH Norfair variant is useful when you want to compare against a ByteTrack-style `[center_x, center_y, aspect_ratio, height]` tracker state. The evaluation output is still MOTChallenge text rows.
- The external ByteTrack comparison variant is reference-only: it depends on ByteTrack internals and is not part of the bundled runtime helper.

Recommended practice:

1. Keep tracker setup and state conversion in `tracking-core`.
2. Keep evaluation in this sub-skill.
3. Compare trackers by the MOTChallenge text files they emit, not by their detector stack.

## 5. Tiny synthetic smoke check

Use the bundled smoke helper when you want a no-download fixture that exercises the parser and scoring path.

```bash
python scripts/motchallenge_smoke.py --output-root ./mot-smoke-output
```

The smoke helper:

1. Creates a tiny MOTChallenge fixture with one sequence.
2. Writes `seqinfo.ini`, `gt/gt.txt`, and `det/det.txt`.
3. Parses detections with `DetectionFileParser`.
4. Writes predictions with `PredictionsTextFile`.
5. Scores the fixture with the reusable evaluation helper when `motmetrics` is available.

If `motmetrics` is missing, the helper still demonstrates layout parsing and reports the dependency block instead of silently pretending the score ran.

## 6. How to use saved metrics

The rendered summary written to `metrics.txt` is the same text returned by `eval_motChallenge`.

Good uses:

- Compare runs from the same dataset split.
- Track regressions on the `OVERALL` row.
- Keep a compact artifact beside the prediction files.

Avoid:

- Treating the rendered text as a replacement for the underlying DataFrame.
- Comparing scores across incompatible matcher settings or tracker state formats without noting the change.