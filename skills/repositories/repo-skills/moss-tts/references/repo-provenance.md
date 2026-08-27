# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of MOSS-TTS. If the current repo commit, dirty state, package metadata, public entry points, or evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T21:30:00Z",
  "repository": {
    "name": "MOSS-TTS",
    "remote_url": "https://github.com/OpenMOSS/MOSS-TTS.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "58b20a0d5fcc6766658d50967a90a9d890009a46",
    "working_tree": "clean-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "moss-tts",
      "version": "0.1.0",
      "import_names": [
        "moss_tts_delay",
        "moss_tts_delay.llama_cpp",
        "moss_tts_local",
        "moss_tts_local_v1.5",
        "moss_tts_realtime.mossttsrealtime"
      ]
    },
    {
      "name": "moss-soundeffect-v2",
      "version": "0.1.0",
      "import_names": ["moss_soundeffect_v2"]
    }
  ],
  "evidence": {
    "package_metadata": ["pyproject.toml", "moss_soundeffect_v2/pyproject.toml", "MANIFEST.in"],
    "source_roots": [
      "moss_tts_delay",
      "moss_tts_delay/llama_cpp",
      "moss_tts_local",
      "moss_tts_local_v1.5",
      "moss_tts_realtime/mossttsrealtime",
      "moss_soundeffect_v2"
    ],
    "docs": [
      "README.md",
      "README_zh.md",
      "docs/moss_tts_model_card.md",
      "docs/moss_ttsd_model_card.md",
      "docs/moss_voice_generator_model_card.md",
      "docs/moss_tts_realtime_model_card.md",
      "docs/moss_sound_effect_model_card.md",
      "moss_tts_delay/README.md",
      "moss_tts_delay/llama_cpp/README.md",
      "moss_tts_local/README.md",
      "moss_tts_local_v1.5/README.md",
      "moss_tts_realtime/README.md",
      "moss_soundeffect_v2/README.md"
    ],
    "configs": ["configs/llama_cpp"],
    "workflow_sources": [
      "clis",
      "scripts",
      "moss_tts_delay/finetuning",
      "moss_tts_local/finetuning",
      "moss_tts_local_v1.5/finetuning",
      "moss_tts_realtime/finetuning",
      "moss_soundeffect_v2/finetuning"
    ],
    "fixtures": ["assets/text", "assets/audio"]
  },
  "verification_scope": {
    "required_backend": "cpu/any lightweight inspection",
    "optional_unverified_backends": [
      "CUDA HF generation",
      "FlashAttention",
      "TensorRT",
      "full model downloads",
      "FastAPI/Gradio service startup",
      "training and benchmark runs",
      "SoundEffect v2 CUDA/Triton generation"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, optional dependency groups, console entry points, model cards, prompt templates, preprocessing/training flags, or public service endpoints changed, run `refresh-repo-skill` even on the same commit.
- If the current working tree contains local edits in evidence paths listed above, verify whether those edits affect APIs, commands, configs, or data formats before relying on this skill.
