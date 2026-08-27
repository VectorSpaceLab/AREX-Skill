# Quickstart

This page gets you from install to a useful first disco session.

## Install

DisCo is distributed as an npm package:

```bash
npm install -g --ignore-scripts @auto-ml-skills/disco
```

`--ignore-scripts` disables dependency lifecycle scripts during install. DisCo does not require install scripts for normal npm installs.

### Uninstall

Use the package manager that installed DisCo:

```bash
# npm install -g
npm uninstall -g @auto-ml-skills/disco

# pnpm
pnpm remove -g @auto-ml-skills/disco

# Yarn
yarn global remove @auto-ml-skills/disco

# Bun
bun uninstall -g @auto-ml-skills/disco
```

Uninstalling disco leaves settings, credentials, sessions, and installed disco packages in `~/.disco/agent/`.

Then start disco in the project directory you want it to work on:

```bash
cd /path/to/project
disco
```

## Authenticate

DisCo can use subscription providers through `/login`, or API-key providers through environment variables or the auth file.

### Option 1: subscription login

Start disco and run:

```text
/login
```

Then select a provider. Built-in subscription logins include Claude Pro/Max, ChatGPT Plus/Pro (Codex), and GitHub Copilot.

### Option 2: API key

Set an API key before launching disco:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
disco
```

You can also run `/login` and select an API-key provider to store the key in `~/.disco/agent/auth.json`.

See [Providers](providers.md) for all supported providers, environment variables, and cloud-provider setup.

## First session

Once disco starts, type a request and press Enter:

```text
Summarize this repository and tell me how to run its checks.
```

By default, disco gives the model four tools:

- `read` - read files
- `write` - create or overwrite files
- `edit` - patch files
- `bash` - run shell commands

Additional built-in read-only tools (`grep`, `find`, `ls`) are available through tool options. DisCo runs in your current working directory and can modify files there. Use git or another checkpointing workflow if you want easy rollback.

## Give disco project instructions

DisCo loads context files at startup. Add an `AGENTS.md` file to tell it how to work in a project:

```markdown
# Project Instructions

- Run `npm run check` after code changes.
- Do not run production migrations locally.
- Keep responses concise.
```

DisCo loads:

- `~/.disco/agent/AGENTS.md` for global instructions
- `AGENTS.md` or `CLAUDE.md` from parent directories and the current directory

Restart disco, or run `/reload`, after changing context files.

## Common things to try

### Reference files

Type `@` in the editor to fuzzy-search files, or pass files on the command line:

```bash
disco @README.md "Summarize this"
disco @src/app.ts @src/app.test.ts "Review these together"
```

Images or text can be pasted with Ctrl+V (Alt+V on Windows); images can also be dragged into supported terminals.

### Run shell commands

In interactive mode:

```text
!npm run lint
```

The command output is sent to the model. Use `!!command` to run a command without adding its output to the model context.

### Switch models

Use `/model` or Ctrl+L to choose a model. Use Shift+Tab to cycle thinking level. Use Ctrl+P / Shift+Ctrl+P to cycle through scoped models.

### Continue later

Sessions are saved automatically:

```bash
disco -c                  # Continue most recent session
disco -r                  # Browse previous sessions
disco --name "my task"    # Set session display name at startup
disco --session <path|id> # Open a specific session
```

Inside disco, use `/resume`, `/new`, `/tree`, `/fork`, and `/clone` to manage sessions.

### Non-interactive mode

For one-shot prompts:

```bash
disco -p "Summarize this codebase"
cat README.md | disco -p "Summarize this text"
disco -p @screenshot.png "What's in this image?"
```

Use `--mode json` for JSON event output or `--mode rpc` for process integration.

## Next steps

- [Using DisCo](usage.md) - interactive mode, slash commands, sessions, context files, and CLI reference.
- [Providers](providers.md) - authentication and model setup.
- [Settings](settings.md) - global and project configuration.
- [Keybindings](keybindings.md) - shortcuts and customization.
- [DisCo Packages](packages.md) - install shared extensions, skills, prompts, and themes.

Platform notes: [Windows](windows.md), [Termux](termux.md), [tmux](tmux.md), [Terminal setup](terminal-setup.md), [Shell aliases](shell-aliases.md).
