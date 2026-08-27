# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, source roots, or public workflow evidence differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T13:10:14Z",
  "repository": {
    "name": "audio-diffusion-pytorch",
    "remote_url": "https://github.com/archinetai/audio-diffusion-pytorch.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f4052e321c820e467e51e14d005f3d0077997278",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/ (untracked local skill/log artifacts; package source files were clean at initial analysis)"
    ]
  },
  "packages": [
    {
      "name": "audio-diffusion-pytorch",
      "version": "0.1.3",
      "import_names": ["audio_diffusion_pytorch"]
    }
  ],
  "evidence": {
    "source_roots": ["audio_diffusion_pytorch/"],
    "docs": ["README.md"],
    "examples": ["README.md snippets"],
    "tests": ["tests/testcustomloss.py"],
    "configs": [],
    "scripts": [],
    "packaging": ["setup.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If package metadata, import names, dependencies, or exported public constructors change, refresh the skill.
- If the README gains new first-class workflows, examples, checkpoints, or CLI guidance, refresh the routing and references.
- If the current checkout has source-file changes outside generated skill artifacts, refresh before relying on this snapshot.
