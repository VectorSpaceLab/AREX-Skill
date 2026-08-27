# Repository provenance

Read this before using the Open-Assistant repo skill against a checkout. If the current checkout differs in source commit, service layout, package versions, public schemas, or package scripts, treat the skill as potentially stale and run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T13:48:31Z",
  "repository": {
    "name": "Open-Assistant",
    "remote_url": "https://github.com/LAION-AI/Open-Assistant.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f1e6ed9526f5817531f3ab85441a40b3671ddccb",
    "working_tree_state": "dirty-generated-artifacts-only",
    "dirty_paths": ["skills/"],
    "working_tree_note": "source tree observed at this commit; dirty state was generated skill/review artifacts under skills/"
  },
  "skill": {
    "id": "open-assistant",
    "role": "operating",
    "import_policy": "not-imported-by-request",
    "scope": ["backend", "oasst-shared", "oasst-data", "website", "inference"]
  },
  "packages": [
    {
      "name": "oasst_shared",
      "version": "1.0.0",
      "import_names": ["oasst_shared"],
      "entry_points": []
    },
    {
      "name": "oasst_data",
      "version": "1.0.0",
      "import_names": ["oasst_data"],
      "entry_points": []
    },
    {
      "name": "oasst_backend",
      "version": null,
      "import_names": ["oasst_backend"],
      "entry_points": ["backend/main.py"]
    },
    {
      "name": "website",
      "version": "0.1.0",
      "import_names": [],
      "entry_points": ["npm run dev", "npm run lint", "npm run typecheck", "npm run jest", "npm run cypress:run"]
    },
    {
      "name": "inference server/worker",
      "version": null,
      "import_names": ["inference.server", "inference.worker"],
      "entry_points": ["inference/server/main.py", "inference/worker/__main__.py", "inference/text-client/__main__.py"]
    }
  ],
  "verified_environment_summary": {
    "python": "3.10.20",
    "pip": "24.0",
    "required_backends": ["cpu"],
    "optional_backends": ["cuda real-model inference", "docker service e2e stack", "node website dependency install"]
  },
  "evidence": {
    "source_roots": [
      "backend/",
      "oasst-shared/",
      "oasst-data/",
      "website/",
      "inference/server/",
      "inference/worker/",
      "inference/text-client/",
      "inference/safety/"
    ],
    "root_files": ["README.md", "docker-compose.yaml", "pyproject.toml"],
    "support_scripts": [
      "scripts/backend-development/",
      "scripts/frontend-development/",
      "scripts/oasst-shared-development/"
    ],
    "excluded_roots": [
      "model/ heavy model-training/evaluation/pretokenizer stack",
      "notebooks/ exploratory material",
      "deploy/ and ansible/ infrastructure deployment",
      "docs/ docs-site maintenance except setup evidence",
      ".github/ CI metadata except high-level setup signals"
    ]
  }
}
```

## Refresh triggers

Run `refresh-repo-skill` if any of these are true:

- `git rev-parse HEAD` differs from `f1e6ed9526f5817531f3ab85441a40b3671ddccb` and the task depends on changed backend, data, website, or inference behavior.
- `backend/`, `oasst-shared/`, `oasst-data/`, `website/`, `inference/`, or `docker-compose.yaml` changed materially.
- `oasst_shared` or `oasst_data` version, schema names, API-client methods, or JSONL export model fields changed.
- Website package scripts or `website/src` task/chat/API-client structure changed.
- Inference server routes, worker websocket protocol version, model-config registry, or text-client behavior changed.
- The user needs excluded `model/` training/evaluation/pretokenizer coverage; use `extend-repo-skill` rather than assuming this skill covers it.

Generated `skills/` artifacts being present in a local checkout are not by themselves a refresh trigger.
