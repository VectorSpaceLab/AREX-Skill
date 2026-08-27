# Repository Provenance

## Purpose

Read this before deciding whether this Raster Vision skill is current for a checkout. If the current repo commit, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:07:58Z",
  "repository": {
    "name": "raster-vision",
    "remote_url": "https://github.com/azavea/raster-vision.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "fed86fb97ba522431cb12b32c356530695587dbf",
    "working_tree": "dirty-generated-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "rastervision",
      "version": "0.31.2-dev",
      "import_names": ["rastervision"]
    },
    {
      "name": "rastervision_pipeline",
      "version": "0.31.2-dev",
      "import_names": ["rastervision.pipeline"]
    },
    {
      "name": "rastervision_core",
      "version": "0.31.2-dev",
      "import_names": ["rastervision.core"]
    },
    {
      "name": "rastervision_pytorch_learner",
      "version": "0.31.2-dev",
      "import_names": ["rastervision.pytorch_learner"]
    },
    {
      "name": "rastervision_pytorch_backend",
      "version": "0.31.2-dev",
      "import_names": ["rastervision.pytorch_backend"]
    },
    {
      "name": "rastervision_aws_s3",
      "version": "0.31.2-dev",
      "import_names": ["rastervision.aws_s3"]
    },
    {
      "name": "rastervision_aws_batch",
      "version": "0.31.2-dev",
      "import_names": ["rastervision.aws_batch"]
    },
    {
      "name": "rastervision_aws_sagemaker",
      "version": "0.31.2-dev",
      "import_names": ["rastervision.aws_sagemaker"]
    },
    {
      "name": "rastervision_gdal_vsi",
      "version": "0.31.2-dev",
      "import_names": ["rastervision.gdal_vsi"]
    }
  ],
  "evidence": {
    "source_roots": [
      "rastervision_pipeline/rastervision/pipeline",
      "rastervision_core/rastervision/core",
      "rastervision_pytorch_learner/rastervision/pytorch_learner",
      "rastervision_pytorch_backend/rastervision/pytorch_backend",
      "rastervision_aws_s3/rastervision/aws_s3",
      "rastervision_aws_batch/rastervision/aws_batch",
      "rastervision_aws_sagemaker/rastervision/aws_sagemaker",
      "rastervision_gdal_vsi/rastervision/gdal_vsi"
    ],
    "docs": [
      "README.md",
      "docs/setup",
      "docs/framework",
      "docs/usage"
    ],
    "examples": [
      "rastervision_pytorch_backend/rastervision/pytorch_backend/examples",
      "integration_tests"
    ],
    "tests": [
      "tests/pipeline",
      "tests/core",
      "tests/pytorch_backend",
      "tests/pytorch_learner",
      "tests/aws_batch",
      "tests/aws_s3",
      "tests/aws_sagemaker",
      "tests/gdal_vsi"
    ],
    "configs": [
      "pyproject.toml",
      "rastervision_*/pyproject.toml",
      "rastervision_*/requirements.in",
      "requirements.txt",
      "cloudformation",
      "docker",
      "scripts"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If public config classes, CLI commands, runner names, package versions, or example keys changed, refresh even if the commit looks close.
- The recorded dirty path is the generated `skills/` output from this production run; ignore it only when comparing the source checkout to this exact skill generation baseline.
- Do not compare local environment paths against this file; the runtime skill intentionally omits private inspection-environment details.
