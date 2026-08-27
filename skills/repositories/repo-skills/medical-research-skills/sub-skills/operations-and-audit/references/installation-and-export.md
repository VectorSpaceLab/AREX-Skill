# Installation and Export Reference

Installation is an explicit deployment operation, not part of routine catalog
routing. The public repository documents OpenClaw as one compatible target and
shows a shell installer that clones the public repository, discovers `SKILL.md`
directories, copies them into a configurable skills directory, skips existing
entries, and supports a `--dry-run` preview. This reference records that
contract without bundling or executing the installer.

## OpenClaw: reference-only contract

Use this section only when the user asks about OpenClaw setup or wants to plan a
manual installation. Before any side effect, confirm:

- the target agent and workspace;
- the exact destination directory (the documented default is a user-level
  OpenClaw skills directory, but a workspace-specific directory can be selected
  explicitly);
- whether the source revision is trusted and which skills are in scope;
- whether existing destinations should be skipped or deliberately replaced;
- network, Git, credentials, and gateway-restart availability;
- privacy and security review of every skill to be exposed to the agent.

The documented installer behavior is approximately:

1. Clone a shallow copy of the public catalog into a temporary directory.
2. Find skill directories containing `SKILL.md`.
3. For each skill, skip an already-existing destination rather than overwrite it.
4. Otherwise copy the skill directory into the selected destination.
5. In dry-run mode, print intended actions without copying.
6. After a real install, the user may need to restart the OpenClaw gateway.

These are reference semantics, not permission to run them. Do not execute a
remote shell one-liner, clone a repository, copy into an agent directory,
restart a gateway, or broaden the install set automatically. Prefer a reviewed
local checkout, a pinned revision, a dry run, and an explicit destination. A
destination collision is a stop-and-confirm event; never use an overwrite flag
that the documented workflow does not provide.

## Safe planning record

Before handing installation to an authorized operator, record:

```text
Target agent       : <OpenClaw / compatible agent>
Source revision    : <trusted tag or commit, if known>
Selected skills    : <canonical ids or reviewed subset>
Destination        : <explicit path, no implicit expansion>
Mode               : DRY-RUN / AUTHORIZED INSTALL
Collision policy   : SKIP / REVIEW EACH / EXPLICIT REPLACE
Network/credentials: <required, available, or unavailable>
Gateway restart    : <required, authorized, or deferred>
Privacy review     : <completed / pending>
Rollback           : <backup or removal plan>
```

After the operator acts, verify the installed tree, frontmatter, internal links,
permissions, and intended skill count. Treat a copied directory as not yet
verified. Record skipped collisions and partial failures. A gateway restart is
separate from file copying and must be reported separately.

## Compatible-agent export

For Claude Code, Codex, another compatible agent, or a project-local directory,
first distinguish **managed DisCo deployment** from **export**:

- Managed DisCo skills remain in their canonical managed scope and are consumed
  through the appropriate router. Do not hand-edit a live router during a
  catalog operation.
- An export is a separate, user-requested copy into a named target. Confirm the
  target layout, duplicate policy, frontmatter compatibility, and whether the
  target agent requires policy/configuration files.
- Export only reviewed, self-contained runtime files. Do not export test
  reports, private inspection environments, source-checkout links, caches,
  credentials, or generated logs.
- Preserve canonical skill names and bundled references. If a target has a
  different discovery model, document the mapping rather than silently
  renaming or merging entries.
- Do not claim that export proves execution, dependency readiness, privacy
  approval, or clinical suitability.

When a user asks to “install everything,” clarify scope and collision policy
before acting. A safe alternative is to produce a dry-run inventory and a
reviewable command for the user to execute locally.

## Failure and rollback expectations

- Network or Git failure: retain the reviewed source choice, report the failing
  step, and retry only after connectivity/authorization is restored.
- Permission failure: do not escalate privileges implicitly; choose an
  authorized destination or stop.
- Collision: leave the existing target unchanged and ask for an explicit
  replacement decision.
- Partial copy: do not report success for the whole set; list completed,
  skipped, and failed entries and remove only newly-created partial artifacts
  if rollback is authorized.
- Restart failure: report the files as copied but the gateway as not refreshed.
- Unexpected skill content or unsafe script: stop the export and route the
  artifact to audit before deployment.
