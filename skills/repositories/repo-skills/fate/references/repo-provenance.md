# FATE repo provenance

This provenance snapshot lets future agents decide whether the generated operating skill is stale relative to a different FATE checkout or installed package set.

```json
{
  "schema_version": "repo-provenance.v1",
  "repository": {
    "name": "FATE",
    "remote_url": "https://github.com/FederatedAI/FATE.git",
    "branch": "master",
    "tag": null,
    "commit": "5a06d9e4c4cd7ab97a5c8357828adbffaca87785",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "generated_at_utc": "2026-08-15T06:33:47Z"
  },
  "packages": [
    {
      "distribution": "pyfate",
      "version": "2.2.0",
      "import_names": ["fate"]
    },
    {
      "distribution": "fate_client",
      "version": "2.2.0",
      "import_names": ["fate_client"]
    },
    {
      "distribution": "fate_flow",
      "version": "2.2.0",
      "import_names": ["fate_flow"]
    },
    {
      "distribution": "fate_utils",
      "version": "0.1.0",
      "import_names": ["fate_utils"]
    }
  ],
  "evidence": {
    "source_roots": [
      "python/fate",
      "rust/fate_utils"
    ],
    "docs": [
      "README.md",
      "doc/README.md",
      "doc/2.0/fate"
    ],
    "examples": [
      "examples/data",
      "examples/launchers",
      "examples/pipeline"
    ],
    "tests": [
      "python/fate/test",
      "python/fate/ml",
      "rust/fate_utils/tests"
    ],
    "configs": [
      "pyproject.toml",
      "python/setup.py",
      "python/requirements.txt",
      "python/requirements-fate.txt",
      "python/requirements-eggroll.txt",
      "python/requirements-rabbitmq.txt",
      "python/requirements-pulsar.txt",
      "python/requirements-spark.txt",
      "examples/data/upload_config",
      "deploy"
    ],
    "scripts": [
      "bin/service.sh",
      "bin/init_env.sh",
      "bin/install_os_dependencies.sh",
      "deploy/docker-compose/docker-deploy/docker_deploy.sh",
      "deploy/docker-compose/docker-deploy/generate_config.sh",
      "examples/launchers/launcher.py",
      "examples/launchers/run.sh",
      "proto/generate_proto_buffer.sh"
    ]
  },
  "construction_notes": [
    "Submodules such as fate_client, fate_flow, fate_board, fate_test, eggroll, and related service repositories were uninitialized in the checkout and treated as external installed dependencies.",
    "The verified baseline was CPU package inspection. GPU, DeepSpeed, Spark, Eggroll cluster, RabbitMQ, Pulsar, and Docker-cluster execution were not verified defaults.",
    "Deployment and cluster shell scripts were used as reference evidence; destructive service, Docker, SSH, or host mutation commands were not bundled as runnable root actions."
  ]
}
```
