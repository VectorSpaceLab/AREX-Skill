# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the Cream monorepo.
If the repository commit, dirty state, or major evidence paths changed, refresh the skill instead of reusing it blindly.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T19:20:47Z",
  "repository": {
    "name": "Cream",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4a13c4091e78f9abd2160e7e01c02e48c1cf8fb9",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "open_clip_torch",
      "version": "2.0.2",
      "import_names": ["open_clip"]
    }
  ],
  "evidence": {
    "source_roots": [
      "AutoFormer",
      "AutoFormerV2",
      "CDARTS",
      "Cream",
      "EfficientViT",
      "MiniViT",
      "TinyCLIP",
      "TinyViT",
      "iRPE"
    ],
    "docs": [
      "README.md",
      "AutoFormer/README.md",
      "AutoFormerV2/README.md",
      "CDARTS/README.md",
      "Cream/README.md",
      "EfficientViT/README.md",
      "MiniViT/README.md",
      "TinyCLIP/README.md",
      "TinyViT/README.md",
      "iRPE/README.md"
    ],
    "examples": [],
    "tests": [
      "TinyViT/tests"
    ],
    "configs": [
      "AutoFormer/experiments",
      "AutoFormerV2/configs",
      "CDARTS/experiments",
      "Cream/experiments/configs",
      "EfficientViT/downstream/configs",
      "MiniViT/Mini-Swin/configs",
      "TinyCLIP/src/open_clip/model_configs",
      "TinyViT/configs"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as stale and run `refresh-repo-skill`.
- If the current checkout has a different dirty-path summary from the snapshot, refresh before relying on the skill for repo-specific claims.
- If the imported package version or key public entry points changed, refresh before reuse.

## Notes

- The snapshot was captured from a dirty checkout that already had an untracked `skills/` directory.
- The generated runtime skill tree and review artifacts are intentionally excluded from the source baseline above.
- Private environment paths, activation commands, and local installation locations are omitted by design.
