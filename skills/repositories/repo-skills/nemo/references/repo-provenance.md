# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of NVIDIA NeMo Speech. If the current repo commit, dirty state, package version, active collections, docs, examples, scripts, or public APIs differ from this snapshot, run `refresh-repo-skill` before relying on version-sensitive guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T16:49:30Z",
  "repository": {
    "name": "NeMo",
    "remote_url": "https://github.com/NVIDIA-NeMo/NeMo.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "8f85359bf29638682816dd53badf4893de8a75a3",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "nemo-toolkit",
      "version": "3.1.0+8f85359",
      "import_names": ["nemo"]
    }
  ],
  "evidence": {
    "source_roots": [
      "nemo",
      "nemo/collections/asr",
      "nemo/collections/tts",
      "nemo/collections/audio",
      "nemo/collections/speechlm2",
      "nemo/collections/common",
      "nemo/core",
      "nemo/utils",
      "nemo/agents/voice_agent"
    ],
    "docs": [
      "README.md",
      "docs/source/starthere/install.rst",
      "docs/source/asr",
      "docs/source/tts",
      "docs/source/audio",
      "docs/source/speechlm2",
      "docs/source/tools",
      "docs/source/dataloaders.rst",
      "docs/source/common",
      "docs/source/core"
    ],
    "examples": [
      "examples/asr",
      "examples/tts",
      "examples/audio",
      "examples/speechlm2",
      "examples/speaker_tasks",
      "examples/voice_agent"
    ],
    "scripts": [
      "scripts/speech_recognition",
      "scripts/tokenizers",
      "scripts/dataset_processing",
      "scripts/speaker_tasks",
      "scripts/voice_activity_detection",
      "scripts/speechlm2",
      "scripts/checkpoint_averaging",
      "scripts/tts_comparison_report"
    ],
    "tools": [
      "tools/asr_evaluator",
      "tools/ctc_segmentation",
      "tools/nemo_forced_aligner",
      "tools/speech_data_explorer",
      "tools/speech_data_simulator",
      "tools/customization_dataset_preparation"
    ],
    "tests": [
      "tests/collections/asr",
      "tests/collections/tts",
      "tests/collections/audio",
      "tests/collections/speechlm2",
      "tests/collections/speaker_tasks",
      "tests/collections/common",
      "tests/core",
      "tests/lightning",
      "tests/utils",
      "tools/nemo_forced_aligner/tests",
      "tools/customization_dataset_preparation/tests"
    ],
    "configs": [
      "pyproject.toml",
      "uv.lock",
      "examples/asr/conf",
      "examples/tts/conf",
      "examples/audio/conf",
      "examples/speechlm2/conf",
      "examples/speaker_tasks/recognition/conf"
    ],
    "existing_agent_guidance": [
      "CLAUDE.md",
      "AGENTS.md",
      ".claude/skills/nemo-speech-asr-finetune"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has non-skill dirty paths that differ from the snapshot, run `refresh-repo-skill` before trusting API or workflow details.
- If `nemo-toolkit` package metadata, collection extras, install instructions, public model classes, example command signatures, or docs changed, refresh the skill.
- If the active NeMo repository has been split, renamed, or restored non-speech collections not covered here, refresh or extend the skill rather than assuming coverage.
