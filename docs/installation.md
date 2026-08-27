# Installation Guide

Using DisCo with the skill collection published in this repository requires
both of the following installation steps, in order:

1. Install the `disco` CLI.
2. Install the public repository-skill collection into DisCo's managed skill
   directory.

Installing portable Creator meta skills into another agent is optional. DisCo
already bundles them.

## Install DisCo

Install the DisCo CLI from npm:

```bash
npm install -g @auto-ml-skills/disco
disco
```

DisCo requires Node.js `>=22.19.0` and builds on
[Pi](https://github.com/earendil-works/pi)'s multi-provider model layer.
The npm package includes its own DisCo-modified coding-agent source and uses
pinned `@earendil-works/pi-agent-core`, `@earendil-works/pi-ai`, and
`@earendil-works/pi-tui` packages as dependencies. It does not depend on
`@earendil-works/pi-coding-agent`, discover `.pi` resources, or share a
globally installed Pi dependency tree.

Configure at least one provider in the startup flow with `/login`, or use
environment variables such as
`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`,
or `MISTRAL_API_KEY`.

### Build from source for local development

```bash
git clone https://github.com/VectorSpaceLab/AREX-Skill.git
cd AREX-Skill
# If model catalog fetching fails behind an HTTP(S) proxy, use: NODE_USE_ENV_PROXY=1 bash scripts/build-from-source-link.sh
bash scripts/build-from-source-link.sh
```

The script installs the standalone package dependencies from the checked-in
shrinkwrap, builds DisCo, and links the `disco` command globally for local use.

## Install The Published Repository Collection

Install the official collection and its router with DisCo:

```bash
disco repo-skills install
```

The command uses a shallow checkout of the official repository, installs only
the published runtime collection, and records its source commit. Git must be
available locally. Later, inspect or update the managed collection with:

```bash
disco repo-skills status
disco repo-skills update
```

`status` is local-only: it checks managed digests, router presence and current
skill coverage without contacting GitHub. Run `update` when you want to check
and apply the latest official commit.

Updates replace only official managed skill IDs. Repo skills created or
imported locally by Creator are preserved. If an official skill was modified
locally or collides with an unmanaged skill, the command stops; an explicit
`--force` update first keeps a recoverable backup.

## Router Behavior And Toggle

DisCo registers the managed collection, but its repository roots and focused
sub-skills use `disable-model-invocation: true` and are omitted from the
initial model context. By default, `repo-skills-router` remains visible,
routes to one practical scenario, and then points DisCo to the selected skill
under its sibling `repo-skills/` collection. Automatic router selection can be
disabled and restored without uninstalling the collection:

```bash
disco repo-skills router disable
disco repo-skills router enable
```

When disabled, the router is omitted from automatic model selection but
remains registered for explicit `/skill:repo-skills-router` invocation.

**Start a new Researcher session after an install, update, or router setting
change.**

## Manual Installation Fallback

```bash
git clone https://github.com/VectorSpaceLab/AREX-Skill.git
cd AREX-Skill
mkdir -p ~/.disco/agent/skills/repositories
cp -R \
  skills/repositories/repo-skills \
  skills/repositories/repo-skills-router \
  ~/.disco/agent/skills/repositories/
```

Running `disco repo-skills install` later can adopt an unchanged manual copy
and preserve additional local skill IDs.

## Portable Meta Skills For Another Agent (Optional)

DisCo already bundles its Creator workflows. To run them in another compatible
agent (Claude Code, Codex, or project-local agents), follow
[Meta Skills For Other Agents](meta-skills-for-other-agents.md).

## See Also

For router behavior, third-party skill packages, and deployment-scope details,
see [DisCo Workflows](disco-workflows.md), the
[AREX-Skill Library guide](../skills/README.md), and the
[DisCo CLI README](../cli/README.md).
