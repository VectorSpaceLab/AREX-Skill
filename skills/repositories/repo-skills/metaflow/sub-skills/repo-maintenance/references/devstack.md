# Devstack and Service Workflows

Metaflow's devtools can run local service stacks such as MinIO, metadata service, PostgreSQL, Minikube, Argo, Airflow, Step Functions Local, and UI components. These workflows can start Docker containers, Kubernetes resources, port forwards, and persistent local state.

Use devstack only after explicit user approval and enough host resources. Typical docs refer to:

```bash
cd devtools
make up
make down
```

When testing S3 behavior with MinIO, verify bucket, endpoint, access key, secret key, and `METAFLOW_S3_TEST_ROOT`. Do not bake sample credentials or local ports into runtime skill content.

Devstack scripts and Tilt files are reference-only here because they are service-affecting and tied to a source checkout.
