---
name: evaluation
description: "Parse MOTChallenge data, accumulate predictions, and compute MOT metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Norfair evaluation

Use this sub-skill when the task is to score a tracker on MOTChallenge data, parse MOT text files, save predictions or metrics, inspect `load_motchallenge` / `eval_motChallenge`, or compare the standard Norfair flow with the XYAH and ByteTrack-style evaluation references.

## Start here

1. Read [references/api-reference.md](references/api-reference.md) for the distilled behavior of `InformationFile`, `PredictionsTextFile`, `DetectionFileParser`, `Accumulators`, `load_motchallenge`, `compare_dataframes`, `eval_motChallenge`, and the expected MOTChallenge folder layout.
2. Read [references/workflows.md](references/workflows.md) for end-to-end scoring, prediction saving, metrics writing, and the XYAH / ByteTrack comparison notes.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for missing `motmetrics` / `pandas`, missing dataset folders, malformed `seqinfo.ini` or `gt.txt`, skipped sequence names, and long-running evaluation runs.
4. Use [scripts/motchallenge_eval.py](scripts/motchallenge_eval.py) as the reusable helper for scoring MOTChallenge predictions without depending on the source demo tree.
5. Use [scripts/motchallenge_smoke.py](scripts/motchallenge_smoke.py) for a tiny synthetic MOTChallenge fixture check when you want to exercise the parser/evaluator without downloading a dataset.

## What this covers

- Reading MOTChallenge sequence folders and the `seqinfo.ini` metadata that describes them.
- Loading `det/det.txt` detection rows as Norfair `Detection` objects.
- Writing prediction rows in the MOTChallenge box format while a tracker loop runs.
- Computing MOT metrics with `motmetrics` and rendering the summary text.
- Understanding the XYAH and ByteTrack-style comparison notes without making those external trees runtime dependencies.

## Typical workflow

1. Confirm the dataset is a labeled MOTChallenge `train/` split or a single labeled sequence folder.
2. Parse `seqinfo.ini` with `InformationFile` and inspect the detection stream with `DetectionFileParser`.
3. Run the tracker elsewhere, then call `PredictionsTextFile.update(...)` and `Accumulators.update(...)` once per frame.
4. Call `Accumulators.compute_metrics()` or the bundled `motchallenge_eval.py` helper when the sequence is complete.
5. Save the rendered summary with `Accumulators.save_metrics(...)` when you want a `metrics.txt` artifact.

## Bundled scripts

- [`scripts/motchallenge_eval.py`](scripts/motchallenge_eval.py): reusable CLI/helper for scoring prediction files against MOTChallenge sequence folders.
- [`scripts/motchallenge_smoke.py`](scripts/motchallenge_smoke.py): tiny synthetic fixture that proves parser and scorer behavior without a dataset download.

## Route elsewhere

- If the user still needs tracker setup, motion-model choices, hit-counter tuning, or other tracker behavior before scoring, route to [../tracking-core/SKILL.md](../tracking-core/SKILL.md).
- If the user needs to render frames, write video outputs, or work with `Video` / `VideoFromFrames`, route to [../video-visualization/SKILL.md](../video-visualization/SKILL.md).
- If the task is about detector integrations or GPU-heavy demo pipelines, keep it out of this sub-skill and route to the detector-specific or runtime-specific skill that owns that integration.

This sub-skill stays focused on MOTChallenge parsing, accumulation, and metrics. Do not absorb tracker tuning, detector setup, or video overlay concerns into this workflow.
