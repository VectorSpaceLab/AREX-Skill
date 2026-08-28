# Sandbox, Artifacts, and Remote Device

## Three file/code capabilities

- **Artifact Generator** keeps a structured spec and creates/edits/rewrites versioned PPTX, DOCX, XLSX, PDF or HTML artifacts.
- **Code Executor** runs Python in a stateful, conversation/run-scoped sandbox and captures output files as artifacts.
- **Read Document** parses files to text, Markdown, structured JSON/tables or chunks through the parsing worker; it is workflow-only in the picker.

File bytes are not injected into model context; artifact references and compact summaries are.

## Sandbox backends

### Jupyter gateway

Self-hosted runner selected by `SANDBOX_BACKEND=jupyter`. Configure gateway URL/token and a hardened kernelspec. Do not use a stock kernel that inherits operator secrets. Enforce container network, CPU, memory, session, execution, input/output and file limits.

### Daytona

Managed backend selected by `SANDBOX_BACKEND=daytona`. Configure key/API URL/target/snapshot and lifecycle/cap limits. Artifact rendering needs `python-pptx`, `python-docx`, `openpyxl`, and `reportlab` in the snapshot; HTML works without those render libraries.

Building a cloud snapshot creates external resources and is not bundled as a safe helper. Review image provenance, packages, cost and cleanup before running a snapshot builder.

## Safe execution

- Keep code/artifact tools out of default chat tools until the runner passes isolation tests.
- Use approval for model-authored code where human confirmation is required.
- Bind session TTL/concurrency and output/file quotas.
- Scrub environment secrets from kernels.
- Deny unrestricted network/host mounts.
- Validate artifacts by MIME/signature, not filename alone.

## Remote Device

A `docsgpt-cli host` daemon connects outward, pairs with a one-time code, and exposes `run_command` to an agent. No inbound port is required.

Approval modes:

- **Ask**: each command pauses; a user may approve a pattern.
- **Full access**: ordinary commands run without prompting, but the built-in catastrophic-command denylist still forces approval.

Compound commands are split and checked part by part. Each device has a revocable token and server-side audit log.

Operational sequence:

1. create a named device with a narrow description and Ask mode;
2. pair with the one-time code;
3. run daemon in foreground first;
4. verify status and one harmless command;
5. install service only after choosing correct system/user identity;
6. attach to one draft agent;
7. inspect audit output and revoke/reset behavior.

Use Full access only on a disposable or tightly isolated machine. The denylist is not a general sandbox.
