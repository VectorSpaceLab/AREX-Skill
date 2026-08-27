# Workflows

## 1) Inspect current package state
```bash
evo_config show --brief --no_color
evo_config show --diff --no_color
evo pkg --info
evo pkg --version
evo pkg --logfile
```
Use `show` with trailing setting names if you only need a few keys.

## 2) Edit a writable copy safely
```bash
tmp_cfg="$(mktemp "${TMPDIR:-/tmp}/evo-settings.XXXXXX.json")"
cp ~/.evo/settings.json "$tmp_cfg"
evo_config set -c "$tmp_cfg" plot_backend qtagg
evo_config set -c "$tmp_cfg" plot_figsize 6 5 plot_usetex plot_fontfamily serif
evo_config show -c "$tmp_cfg" --diff --no_color
```
If you need to overlay another file:
```bash
evo_config set -c "$tmp_cfg" -m overlay.json
evo_config set -c "$tmp_cfg" -m overlay.json --soft
```
Use `--soft` when you want to keep existing keys and only fill missing ones from the overlay.

## 3) Generate a config file from CLI flags
```bash
evo_config generate --align --plot --plot_mode xz --verbose --no_color
evo_config generate --align --plot --plot_mode xz --verbose -o cfg.json
```
Use long `--` flags where possible; combined short flags like `-vp` are discouraged. Without `-o`, the command is read-only and saves nothing.

## 4) Reset carefully
```bash
evo_config reset -y
evo_config reset -y plot_backend plot_seaborn_style
```
`reset` only targets the package settings file and never takes `-c`. Keep `-y` before the trailing keys.

## 5) Inspect or clear the logfile
```bash
evo pkg --logfile
evo cat_log
printf 'hello from evo' | evo cat_log --source demo --loglevel info
evo cat_log --clear_log
```
Read mode prints the existing logfile. Pipe mode writes only when `global_logfile_enabled` is true.

## 6) Launch the evo shell
```bash
evo_ipython
```
On first launch, the `evo` profile is created automatically and the package config is copied into the profile directory.

## Why no bundled helper
A `config_smoke.py` helper would either duplicate the read-only CLI commands above or risk mutating user settings. This sub-skill keeps the safe path explicit and uses the CLI itself as the smoke surface.

The original `test/demos/config_demo.sh` stays out of the runtime skill for the same reason: it is interactive, assumes source-tree layout, and mutates package settings while waiting for stdin.
