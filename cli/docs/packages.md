> disco can help you create disco packages. Ask it to bundle your extensions, skills, prompt templates, or themes.

# DisCo Packages

DisCo packages bundle extensions, skills, prompt templates, and themes so you can share them through npm or git. A package can declare resources in `package.json` under the `disco` key, or use conventional directories.

## Table of Contents

- [Install and Manage](#install-and-manage)
- [Package Sources](#package-sources)
- [Creating a DisCo Package](#creating-a-disco-package)
- [Package Structure](#package-structure)
- [Dependencies](#dependencies)
- [Package Filtering](#package-filtering)
- [Enable and Disable Resources](#enable-and-disable-resources)
- [Scope and Deduplication](#scope-and-deduplication)

## Install and Manage

> **Security:** DisCo packages run with full system access. Extensions execute arbitrary code, and skills can instruct the model to perform any action including running executables. Review source code before installing third-party packages.

```bash
disco install npm:@foo/bar@1.0.0
disco install git:github.com/user/repo@v1
disco install https://github.com/user/repo  # raw URLs work too
disco install /absolute/path/to/package
disco install ./relative/path/to/package

disco remove npm:@foo/bar
disco list                     # show installed packages from settings
disco update                   # update disco only
disco update --all             # update disco, update packages, and reconcile pinned git refs
disco update --extensions      # update packages and reconcile pinned git refs only
disco update --models          # refresh model catalogs only
disco update --self            # update disco only
disco update --self --force    # reinstall disco even if current
disco update npm:@foo/bar      # update one package
disco update --extension npm:@foo/bar
```

These commands manage disco packages and `disco update` can update the disco CLI installation. To uninstall disco itself, see [Quickstart](quickstart.md#uninstall).

By default, `install` and `remove` write to user settings (`~/.disco/agent/settings.json`). Use `-l` to write to project settings (`.disco/settings.json`) instead. Project settings can be shared with your team, and disco installs any missing packages automatically on startup after the project is trusted.

To try a package without installing it, use `--extension` or `-e`. This installs to a temporary directory for the current run only:

```bash
disco -e npm:@foo/bar
disco -e git:github.com/user/repo
```

## Package Sources

DisCo accepts three source types in settings and `disco install`.

### npm

```
npm:@scope/pkg@1.2.3
npm:pkg
```

- Versioned specs are pinned and skipped by package updates (`disco update --extensions`, `disco update --all`).
- User installs go under `~/.disco/agent/npm/`.
- Project installs go under `.disco/npm/`.
- Set `npmCommand` in `settings.json` to pin npm package lookup and install operations to a specific wrapper command such as `mise` or `asdf`.

Example:

```json
{
  "npmCommand": ["mise", "exec", "node@20", "--", "npm"]
}
```

### git

```
git:github.com/user/repo@v1
git:git@github.com:user/repo@v1
https://github.com/user/repo@v1
ssh://git@github.com/user/repo@v1
```

- Without `git:` prefix, only protocol URLs are accepted (`https://`, `http://`, `ssh://`, `git://`).
- With `git:` prefix, shorthand formats are accepted, including `github.com/user/repo` and `git@github.com:user/repo`.
- HTTPS and SSH URLs are both supported.
- SSH URLs use your configured SSH keys automatically (respects `~/.ssh/config`).
- For non-interactive runs (for example CI), you can set `GIT_TERMINAL_PROMPT=0` to disable credential prompts and set `GIT_SSH_COMMAND` (for example `ssh -o BatchMode=yes -o ConnectTimeout=5`) to fail fast.
- Refs are pinned tags or commits. `disco update --extensions` and `disco update --all` do not move them to newer refs, but they do reconcile an existing clone to the configured ref.
- Use `disco install git:host/user/repo@new-ref` to update settings and move an existing package to a new pinned ref.
- Cloned to `~/.disco/agent/git/<host>/<path>` (global) or `.disco/git/<host>/<path>` (project).
- When reconciliation changes the checkout, disco resets and cleans the clone, then runs `npm install` if `package.json` exists.

**SSH examples:**
```bash
# git@host:path shorthand (requires git: prefix)
disco install git:git@github.com:user/repo

# ssh:// protocol format
disco install ssh://git@github.com/user/repo

# With version ref
disco install git:git@github.com:user/repo@v1.0.0
```

### Local Paths

```
/absolute/path/to/package
./relative/path/to/package
```

Local paths point to files or directories on disk and are added to settings without copying. Relative paths are resolved against the settings file they appear in. If the path is a file, it loads as a single extension. If it is a directory, disco loads resources using package rules.

## Creating a DisCo Package

Add a `disco` manifest to `package.json` or use conventional directories. Include the `disco-package` keyword for discoverability.

```json
{
  "name": "my-package",
  "keywords": ["disco-package"],
  "disco": {
    "extensions": ["./extensions"],
    "skills": ["./skills"],
    "prompts": ["./prompts"],
    "themes": ["./themes"]
  }
}
```

Paths are relative to the package root. Arrays support glob patterns and `!exclusions`.

### Discovery Metadata

Add the `disco-package` keyword so users can find compatible packages in npm search. Optional `video` and `image` fields may be used by package indexes or documentation tools:

```json
{
  "name": "my-package",
  "keywords": ["disco-package"],
  "disco": {
    "extensions": ["./extensions"],
    "video": "https://example.com/demo.mp4",
    "image": "https://example.com/screenshot.png"
  }
}
```

- **video**: URL for a demonstration video.
- **image**: URL for a representative image.

DisCo itself does not currently host or query a package gallery.

## Package Structure

### Convention Directories

If no `disco` manifest is present, disco auto-discovers resources from these directories:

- `extensions/` loads `.ts` and `.js` files
- `skills/` recursively finds `SKILL.md` folders and loads top-level `.md` files as skills
- `prompts/` loads `.md` files
- `themes/` loads `.json` files

## Dependencies

Third party runtime dependencies belong in `dependencies` in `package.json`. Dependencies that do not register extensions, skills, prompt templates, or themes also belong in `dependencies`. When disco installs a package from npm or git, it runs `npm install`, so those dependencies are installed automatically.

DisCo bundles core packages for extensions and skills. If you import any of these, list them in `peerDependencies` with a `"*"` range and do not bundle them: `@earendil-works/pi-ai`, `@earendil-works/pi-agent-core`, `@auto-ml-skills/disco`, `@earendil-works/pi-tui`, `typebox`.

Other disco packages must be bundled in your tarball. Add them to `dependencies` and `bundledDependencies`, then reference their resources through `node_modules/` paths. DisCo loads packages with separate module roots, so separate installs do not collide or share modules.

Example:

```json
{
  "dependencies": {
    "shitty-extensions": "^1.0.1"
  },
  "bundledDependencies": ["shitty-extensions"],
  "disco": {
    "extensions": ["extensions", "node_modules/shitty-extensions/extensions"],
    "skills": ["skills", "node_modules/shitty-extensions/skills"]
  }
}
```

## Package Filtering

Filter what a package loads using the object form in settings:

```json
{
  "packages": [
    "npm:simple-pkg",
    {
      "source": "npm:my-package",
      "extensions": ["extensions/*.ts", "!extensions/legacy.ts"],
      "skills": [],
      "prompts": ["prompts/review.md"],
      "themes": ["+themes/legacy.json"]
    }
  ]
}
```

`+path` and `-path` are exact paths relative to the package root.

- Omit a key to load all of that type.
- Use `[]` to load none of that type.
- `!pattern` excludes matches.
- `+path` force-includes an exact path.
- `-path` force-excludes an exact path.
- Filters layer on top of the manifest. They narrow down what is already allowed.

## Enable and Disable Resources

Use `disco config` to enable or disable extensions, skills, prompt templates, and themes from installed packages and local directories. `disco config` starts in global settings (`~/.disco/agent/settings.json`); press Tab to switch between global and project-local modes. Use `disco config -l` to start in project overrides (`.disco/settings.json`) with inherited global resources dimmed.

## Scope and Deduplication

Packages can appear in both global and project settings. If the same package appears in both, the project entry wins unless the project entry has `autoload: false`, in which case it is applied as a delta over the global entry. Identity is determined by:

- npm: package name
- git: repository URL without ref
- local: resolved absolute path
