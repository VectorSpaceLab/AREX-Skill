# Repository Provenance

## Purpose

Read this before deciding whether this skill matches the current checkout of Lumina-T2X. If the repo commit, dirty state, package version, or evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T10:52:52Z",
  "repository": {
    "name": "Lumina-T2X",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1c606962f95899da711633ee3a333d21c753e2d9",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "lumina-t2x",
      "version": "1.5.0",
      "import_names": ["lumina_t2i", "lumina_next_t2i", "lumina_next_t2i_mini", "visual_anagrams"]
    }
  ],
  "evidence": {
    "source_roots": [
      "lumina_t2i",
      "lumina_next_t2i",
      "lumina_next_t2i_mini",
      "lumina_next_compositional_generation",
      "lumina_audio",
      "lumina_music",
      "visual_anagrams",
      "Flag-DiT-ImageNet",
      "Next-DiT-ImageNet",
      "Next-DiT-MoE"
    ],
    "docs": ["README.md", "README_cn.md"],
    "examples": [
      "lumina_next_t2i/sample.py",
      "lumina_next_t2i_mini/sample.py",
      "lumina_next_t2i_mini/sample_img2img.py",
      "lumina_next_t2i_mini/sample_sd3.py",
      "visual_anagrams/generate.py",
      "visual_anagrams/animate.py"
    ],
    "tests": [],
    "configs": [
      "pyproject.toml",
      "requirements.txt",
      "lumina_t2i/configs",
      "lumina_next_t2i/configs",
      "lumina_next_t2i_mini/configs",
      "lumina_audio/configs",
      "lumina_music/configs",
      "visual_anagrams/environment.yml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, treat the skill as potentially stale.
- If the working tree becomes dirty in ways that affect the source evidence paths, refresh the skill.
- If the public package version or console-script layout changes, refresh the skill.
