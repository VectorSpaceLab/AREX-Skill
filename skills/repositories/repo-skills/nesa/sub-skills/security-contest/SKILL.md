---
name: security-contest
description: "Explain Nesa Hack EE contest rules, token-mapping submission
  format, scoring, and baseline attack ideas safely."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# Hack EE Security Contest

Use this sub-skill when the user asks about the Nesa Hack EE contest, encrypted
token ID mappings, submission JSON, scoring, daily/grand-prize rules, or the
baseline attacks described in the public attack paper.

Typical triggers:

- "format my Hack EE submission"
- "what does `{"tokens": ...}` need to look like?"
- "how is the contest scored?"
- "summarize baseline attacks against EE"
- "plan a safe token-mapping analysis"

## Ground rules

- The public contest objective is to map encrypted/private token IDs back to
  original text tokens.
- This skill can explain rules and safe local analysis; it does not provide a
  guaranteed decryption method.
- Do not submit to the live contest portal or tweet on the user's behalf.
- Do not claim success without a user-provided gold/evaluation signal.

## Submission format

Contest mappings are JSON objects shaped like:

```json
{"tokens":{"12":"an","345":"swer","678":" he"}}
```

Use [scripts/validate_submission.py](scripts/validate_submission.py) to check
local JSON shape and optionally score against a user-provided gold fixture.

## Attack-baseline workflow

1. Read [references/contest-format.md](references/contest-format.md) for rules,
   scoring, and submission caveats.
2. Read [references/attack-baselines.md](references/attack-baselines.md) for the
   optimization framing and baseline heuristic families.
3. If the user provides encrypted prompt/response pairs, keep the analysis local
   and record assumptions about vocabulary, hints, frequency counts, and model
   family.
4. If the user provides a gold mapping for a toy case, validate or score local
   guesses with the bundled script.
5. Be explicit about uncertainty and contest timing rules.

## References and scripts

- [references/contest-format.md](references/contest-format.md): daily and grand
  prize flow, submission JSON, scoring, hints, bonus, and caveats.
- [references/attack-baselines.md](references/attack-baselines.md): loss-function
  design, brute force, random/genetic sampling, and hill climbing.
- [references/troubleshooting.md](references/troubleshooting.md): malformed
  mapping JSON, duplicate/invalid keys, and rule misunderstandings.
- [scripts/validate_submission.py](scripts/validate_submission.py): self-contained
  JSON shape validator and optional local scorer.

## Boundaries

- For local encrypted model demos, route to `encrypted-distilbert`.
- For backend tokenization/request flow, route to `backend-protocol`.
- For web UI runtime, route to `web-ui-runtime`.
- Do not automate credentialed submissions, leaderboard scraping, or social
  media bonus actions without an explicit user request and safe boundaries.
