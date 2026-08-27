# Skills and Meta-Skills Command Catalog

Evidence baseline: OpenSquilla 0.5.3 was inspected in a CPU-only environment.
The `opensquilla` entry point and Skill CLI command family were recorded as
available; `mcp`, `lightgbm`, `onnxruntime`, `tokenizers`, `tiktoken`, and
`jieba` imported successfully in that inspection environment. Provider, channel,
and search catalogs are separate route families; use this sub-skill only for the
Skill/MetaSkill catalog.

## Safety Classes

| Class | Commands | Notes |
| --- | --- | --- |
| Read-only | `skills list`, `skills view`, `skills doctor`, `skills inspect`, `skills meta runs ...`, `skills meta proposals list/show`, `skills tap list` | Prefer these first. Doctor is read-only and does not run third-party scripts or call an LLM. |
| Network/read source | `skills search`, `skills install`, `skills update`, `skills tap add/remove`, `skills publish` | Search/install/update/publish may contact source services or repositories. |
| Local mutation | `skills install`, `skills update`, `skills uninstall`, `skills reload`, `skills meta proposals accept` | Confirm intent, identity, risk, and rollback expectations before acting. |

`skills reload` mutates only the running Gateway's in-memory catalog generation,
but it is still a state change: it has no offline fallback and should not be run
as a casual probe.

## Skill Inventory and Inspection

```sh
opensquilla skills list
opensquilla skills list --json
opensquilla skills view <skill-name>
opensquilla skills view <skill-name> --json
opensquilla skills doctor
opensquilla skills doctor <skill-name-or-install-id> --json
opensquilla skills inspect <meta-skill-name>
```

- `skills list` prefers the live Gateway catalog. If the Gateway is unreachable,
  it can validate local Skills offline under the profile lock and marks them as
  offline observations rather than active live catalog rows.
- `skills view` reads one Skill from the running Gateway catalog and prints
  metadata plus a content preview.
- `skills doctor` reports install, load, selection, compatibility, and readiness
  states. It can explain `needs_setup`, disabled Skills, degraded compatibility,
  shadowing, and transaction recovery issues.
- `skills inspect` prints the compiled `composition.steps` for a MetaSkill. Use
  `skills view` for ordinary Skill text.

When JSON automation matters, prefer `--json` and check exit code as well as
payload fields such as `ok`, `diagnostics`, `lifecycle`, `catalogState`, and
`effectiveFrom`.

## Search and Community Source Discovery

```sh
opensquilla skills search pdf
opensquilla skills search pdf --json
opensquilla skills search pdf --json --include-diagnostics
```

- Human output prints result cards and source diagnostics.
- Historical JSON output is a top-level list. Add `--include-diagnostics` only
  when the caller explicitly wants a stable envelope with `results`, source
  `diagnostics`, `partial`, and `allSourcesUnavailable`.
- `--include-diagnostics` requires `--json`.
- Source failures, invalid source responses, and rate limits can be partial; do
  not turn a partial source diagnostic into "no matching Skill exists" unless
  all relevant sources were searched successfully.

## Install, Update, and Uninstall

```sh
opensquilla skills install <clawhub-install-reference> --source clawhub
opensquilla skills install <owner/repo[@ref][:subpath]> --source github
opensquilla skills install <identifier> --source <clawhub|github> \
  --force --risk-confirmation <confirmation-token>
opensquilla skills install <identifier> --source <clawhub|github> --replace-source

opensquilla skills update <skill-name>
opensquilla skills update --install-id <install-id>
opensquilla skills update --all
opensquilla skills update <skill-name> --force --risk-confirmation <confirmation-token>

opensquilla skills uninstall <skill-name>
opensquilla skills uninstall --install-id <install-id>
opensquilla skills uninstall <skill-name> --allow-drift
```

Operational facts:

- Community installs are instruction-first. They commit content and provenance;
  they do not install declared runtime dependencies.
- A GitHub branch or tag resolves to an immutable commit before fetch. Immutable
  revisions are checked for content changes.
