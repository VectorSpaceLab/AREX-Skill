# Installer Safety

ARIS installers are intentionally conservative because they write into user research projects.

## Manifest Ownership

Each platform has its own manifest. Install, reconcile, and uninstall should only operate on entries recorded in that manifest. Declined-skill files remember choices made during selective install so reconcile does not keep prompting for the same skipped skills.

## Symlink and Path Rules

- Skill entries are usually symlinks to the user's ARIS checkout.
- Creating a skill aborts if the destination path already exists and is not an approved managed symlink.
- Removing a skill revalidates the exact symlink target before deletion.
- Symlinks outside the configured ARIS checkout are treated as user-owned and must not be deleted.
- Parent directories such as `.aris/`, `.claude/`, `.agents/`, `.github/`, or host skill roots should not themselves be unexpected symlinks.
- Temporary files should be written in the same directory as the final manifest so atomic rename is meaningful.

## Lock and Crash Recovery

Installer runs serialize through a lock directory. A stale lock should only be cleared when host/PID metadata proves the prior process is gone. If a crash happens mid-apply, rerun the installer/reconcile path instead of manually cleaning random symlinks; the previous manifest should remain authoritative.

## When to Use Special Flags

- `--dry-run`: use before mutating a non-empty project or explaining a planned change.
- `--replace-link NAME`: use only after confirming the existing path is a symlink for that exact skill and replacement is intended.
- `--adopt-existing NAME`: use when an existing symlink already points at the expected upstream target and the user wants the manifest to own it.
- `--clear-stale-lock`: use only after verifying the lock is stale.
- `--uninstall`: removes manifest-owned entries only; it should leave unrelated user files alone.

## Why This Generated Skill Does Not Bundle Installers

The upstream installer scripts are large, actively maintained, and intentionally side-effectful. Vendoring them into a generated repo skill would create stale mutating copies. This skill instead distills their interface and safety contracts and provides read-only diagnostic helpers.
