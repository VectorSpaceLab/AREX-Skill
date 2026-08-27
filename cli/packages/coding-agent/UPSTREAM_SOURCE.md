# Upstream Source

- Repository: `https://github.com/earendil-works/pi.git`
- Package: `packages/coding-agent`
- Tag: `v0.83.0`
- Commit: `845d6ff1f6643aba440341cce877ce1c43ebbc39`
- Audited source: all 187 tracked files from `src/`; 135 remain byte-identical,
  49 are adapted for DisCo, `utils/pi-user-agent.ts` is adapted and renamed to
  `utils/disco-user-agent.ts`, and two unused Pi announcement resources are
  intentionally excluded.
- Imported tests: all 219 tracked files from `test/`; 179 remain byte-identical
  and 40 are adapted. Eight DisCo-specific integration tests are added.
- Imported documentation: `docs/`, excluding the upstream documentation-site
  configuration `docs/docs.json` and four Pi-branded screenshots. All 30
  retained documents are rewritten and published as DisCo behavior resources.
- Imported examples: all 134 tracked files from `examples/`; 26 remain
  byte-identical and 108 have DisCo package names, commands, or paths adapted.
- Imported OAuth support from `packages/ai/src/auth/oauth/`: Anthropic,
  OpenAI Codex, and OpenRouter flows plus `device-code.ts`, `oauth-page.ts`,
  and `pkce.ts`. These local copies isolate DisCo from
  `PI_OAUTH_CALLBACK_HOST`; all other `pi-ai` behavior remains an exact npm
  dependency at v0.83.0.

The content-addressed file manifest is
[`UPSTREAM_MANIFEST.json`](./UPSTREAM_MANIFEST.json). It records the upstream
and local SHA-256 hash and disposition of every tracked coding-agent file, all
11 upstream `pi-ai` OAuth files, and every local runtime, test, documentation,
and example file. Regenerate or compare it with:

```bash
node scripts/upstream-provenance.mjs --write \
  --upstream-root /path/to/pi-v0.83.0
node scripts/upstream-provenance.mjs --check \
  --upstream-root /path/to/pi-v0.83.0
```

The package's `verify:provenance` release gate performs the local hash and
inventory check without requiring a separate Pi checkout. Supplying the
upstream root additionally verifies the exact Git commit/tag, tracked-tree
cleanliness, upstream hashes, and every migration decision.

No source file from Pi's `packages/agent` or `packages/tui` has been copied.
Apart from the six explicitly listed OAuth support files, no source file from
`packages/ai` has been copied. Those packages remain external dependencies as
`@earendil-works/pi-agent-core`, `@earendil-works/pi-ai`, and
`@earendil-works/pi-tui`, each pinned to `0.83.0`.

The following upstream package content is intentionally excluded from the
DisCo implementation and npm tarball:

- `dist/`
- `node_modules/`
- `bin/pi`
- `install-lock/`
- upstream `npm-shrinkwrap.json`
- `scripts/migrate-sessions.sh`
- `docs/docs.json`
- the four screenshots under `docs/images/`, because they show Pi-branded or
  no-longer-accurate UI
- `src/modes/interactive/components/earendil-announcement.ts` and
  `src/modes/interactive/assets/clankolas.png`, because the announcement has no
  runtime caller and is unrelated to DisCo

Generated or local-install artifacts such as `dist/`, `node_modules/`, and the
untracked development `bin/pi` link are also excluded. `upstream-package.json`,
`UPSTREAM_CHANGELOG.md`, and `UPSTREAM_MANIFEST.json` are retained for source
comparison only. They are outside the published package file list and must not
be used as a runtime package root.
