# Agent Workflow Troubleshooting

## `wren skills get` reports an unknown guide or script

Run `wren skills list` against the installed package. Guide inventories are
versioned with the CLI; do not assume a name from a different release exists.

## Discovery stub is installed but `wren` is unavailable

The stub is only discovery guidance. Install `wrenai` in the environment that
the agent/client will invoke, then verify with `wren --version`.

## `wren ask` fails

Choose exactly one of `--guided` and `--direct`. The command does not have a
default mode and does not run a query.

## dlt project can build but tables are not found at query time

Check that each generated DuckDB model uses the database filename stem as its
catalog and that the profile points at the directory containing the database.
Then rebuild the project target before querying.

## A new guide is not delivered by the CLI

Confirm the guide is in package skill content, has a `SKILL.md`, and has a
matching skills CLI test. A discovery-stub-only edit cannot make `wren skills
get` return new content.

## Credential exposure risk

Never ask the user to paste an API key into chat or a generated script. Use dlt
or Wren-supported environment/secret configuration and keep secret files out of
version control.
