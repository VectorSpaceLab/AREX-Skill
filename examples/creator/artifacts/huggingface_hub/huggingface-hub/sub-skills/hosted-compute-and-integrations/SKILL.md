---
name: hosted-compute-and-integrations
description: "Routes hosted Jobs and Sandboxes, Space runtime configuration, OAuth and webhooks, framework/model integration, repository cards, tensor serialization, and TensorBoard logging workflows."
disable-model-invocation: true
license: Apache-2.0
metadata:
  disco-role: operating
---

# Hosted compute and integrations

Use this route when a task mentions Hugging Face Jobs, scheduled Jobs, a
Sandbox or SandboxPool, Space hardware/storage/secrets/variables, OAuth,
WebhooksServer, model-framework integration, model/dataset/Space cards, DDUF,
sharded checkpoints, safetensors, or TensorBoard traces.

## Choose the route

- Read [jobs-and-sandboxes.md](references/jobs-and-sandboxes.md) for Jobs,
  scheduled Jobs, hardware selection, volumes, logs, and sandbox lifecycle.
- Read [spaces-and-server-integrations.md](references/spaces-and-server-integrations.md)
  for Space runtime changes, secrets/variables, OAuth, webhook servers, and
  Hub-managed webhook registration.
- Read [model-integration-and-cards.md](references/model-integration-and-cards.md)
  for `ModelHubMixin`, `PyTorchModelHubMixin`, local save/load, cards,
  model-index metadata, and the local-versus-Hub TensorBoard writer boundary.
- Read [serialization.md](references/serialization.md) for DDUF, torch
  safetensors/pickle formats, sharding, index-file safety, and local round trips.
- Read [troubleshooting.md](references/troubleshooting.md) for optional
  dependencies, invalid resources/configuration, auth/network errors, and
  recovery decisions. It is also the route for distinguishing client wait
  timeouts from server Job/Space failures.

Run the safe local integration fixture with
[`scripts/local_integration_smoke.py`](scripts/local_integration_smoke.py)
before attempting any hosted operation. It creates a temporary model/card,
sharded checkpoint, DDUF archive, and mocked configuration recovery; it does
not contact the Hub or change a remote resource.

## Operating contract

1. **Classify side effects first.** `run_job`, scheduled-Job creation or
   triggering, `Sandbox.create`, `SandboxPool` warm-up, Space creation/upload,
   Space hardware/storage/secret/variable changes, webhook registration, card
   publishing, `push_to_hub`, and `HFSummaryWriter` are credentialed or
   side-effecting. Treat GPU/paid flavors, storage, and long-running processes
   as potentially billable. Use mocks or local fixtures until the user has
   explicitly authorized a real target.
2. **Pin the package contract.** Confirm the installed version and inspect the
   public signature before composing a command. Representative public APIs are
   listed in the linked references; do not infer new parameters from an old
   example. Experimental Sandbox, UV-job, OAuth, WebhooksServer, DDUF, and
   TensorBoard APIs can change, so pin a compatible `huggingface_hub` version.
3. **Separate configuration from execution.** Validate image, command, cron,
   volume URI, model/card metadata, checkpoint index, webhook route, and Space
   settings locally. Keep ordinary environment values in `env`/variables and
   sensitive values in encrypted Job/Space secrets where supported. Never print
   secret values or forward an HF token unless it is an explicit requirement.
4. **Choose resources deliberately.** Query available Jobs/Space hardware
   rather than hard-coding an assumption. A dedicated Sandbox supports GPU and
   stronger VM isolation; a SandboxPool is CPU-only, shares a host, accepts no
   per-sandbox volume, and does not provide the dedicated Job secret channel.
   Stop or pause paid resources when the work ends.
5. **Observe state, do not assume success.** Jobs move through `SCHEDULING` and
   `RUNNING` to `COMPLETED`, `CANCELED`, `ERROR`, or `DELETED`; `wait_for_job`
   returns failed final info rather than raising for a failed Job. Spaces may
   remain in build/start stages and need `wait_for_space`; inspect the returned
   stage and logs before retrying. A scheduled Job's immediate trigger does not
   alter its schedule.
6. **Prefer safe serialization.** Save torch weights as safetensors by default,
   validate the generated index and weight map, load with an explicit device and
   strictness policy, and treat pickle loading as unsafe for untrusted files.
   DDUF is a constrained diffusion archive, not a general-purpose ZIP.
7. **Preserve recovery evidence.** Record the input resource, requested versus
   actual state, credential scope, error/status message, and the corrective
   change. After a restart or webhook/OAuth change, re-read runtime/route state
   and perform a local or mocked request before repeating a remote mutation.

## Verification route

- Start with import/signature checks and the bundled local fixture.
- Assert local model config, card metadata, tensor keys/shapes, generated shard
  index paths, DDUF entry names, and round-trip values.
- For lifecycle logic, replace `HfApi` methods with autospecced mocks and feed
  staged `JobInfo`/`SpaceRuntime` results. Assert invalid configuration causes
  zero client calls, then assert the corrected plan calls only the mocks.
- Keep socket access blocked while the fixture runs. A green local result proves
  payload/config handling, not credentials, service capacity, billing, or a
  production callback. Escalate to live verification only with authorization.

## Minimal environment check

For a normal install, check only what the requested route needs:

```bash
python -c "import huggingface_hub; print(huggingface_hub.__version__)"
# Add torch and safetensors for serialization; add gradio for WebhooksServer;
# add the oauth extra for OAuth; add tensorboard or tensorboardX for logging.
```

Do not run the following during safe verification: hosted Job/Sandbox creation,
`SandboxPool` construction with warm-up, Space or endpoint resource changes,
secret writes/deletes, webhook create/update/delete, card/mixin uploads,
`push_to_hub`, live OAuth callbacks, `HFSummaryWriter` against a real repo, or
remote validation/downloads. Mock the client boundary and use local fixtures;
see [troubleshooting.md](references/troubleshooting.md) when a live check is
explicitly authorized.
