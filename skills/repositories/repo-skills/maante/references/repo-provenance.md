# Repository Provenance

## Purpose

Read this before deciding whether this MaaNTE skill is current for a checkout. If the current commit, source layout, task catalog, or MaaFramework/runtime assumptions differ materially from this snapshot, run `refresh-repo-skill` before relying on version-sensitive guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T21:14:23Z",
  "repository": {
    "name": "MaaNTE",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "dev",
    "tag": "v1.3.1",
    "commit": "4ebdd899089014965763d867c387b6755a6e045c",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "maafw",
      "version": "5.10.4",
      "import_names": ["maa"]
    }
  ],
  "evidence": {
    "source_roots": [
      "agent/main.py",
      "agent/custom/action",
      "agent/utils"
    ],
    "assets_and_configs": [
      "assets/interface.json",
      "assets/resource/tasks",
      "assets/resource/base/pipeline",
      "assets/resource/base/image",
      "assets/resource/base/routes",
      "assets/resource/locales/interface"
    ],
    "docs": [
      "README.md",
      "AGENTS.md",
      "docs/zh_cn/develop",
      "docs/zh_cn/introduction",
      "docs/eng/trouble_shooting.md",
      "docs/zh_cn/问题排查.md"
    ],
    "repo_local_skills": [
      ".claude/skills/maa-logging/SKILL.md",
      ".claude/skills/pipeline-guide/SKILL.md",
      ".claude/skills/python-action-guide/SKILL.md",
      ".claude/skills/task-config/SKILL.md",
      ".claude/skills/maante-issue-log-analysis/SKILL.md",
      ".claude/skills/maante-cyber-fortune-master/SKILL.md"
    ],
    "scripts_and_tools": [
      "build.py",
      "scripts/update_navi_coordinate_transform.py",
      "tools/demo_coordinate_capture.py",
      "tools/i18n/sync_ocr_expected.py"
    ],
    "native_tests": [
      "docs/zh_cn/develop/node-testing.md notes automated node tests are not yet ready",
      "assets/resource/tasks/LocalRouteNavigationMemoryTest.json",
      "assets/resource/base/pipeline/LocalRouteNavigationMemoryTest.json",
      "assets/resource/routes/test.json"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `4ebdd899089014965763d867c387b6755a6e045c`, treat this skill as potentially stale.
- If `requirements.txt`, `assets/interface.json`, `agent/custom/action/__init__.py`, any task JSON, or major Pipeline JSON files changed, refresh the task catalog and sub-skill references.
- If MaaFramework (`maafw`), MXU/MFAA packaging versions, Python target version, controller types, or navigation coordinate API versions changed, refresh setup/runtime guidance.
- Generated skill files were written after the clean source snapshot; do not count the skill's own output files as evidence of source dirtiness.
