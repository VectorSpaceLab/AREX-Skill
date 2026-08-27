# Repository Maintenance Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| User asks for code changes but no approved issue | External-contributor gate blocks implementation | Ask for the issue; point to contribution guide and issue labels. |
| Core runtime PR lacks reproduction | Higher-bar area touched | Require minimal reproduction in the real execution mode and a technical rationale. |
| `pytest` or `mocker` fixture missing | Dev test dependencies not installed | Install focused test dependencies only after user approval, or run static/source review. |
| S3/data tests fail with credentials | Service root or MinIO/AWS credentials missing | Configure service test root or skip as service-blocked. |
| Pre-commit fails | Formatting, JSON/YAML, or shellcheck issue | Run hooks locally and fix the exact file category. |
| Devstack hangs or mutates host state | Docker/Kubernetes service workflow started without enough resources | Stop devstack and ask before restarting. |
