# Client and Data Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `MetaflowNotFound` for a run that exists | Namespace filtering or metadata provider mismatch | Check `get_namespace()` and `get_metadata()`. Use `namespace(None)` only when intentionally disabling filtering. |
| Pathspec error | Wrong number of path components | Use `Flow`, `Run`, `Step`, `Task`, or `DataArtifact` with the exact pathspec depth. |
| Artifact read fails on cloud datastore | Credentials, service endpoint, or datastore root issue | Verify provider-specific config and credentials outside the generated skill. Do not treat CPU import as cloud verification. |
| `You need to install 'boto3' in order to use S3` | S3 datatools dependency missing | Install Metaflow with base dependencies or add boto3 to the step environment. |
| Logs command returns nothing | Wrong task pathspec or logs stored in a different datastore/metadata context | Query the run/task first, then use `logs show` in the same environment/profile. |
| IncludeFile cannot open file | Local path missing at parameter evaluation time | Materialize the file locally before the run or pass a pointer string. |
