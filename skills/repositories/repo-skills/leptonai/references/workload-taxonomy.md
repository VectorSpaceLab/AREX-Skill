# Lepton workload taxonomy

Read this when a user describes a Lepton compute need without naming the exact workload type.

| Workload | Lifetime | Replica model | Best for | Usually not for |
| --- | --- | --- | --- | --- |
| Endpoint | Long-running service | Autoscaled replicas, can scale to zero | HTTP inference, embedding, chat/model serving, custom container APIs | One-off training or interactive notebooks |
| Dev pod | Long-lived interactive machine | Single pod | SSH/Jupyter/debugging/IDE/data exploration | Production serving or distributed completion jobs |
| Batch job | Finite run to completion | Parallelism/completions workers | Training, evaluation, sweeps, data processing, scheduled finite work | Persistent service traffic or interactive dev |
| Ray cluster | Long-running distributed cluster | Head plus worker groups | Ray actors, distributed Python pipelines, RL/data processing | Simple one-off shell command |
| Fine-tuning job | Finite guided training | Recipe/trainer-driven job | Model fine-tuning with supported trainers/models/datasets | Fully custom training entrypoint; use batch job instead |
| Slurm cluster | Long-running managed HPC cluster | Controller/login nodes | Teams already using Slurm workflows | Self-serve creation from ordinary `lep` commands |
| Storage | Workspace file system, not compute | Persistent files | Data/model artifact transfer and mounts | Secrets or endpoint traffic routing |
| Ingress | Routing resource, not compute | Weighted endpoint list | Domain/canary traffic routing across endpoints | Deploying endpoint containers |

## Decision rules

- If the task says **serve**, **API**, **HTTP**, **replicas**, **scale**, **tokens**, or **public/IP allowlist**, choose endpoint plus storage/ingress if needed.
- If the task says **SSH**, **Jupyter**, **notebook**, **interactive**, **debug machine**, or **remote shell**, choose dev pod.
- If the task says **train once**, **evaluate**, **process dataset**, **sweep**, **schedule**, or **completion**, choose batch job.
- If the task says **Ray**, **actors**, **head/worker**, **Ray job**, or **autoscaling distributed Python**, choose Ray cluster.
- If the task says **fine-tune**, **trainer**, **base model**, **dataset recipe**, or **LoRA/SFT through Lepton**, choose fine-tuning job unless full custom control is required.
- If the task says **storage mount**, **upload/download**, **secret**, **ingress**, **canary**, or **IP allowlist**, route to `storage-secrets-ingress` for that part and to `workload-management` for any compute workload.

## Read-first commands

Use read-only commands after workspace context is established:

```bash
lep endpoint list
lep pod list --detail
lep job list
lep raycluster list
lep finetune list
lep node resource-shape --purpose deployment
lep ingress list
lep storage ls /
lep secret list
```

Do not treat a read-only command as non-credentialed: most commands still require workspace auth and network access.
