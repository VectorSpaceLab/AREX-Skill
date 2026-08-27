# Safety, approval, and trust boundaries

## The approval ladder

Treat a model tool request as a proposed side effect, not as a command to run.
Use this order at the application boundary:

1. **Parse:** accept only a bounded JSON shape; reject malformed JSON, unknown
   envelopes, duplicate/empty names, non-object arguments, and oversized input.
2. **Admit the tool:** compare the exact name to a narrow allowlist. A schema
   description or MCP discovery result never grants admission.
3. **Validate arguments:** use strict schema validation, then apply business
   rules such as enum/range checks, approved resource IDs, workspace roots,
   URL hosts, and maximum result size.
4. **Ask for approval where impact requires it:** human approval is required for
   deletion, writes outside a disposable workspace, external messages,
   purchases, credential use, network calls, package installation, code
   execution, or any irreversible operation. Show the normalized name and
   redacted arguments, not secrets.
5. **Execute in the narrowest boundary:** use a wrapper that enforces the
   policy, not only a prompt or a model requirement. Apply timeouts, output
   caps, resource quotas, and artifact handling.
6. **Observe and audit:** record identity, tool name, decision, policy version,
   duration, success/failure, and a redacted result. Never log raw tokens,
   authorization headers, full private paths, or untrusted payloads by default.

A `uses_tool` requirement, a tool schema, `allowed_paths`, an import allowlist,
or a declared `CapabilityPolicy` is not by itself a complete approval boundary.
Use the static checker as an advisory preflight; a clean report is not an
execution authorization.

## Execution tiers and honest policy claims

| Choice | What it really provides | Safe claim |
|---|---|---|
| `static` | AST/import or shell parsing only; no execution | “Inspected without executing.” |
| `local_unsafe` | Host subprocess, no policy/isolation | “Trusted local code.” |
| `local` | Host subprocess; timeout and output/artifact controls can apply | “Host execution with limited enforced controls.” |
| `docker_unsafe` | llm-sandbox/Docker boundary, no declared policy | “Container execution without policy declarations.” |
| `docker` | llm-sandbox/Docker plus declared policy and selected enforced limits | “Container execution with enforced runtime limits.” |

`CapabilityPolicy.ENFORCED_*` is the source of truth for the current runtime.
Timeout, stdout/stderr truncation, artifact export paths, and package handling
are enforced. Filesystem read/write roots, `network_access`,
`package_installation`, `subprocess_execution`, and `env_var_access` are
reported as declarative-only fields in this version. In particular, a
`local` policy with `network_access=False` does **not** prevent a child process
from opening a socket. Docker is a stronger process boundary, but do not claim
that the policy's network boolean blocks egress unless the surrounding Docker
runtime actually supplies that restriction.

Python `allowed_imports` is an AST preflight check of top-level imports, not a
complete capability sandbox: dynamic imports, native extensions, existing
scripts, subprocesses, and data exfiltration require a real isolation boundary.
Package specifiers are passed to `uv pip install` or pip and may contain URLs or
VCS references; keep them application-controlled. Persistent Docker sessions
can retain files, packages, and artifacts across calls, so clear or recreate
the environment when cross-call contamination matters.

## Shell-specific boundary

`bash_executor` is local denylist-protected subprocess execution. Its checks
reject known privilege escalation, interactive shells, inline interpreter
execution, command substitution, shell operators, destructive Git/RM patterns,
and writes to protected system paths. It does not prove a command is harmless.
In particular:

- A pre-existing `script.sh` or `script.py` can contain arbitrary behavior even
  when the wrapper command itself passes the denylist.
- Network clients (`curl`, `wget`, `ssh`, package managers, Git remotes) can
  contact external systems, upload data, or read ambient credentials unless the
  application prevents it.
- `working_dir` and `allowed_paths` constrain the validator's recognized write
  targets; they are not a kernel filesystem sandbox and cannot make a hostile
  executable safe.
- The checker rejects shell composition such as `|`, `>`, `&&`, and `;` in
  ordinary command syntax. Compose trusted operations in Python instead of
  trying to bypass this rule with a wrapper.

