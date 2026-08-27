# GCP config template

## Purpose

Read this when creating or reviewing the AXLearn GCP CLI config file.

## Template shape

AXLearn stores GCP settings under a TOML table named `gcp."<project>:<env_id>"`.
Use this distilled template and replace every placeholder with your project values:

```toml
[gcp."my-gcp-project:us-central2-b"]
project = "my-gcp-project"
env_id = "us-central2-b"
zone = "us-central2-b"
network = "projects/my-gcp-project/global/networks/default"
subnetwork = "projects/my-gcp-project/regions/us-central2/subnetworks/default"
service_account_email = "ml-training@my-gcp-project.iam.gserviceaccount.com"
permanent_bucket = "public-permanent-us-central2"
private_bucket = "private-permanent-us-central2"
ttl_bucket = "ttl-30d-us-central2"
labels = "v4-tpu"
docker_repo = "us-docker.pkg.dev/my-gcp-project/axlearn"
default_dockerfile = "Dockerfile"
vertexai_tensorboard = "1231231231231231231"
vertexai_region = "us-central1"
```

## Field notes

- `project`, `env_id`, and `zone` identify the active environment.
- `network` and `subnetwork` are used by VM, TPU, GKE, and Dataflow workflows.
- `permanent_bucket` stores persistent artifacts such as checkpoints.
- `private_bucket` stores private or quota-related metadata.
- `ttl_bucket` stores temporary job assets and logs.
- `docker_repo` and `default_dockerfile` drive Docker-based bundlers.
- `labels` help `axlearn gcp config activate --label=...` select an environment.
- Vertex AI Tensorboard fields are optional and only needed for Tensorboard integration.

## Safe use

Do not commit real credentials or private project details unless the repository policy explicitly allows it. Prefer a user-local `.axlearn/.axlearn.config` or `~/.axlearn.config` for private settings.
