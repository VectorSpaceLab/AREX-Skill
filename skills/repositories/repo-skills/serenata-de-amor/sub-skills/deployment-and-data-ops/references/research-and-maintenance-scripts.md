# Research and maintenance script safety

This repository contains historical data-acquisition, cron, deploy, and infrastructure update scripts. They are useful evidence for operations, but most are not safe generic runtime helpers. Classify before executing anything.

## Safety decision rule

Do not run a script when any of these are true unless the user explicitly authorizes the target, credentials, cost, and rollback plan:

- creates/destroys cloud resources;
- uses DigitalOcean, Twitter, Google, Foursquare, Yelp, inbox, object-storage, or other external credentials;
- downloads large datasets or scrapes public services;
- publishes tweets or contacts external users;
- mutates a production database or deployment;
- assumes legacy Python 2/Pipenv/Ansible behavior;
- is scheduled cron automation rather than a one-shot local diagnostic.

## Production/maintenance items

| Item | Classification | What it does | Runtime guidance |
| --- | --- | --- | --- |
| Production deploy shell script | Reference-only / unsafe by default | Pulls latest code, pulls/stops/starts production Compose services, collects static assets, runs migrations, clears cache | Do not bundle or execute generically. Use only for an authorized production target with backups and service-owner approval. |
| Cron `receipts` job | Reference-only / network + DB mutation | Runs `receipts` in production Compose with smaller batch size and longer pause | Prefer the documented `receipts` command only when network fetching is desired. |
| Cron `whistleblower` job | Reference-only / external publishing | Runs `tweet` on a schedule | Use `tweet --fake` for diagnostics; real publishing requires explicit credentials and approval. |
| Cron `update` job | Reference-only / destructive + cloud automation | Runs the DigitalOcean/Pipenv/Ansible update playbook | Do not run as setup. It creates infrastructure and reloads Jarbas data. |
| Cron `cleanup` job | Reference-only / cloud resource deletion | Destroys an update droplet | Do not run without confirming the cloud account and resource. |
| DigitalOcean update playbook | Reference-only / credential-bound | Creates a new droplet, installs dependencies, runs Rosie, runs Jarbas update/searchvector, destroys the droplet | Historical automation; relies on DO credentials, SSH key names, Python/Pipenv/Ansible compatibility, and production DB credentials. |
| DigitalOcean cleanup script | Reference-only / credential-bound deletion | Finds a droplet named for update automation and destroys it | Never run without human confirmation of the exact cloud account and droplet. |

## DigitalOcean update workflow, distilled

The historical update automation performed these steps:

1. Create or reuse a registered SSH key name in DigitalOcean.
2. Create a temporary Ubuntu droplet.
3. Install Git and Python package tools.
4. Clone the repository on the droplet.
5. Install Rosie and Jarbas Python requirements.
6. Create a Jarbas `.env` from sample settings and inject the production database URL.
7. Run migrations against the configured database as a credential test.
8. Run Rosie for Chamber of Deputies data.
9. Run `python manage.py update <data-directory>` to replace/reload Jarbas data.
10. Rebuild search vectors.
11. Destroy the temporary droplet.

This is not a safe local development sequence. For local development, use the sample load order in `data-loading.md`. For production updates, require an operator-approved runbook with backups.

## Research data acquisition scripts

The `research` area contains scripts for fetching or transforming datasets. Treat them as reference-only unless the user requests a specific research data acquisition task and authorizes network/API use.

| Script family | Examples | Risks / prerequisites | Safer alternative for common tasks |
| --- | --- | --- | --- |
| Backup/toolbox fetch | setup script, backup data helpers | large downloads, current toolbox/API compatibility, disk usage | Use existing sample datasets for Jarbas smoke tests. |
| Chamber/Federal public data fetchers | congressperson details, federal budget, sanctions, suppliers, receipts, TSE data | network availability, schema drift, rate limits, large outputs | Use Rosie sub-skill for classifier workflow; use sample/full prepared datasets for Jarbas loading. |
| External enrichment | CNPJ info, Foursquare, Yelp, geocoding, sex-place datasets | API credentials, rate limits, service terms, incomplete data | Leave fields blank or use already prepared company datasets unless enrichment is explicitly needed. |
| Inbox/social sourcing | inbox fetchers | credentials and personal/sensitive data handling | Do not run for generic setup. |
| Grouping/translation utilities | grouping receipts, translation table utilities | input/output assumptions tied to historical datasets | Inspect data schema and run on copies only. |

## Credential checklist before any external script

Ask or verify:

1. Which account/credential will be used?
2. Is the credential allowed for this exact operation?
3. What resources or public actions can be created, modified, deleted, or published?
4. What database or files will be mutated?
5. Is there a backup or rollback plan?
6. What cost, quota, rate limit, and legal/terms constraints apply?
7. How will logs be redacted?

If any answer is missing, stop and report the missing authorization instead of attempting a run.

## Maintenance command substitutes

Use the safer Django commands for local operations:

- Sample seed: `migrate`, `reimbursements`, `companies`, `suspicions`, `searchvector`.
- Receipt URL enrichment: `receipts` with explicit batch/pause and network authorization.
- Tweet link import: `tweets` with read-only Twitter credentials; missing credentials are okay.
- Tweet publishing dry run: `tweet --fake`.
- Full rebuild: prefer explicit manual command sequence; use `update` only after backups and target confirmation.

## What not to bundle as runtime scripts

The production deploy, cron wrappers, DigitalOcean Ansible playbook, cloud cleanup, and research fetch scripts are intentionally not copied into this sub-skill's `scripts/` directory. Their side effects, credentials, and historical environment assumptions make prose safety guidance more appropriate than reusable executable wrappers.