Use `StaticBashEnvironment` or `scripts/audit_tool_request.py` before approval,
then run in a disposable container/VM when input is untrusted.

## Optional model-based function-call evaluation

A separate Granite Guardian adapter check can score malformed or hallucinated
function calls: `guardian_check(context, guardian_backend,
criteria="function_call", scoring_schema="tool_call")` returns a risk score
from `0.0` to `1.0`. This requires an adapter-capable backend and its model
weights, is model-dependent, and is an evaluation signal—not deterministic
schema validation, approval, or an execution block. Put strict JSON/schema and
business-policy checks first; route adapter/backend setup to
`backends-and-models` and evaluator policy to `sampling-and-evaluation`.

## Code, network, files, and credentials

- Do not expose `eval`, arbitrary SQL, unrestricted HTTP, raw file open, or a
  general Python interpreter when a fixed-domain wrapper is possible.
- Treat output as potentially sensitive: a tool can return secrets, prompt
  injection, malicious URLs, or huge data. Cap and sanitize it before adding it
  to model context. Do not let tool output redefine policy.
- Store API keys in a secret manager or process configuration. Pass only the
  minimum credential to a wrapper, never interpolate it into a prompt, schema,
  shell command, MCP description, or audit log.
- For HTTP/SSE MCP, approve the exact origin and TLS path, set bounded connect
  and read timeouts, and decide whether the server may receive user data. For
  `api_key=`, Mellea creates a Bearer header; protect the connection dictionary.
- For stdio MCP, pin the executable/arguments and pass a minimal `env` mapping.
  The child process and every tool call are part of the trust boundary. Do not
  inherit a broad environment merely because the server needs one token.
- Do not assume LangChain or smolagents tools are inert. Search, browser,
  Python, database, filesystem, and messaging tools retain their original
  permissions after adaptation.

## Tool hooks as enforcement points

`acall_tools()` fires `tool_pre_invoke` before execution and
`tool_post_invoke` after execution. Payloads are immutable. A pre hook can
return a modified `ModelToolCall` (for example, normalized or redacted
arguments) or `block("reason")`; a block raises `PluginViolationError` and the
tool does not run. A post hook can transform `tool_output` before the final
`ToolMessage` is rebuilt, which is useful for secret redaction and output caps.
The post payload also has `execution_time_ms`, `success`, and `error`.

Use `payload.is_control_flow` to distinguish framework control flow such as
ReAct's `final_answer` from user tools. Allowlist plugins should normally skip
control-flow calls so they do not prevent loop termination. Hooks see raw
arguments/output before redaction; secure the hook process and redact before
logging. Use scoped plugin registration and remove temporary policies after the
operation.

A central pre-hook should re-check the final tool name and arguments even when
the generation layer already used strict validation. Multiple loops or foreign
adapters may otherwise bypass a requirement. Keep policy hooks deterministic,
short, and fail closed on malformed or missing fields. Use `SEQUENTIAL` or
`TRANSFORM` mode when changing payloads; concurrent, audit, and
fire-and-forget hook modifications are discarded. Also avoid applying
`tool_arg_validator` directly to secret-bearing fields: a failed requirement's
reason can include the argument value for repair, logging, or model feedback.

## MCP admission checklist

Before wrapping a discovered `MCPToolSpec`, confirm:

- `mellea[tools]` is installed and the selected transport is available.
- The URL/origin or stdio executable is explicitly trusted.
- The server identity, auth scope, timeout, outbound-data policy, and rate
  limits are known.
- Name, description, input schema, required fields, and property types are
  valid; reject unconstrained paths, URLs, commands, and extra properties.
- The tool's side effects are understood and separately approved.
- Results are bounded, treated as data, and filtered for prompt injection.
- No API key, cookie, environment dump, or private path is inserted into the
  model-visible tool schema or logs.

Discovery only calls `list_tools()`. Each wrapped invocation opens a fresh MCP
session; stdio therefore starts a fresh server subprocess per invocation.
Server errors are returned as text markers, so the caller must not treat a
string beginning `[tool error]` as a successful business result.
