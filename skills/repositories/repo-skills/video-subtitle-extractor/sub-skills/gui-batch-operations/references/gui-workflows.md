# GUI Workflows

## Single video extraction

1. Launch GUI from a VSE source checkout or release.
2. Click Open and choose one video.
3. Draw or adjust the subtitle rectangle in the preview.
4. Confirm language, recognition mode, hardware acceleration, TXT output, and
   word segmentation settings.
5. Click Run. The task list shows status/progress and the log panel shows
   extraction stages.
6. Open the output SRT from the task context menu after completion.

## Batch extraction

Open multiple videos at once. VSE adds each as a pending task and processes
pending tasks sequentially. The README recommends batch videos have the same
resolution and subtitle area. If a later task has no selection, the GUI tries
to reuse an existing task selection, then falls back to saved config.

## AB sections and selection binding

The video display component can store AB section ranges and bind a selection to
a section. Use this for videos whose subtitle placement changes over time. The
current implementation generally treats one active selection as the main
extraction area, so verify behavior on a short segment before long batches.

## Stop and retry

Stop terminates the tracked extraction process and subordinate PIDs, then resets
the current task to Pending. Retrying after a stop should start from a clean
state; if caches were retained for debug, clear them before production reruns.
