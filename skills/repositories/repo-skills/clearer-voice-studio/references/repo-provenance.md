# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of ClearerVoice-Studio. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:16:26Z",
  "repository": {
    "name": "ClearerVoice-Studio",
    "remote_url": "https://github.com/modelscope/ClearerVoice-Studio.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6b3774dc79c46ae8bed2a4fa5f706f0ac8c75c61",
    "working_tree": "dirty-production-artifacts-only",
    "dirty_paths": [
      "skills/ (production log, generated skill, and review artifacts; no source-code changes outside skills/)"
    ]
  },
  "packages": [
    {
      "name": "clearvoice",
      "version": "0.1.2",
      "import_names": ["clearvoice"],
      "notes": "source __version__ string inspected as 0.1.0"
    },
    {
      "name": "SpeechScore source component",
      "version": null,
      "import_names": ["speechscore"],
      "notes": "source-layout component, not a separately installed distribution in this snapshot"
    }
  ],
  "evidence": {
    "source_roots": [
      "clearvoice/clearvoice",
      "speechscore",
      "train/speech_enhancement",
      "train/speech_separation",
      "train/speech_super_resolution",
      "train/target_speaker_extraction",
      "train/target_speaker_extraction_online",
      "train/data_generation/speech_enhancement"
    ],
    "docs": [
      "README.md",
      "clearvoice/README.md",
      "speechscore/README.md",
      "train/speech_enhancement/README.md",
      "train/speech_separation/README.md",
      "train/speech_super_resolution/README.md",
      "train/target_speaker_extraction/README.md",
      "train/target_speaker_extraction_online/README.md",
      "train/data_generation/speech_enhancement/generate_noisy_speech/README.md",
      "train/data_generation/speech_enhancement/generate_reverb_noisy_speech/README.md"
    ],
    "examples": [
      "clearvoice/demo.py",
      "clearvoice/demo_with_more_comments.py",
      "clearvoice/demo_Numpy2Numpy.py",
      "speechscore/demo.py"
    ],
    "configs": [
      "clearvoice/clearvoice/config/inference",
      "train/speech_enhancement/config",
      "train/speech_separation/config",
      "train/speech_super_resolution/config",
      "train/target_speaker_extraction/config",
      "train/target_speaker_extraction_online/config"
    ],
    "scripts": [
      "train/speech_enhancement/train.sh",
      "train/speech_enhancement/inference.sh",
      "train/speech_separation/train.sh",
      "train/speech_separation/inference.sh",
      "train/speech_super_resolution/train.sh",
      "train/speech_super_resolution/inference.sh",
      "train/target_speaker_extraction/train.sh",
      "train/target_speaker_extraction/evaluate_only.sh",
      "train/target_speaker_extraction_online/train.sh",
      "train/target_speaker_extraction_online/evaluate_only.sh",
      "train/data_generation/speech_enhancement/generate_noisy_speech/run.sh",
      "train/data_generation/speech_enhancement/generate_reverb_noisy_speech/run.sh"
    ],
    "tests": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source files under `clearvoice/`, `speechscore/`, `train/`, root dependency metadata, or README files changed, run `refresh-repo-skill`.
- Ignore expected production artifacts under `skills/` when comparing source-code cleanliness unless the user asks to refresh the generated skill itself.
- If `clearvoice` public signatures, supported model names, config layouts, or SpeechScore metric names change, run `refresh-repo-skill` even on the same commit.
