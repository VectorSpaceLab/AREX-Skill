# Intent descriptors

`INTENTS.json` is data-only routing metadata. It lets chat adapters map a raw
request to a deterministic `clawbio.py run` plan without importing skill code,
executing shell text, or granting new CLI privileges.

## Location and required shape

Place `skills/<skill>/INTENTS.json` (preferred) or the supported alias
`skill_intents.json`. The top-level object requires:

```json
{
  "schema": "clawbio.skill_intents.v1",
  "skill": "my-alias",
  "routes": [
    {
      "intent_id": "status",
      "description": "Check the local skill status.",
      "trigger_terms": ["status", "runtime version"],
      "demo_policy": "never_unless_explicit",
      "plan": [{"kind": "skill_run", "skill": "my-alias"}]
    }
  ]
}
```

`schema` must be exactly `clawbio.skill_intents.v1`; `skill` is the CLI skill name
(or the descriptor's conservative identifier); and `routes` is non-empty. Optional
aliases, an `entrypoint`/`script`, or `execution.entrypoint` must point inside the
skill directory. A descriptor may use a CLI alias that differs from the folder (for
example, a `pharmgx-reporter` folder can publish a `pharmgx` descriptor), but the
alias must resolve to the intended registered script when it claims an executable
route.

Each route has a stable identifier, short description, trigger terms or aliases,
a permitted `demo_policy`, and one or more `skill_run` plan steps. A plan step may
use a safe local `input`, `output`, `input_template`, bounded `slots`, literal
allowlisted `args`, `demo`, and an explicit confirmation object for mutating or
expensive work.

## Trigger and demo behavior

Use specific phrases that distinguish this skill from adjacent skills. Keep the
route description and trigger text as untrusted labels, not executable prompts.
Use `never_unless_explicit` by default. Use `only_when_explicit` for demo-only
routes. A requested mode of `demo` is not sufficient by itself: the raw request
must say demo, example, synthetic, sample, or equivalent confirmation. This avoids
silently running a demo in response to an ordinary analysis request.

For parameterized requests, extract only bounded, expected slots:

```json
{
  "input_template": {"gene": "{gene}"},
  "slots": {
    "gene": {
      "pattern": "\\b([A-Z][A-Z0-9]{2,15})\\b",
      "required": true
    }
  }
}
```

Patterns must compile, stay short, and use conservative slot names. `choices`,
`aliases`, `default`, and `required` make interpretation explicit. Use an input
file or template for request data; do not put arbitrary user text into shell-like
arguments.

## Path and plan safety

Descriptor paths (`entrypoint`, `script`, plan `input`, and plan `output`) resolve
relative to the skill directory. Reject absolute paths and `..` traversal, and
verify the resolved path stays inside that directory. The planner materializes
`input_template` data as a bounded local request file; it never invokes a shell.

`args` are literal tokens only. They cannot override core execution controls or
smuggle a path. The source planner blocks these exact flags:

- `--input`, `--output`, `--profile`, `--profile-path`, `--demo`, `--help`, `-h`;
- flags containing sensitive fragments such as `credential`, `password`, `secret`,
  `token`, `profile`, `output`, `input`, `config`, `path`, `file`, `dir`, `weights`,
  `pop-map`, `reference`, `vcf`, `counts`, `metadata`, `reads`, `genome`, `adata`,
  or `sheet`.

The exact source implementation is deliberately conservative: absolute values,
`~`, traversal, path separators, NUL/newline characters, and overlong tokens are
rejected. A descriptor's own `allowed_extra_flags` metadata cannot create runner
privileges. Descriptor args are emitted only when the target is already registered
with a static `allowed_extra_flags` allow-list, and only those values are accepted.
Use `input`/`input_template` for request files and the plan `output` for confined
outputs rather than attempting blocked flags.

Do not encode shell operators, pipelines, command substitutions, credentials, or
free-form command lines in a descriptor. A request field such as `shell_line` is
only ordinary JSON for a registered skill that explicitly validates and interprets
it; it is not permission for the planner to run a shell.

## Registration states

- A valid descriptor with no local executable can still provide routing metadata,
  but a matching plan returns `needs_registration`.
- A descriptor with a conventional or declared local Python entrypoint can be
  augmented into the chat registry when its route is executable.
- Static `clawbio.py` registration remains the source of the runner's allowlist,
  demo arguments, and stable `clawbio run` interface. Do not use a descriptor to
  bypass that registry or to expose an arbitrary script outside the skill folder.

After adding or changing a descriptor, run the static checker, test a normal route,
test a missing-slot response, and test that a demo route does not fire without an
explicit demo request. Keep descriptor-only routing separate from domain validation
and scientific interpretation.
