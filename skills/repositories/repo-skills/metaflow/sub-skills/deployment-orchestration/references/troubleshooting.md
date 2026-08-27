# Deployment Orchestration Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `*@batch* decorator requires --datastore=s3` | Batch needs S3-backed code/artifacts/log bridge | Configure S3 datastore root and rerun with `--datastore=s3`. |
| `*@kubernetes* decorator requires --datastore=s3 or --datastore=azure or --datastore=gs` | Kubernetes remote tasks need non-local datastore | Select and verify a cloud datastore before running remote tasks. |
| Step marked for both Batch and Kubernetes | Mutually exclusive compute decorators | Choose exactly one backend per step or run. |
| `@parallel` with `@catch` rejected on Kubernetes | Unsupported decorator combination | Remove `@catch`, change backend, or redesign fallback behavior. |
| Timeout below 60 seconds rejected remotely | Remote backends enforce minimum runtime limit | Increase `@timeout` or provider runtime limit to at least 60 seconds. |
| Missing Kubernetes/Boto/Airflow/Argo imports | Optional provider dependencies absent | Install only the provider dependencies required by the selected backend. |
| Access denied or service not found | Credentials, roles, namespace, bucket, service URL, or cluster not configured | Stop and verify provider configuration before retrying mutating commands. |