- The scanner may return `SCAN_CONFIRMATION_REQUIRED`. Review findings, then
  retry the exact same artifact with `--force --risk-confirmation <token>`. The
  token is tied to resolved source revision and fetched content; changed content
  requires a new token.
- Runtime Skill name, package identity, safe managed-directory key, and
  `install-id` are separate. Ambiguous name-only mutations fail closed; use
  `--install-id` when Doctor/list output shows ambiguous or shadowed installs.
- `--replace-source` is required before replacing a same-name installation from
  another package/source.
- `--allow-drift` confirms removal of a tracked Skill whose installed tree no
  longer matches the lockfile digest.
- Online install/update results become observable to agent turns from the next
  turn. Offline installs are validated for the next Gateway start; live
  activation/readiness are evaluated at that start.

## Reload the Running Catalog

```sh
opensquilla skills reload
opensquilla skills reload --json
```

- Requires a reachable running Gateway; unlike `skills list` and Doctor, it does
  not fall back to an offline scan.
- Human output shows active generation and Added/Removed/Modified differences.
- A partial reload can warn about broken Skills while succeeding. A failed reload
  keeps the previous generation active and exits non-zero.

## Taps and Publishing

```sh
opensquilla skills tap list
opensquilla skills tap add <owner/repo>
opensquilla skills tap remove <owner/repo>
opensquilla skills publish <path-to-skill>
opensquilla skills publish <path-to-skill> --repo <owner/repo>
```

Use taps when a team maintains a custom Skill source repository. Publishing is a
maintainer/source workflow; confirm target repository, credentials, and review
expectations before invoking it.

## MetaSkill Run History

```sh
opensquilla skills meta runs list
opensquilla skills meta runs list --name <meta-skill-name> --status ok --since 24h --limit 20
opensquilla skills meta runs show <run-id>
opensquilla skills meta runs steps <run-id>
opensquilla skills meta runs failures --since 24h
opensquilla skills meta runs diff <left-run-id> <right-run-id>
opensquilla skills meta runs cost --since 7d
opensquilla skills meta runs validate <run-id>
opensquilla skills meta runs eval-baseline <run-id>
opensquilla skills meta runs replay <run-id> --dry-run
opensquilla skills meta runs draft <run-id>
```

- The run-history CLI resolves the same state database as the Gateway. If the
  database has never been created, list-style commands exit successfully with an
  empty shape; lookup commands report `run not found`.
- `replay --dry-run` prints the historical or latest DAG shape. Live CLI-direct
  replay is not available in this build; use the dry-run path for inspection.
- `draft <run-id>` derives an authoring seed from a historical run and reports
  trigger conflicts against the current loaded specs.
- Use `validate` and `eval-baseline` to inspect stored request-template,
  validation, policy, and deterministic eval metadata.

## MetaSkill Proposals

```sh
opensquilla skills meta proposals list
opensquilla skills meta proposals show <proposal-id>
opensquilla skills meta proposals accept <proposal-id>
opensquilla skills meta proposals accept <proposal-id> --force
```

- Proposal ids are eight lowercase hex characters.
- `show` prints candidate `SKILL.md` and gates, or JSON with `--json`.
- `accept` promotes a proposal into the managed Skills layer only if gates mark
  it eligible, unless `--force` is explicitly supplied. Use `--force` only after
  human review of the failed gates and risk trade-off.
- Acceptance refuses to overwrite an existing managed Skill with the same name;
  remove or rename first.
- Restart or reload the Gateway as appropriate after accepting a proposal so the
  live catalog sees the new managed Skill.

## Bundled Helper

The local helper [../scripts/skills_meta_health.py](../scripts/skills_meta_health.py)
runs a read-only snapshot:

```sh
python sub-skills/skills-and-meta/scripts/skills_meta_health.py \
  --skill <optional-skill-name> --meta <optional-meta-skill-name>
```

It calls only read-only CLI surfaces: list, Doctor, recent MetaSkill runs,
proposal listing, and optional compiled MetaSkill inspection. It never performs
install, update, uninstall, reload, publish, search, or proposal acceptance.
