# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Porcupine. If the current repo commit, dirty state, package version, public SDK surface, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T19:52:29Z",
  "repository": {
    "name": "porcupine",
    "remote_url": "https://github.com/Picovoice/porcupine.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "b42ec9f849c05bb2aa99e6cbd1c85c9b66e103bb",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "pvporcupine",
      "version": "4.0.3",
      "import_names": ["pvporcupine"]
    },
    {
      "name": "@picovoice/porcupine-node",
      "version": "4.0.2",
      "import_names": ["@picovoice/porcupine-node"]
    },
    {
      "name": "@picovoice/porcupine-web",
      "version": "4.0.1",
      "import_names": ["@picovoice/porcupine-web"]
    },
    {
      "name": "@picovoice/porcupine-react",
      "version": "4.0.0",
      "import_names": ["@picovoice/porcupine-react"]
    },
    {
      "name": "@picovoice/porcupine-react-native",
      "version": "4.0.0",
      "import_names": ["@picovoice/porcupine-react-native"]
    },
    {
      "name": "porcupine_flutter",
      "version": "4.0.0",
      "import_names": ["porcupine_flutter"]
    },
    {
      "name": "Porcupine-iOS",
      "version": null,
      "import_names": ["Porcupine"]
    },
    {
      "name": "Porcupine",
      "version": null,
      "import_names": ["Porcupine"]
    }
  ],
  "evidence": {
    "source_roots": [
      "binding/python",
      "binding/nodejs/src",
      "binding/web/src",
      "binding/react/src",
      "binding/android/Porcupine/porcupine/src",
      "binding/java/src",
      "binding/dotnet/Porcupine",
      "binding/ios",
      "binding/flutter/lib",
      "binding/react-native/src",
      "include"
    ],
    "docs": [
      "README.md",
      "binding/python/README.md",
      "binding/nodejs/README.md",
      "binding/web/README.md",
      "binding/react/README.md",
      "binding/android/README.md",
      "binding/java/README.md",
      "binding/dotnet/README.md",
      "binding/ios/README.md",
      "binding/flutter/README.md",
      "binding/react-native/README.md",
      "demo/*/README.md",
      "lib/README.md",
      "resources/keyword_files/README.md"
    ],
    "examples": [
      "demo/python",
      "demo/nodejs",
      "demo/web",
      "demo/react",
      "demo/c",
      "demo/java",
      "demo/dotnet",
      "demo/android",
      "demo/ios",
      "demo/flutter",
      "demo/react-native",
      "demo/mcu"
    ],
    "tests": [
      "binding/python/test_porcupine.py",
      "binding/nodejs/test/index.test.ts",
      "binding/web/test",
      "binding/react/test",
      "binding/java/test",
      "binding/dotnet/PorcupineTest",
      "binding/android/PorcupineTestApp",
      "binding/ios/PorcupineAppTest",
      "demo/c/test",
      "resources/.test/test_data.json"
    ],
    "configs_and_assets": [
      "Package.swift",
      "binding/*/package.json",
      "binding/python/setup.py",
      "binding/flutter/pubspec.yaml",
      "resources/keyword_files*",
      "resources/audio_samples",
      "lib/common"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package versions, public entry points, built-in keyword/resource layout, or SDK install channels changed, run `refresh-repo-skill`.
- If a checkout is clean and differs only by not having generated `skills/` artifacts, that alone does not imply Porcupine source drift; compare source, docs, package metadata, and resources.
