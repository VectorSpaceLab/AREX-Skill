# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
MMAudio. If the current repo commit, dirty source state, package metadata, or
major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T13:35:10Z",
  "repository": {
    "name": "MMAudio",
    "remote_url": "https://github.com/hkchengrex/MMAudio.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "974010a026c731054592d8f777218bd9d85a6c24",
    "working_tree": "clean-before-generated-skill-files",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "mmaudio",
      "version": "1.0.0",
      "import_names": ["mmaudio"]
    }
  ],
  "evidence": {
    "source_roots": ["mmaudio"],
    "docs": ["README.md", "docs/MODELS.md", "docs/TRAINING.md", "docs/EVAL.md"],
    "scripts": ["demo.py", "gradio_demo.py", "batch_eval.py", "train.py", "eval_onsets.py", "training/partition_clips.py", "training/extract_audio_training_latents.py", "training/extract_video_training_latents.py"],
    "configs": ["config/base_config.yaml", "config/train_config.yaml", "config/eval_config.yaml", "config/data/base.yaml", "config/eval_data/base.yaml"],
    "fixtures": ["training/example_audio.tsv", "training/example_video.tsv", "training/example_audios", "training/example_videos", "sets/vgg-train.tsv", "sets/vgg-val.tsv", "sets/vgg-test.tsv"]
  },
  "verification_summary": {
    "inspection_python": "private Python 3.11 environment",
    "package_imports": "mmaudio, eval_utils, model, data, and runner modules imported",
    "cuda_smoke": "passed on CUDA-capable host",
    "native_heavy_runs": "not executed; model downloads, full feature extraction, training, and batch evaluation remain gated by user approval/data availability"
  }
}
```

The source tree was clean when the snapshot was captured. Later untracked files
under `skills/` are generated skill/review artifacts, not source evidence.

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If package metadata, model variant names, config keys, top-level workflow
  scripts, or data schemas changed, refresh even when the commit is nearby.
- If the current checkout has source edits outside generated skill artifacts,
  refresh or at least re-run the environment/API inspection before relying on
  detailed signatures and config facts.
- If upstream adds a proper CLI entry point or changes model-download behavior,
  refresh the inference and model-assets references.
