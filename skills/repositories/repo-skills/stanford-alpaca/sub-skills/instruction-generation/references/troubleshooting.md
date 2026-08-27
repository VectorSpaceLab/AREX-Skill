# Troubleshooting

## `OPENAI_API_KEY` is missing

Symptoms:
- live generation fails before the first API request succeeds
- helper scripts still work, but the networked workflow does not start

Fix:
- export `OPENAI_API_KEY`
- if your account requires it, also export `OPENAI_ORG`
- verify that you are using the legacy completion client expected by the source code

## Rate limits or transient OpenAI failures

Symptoms:
- repeated `OpenAIError` warnings
- requests appear to stall and retry

Fix:
- lower the request rate or batch size
- keep the default retry sleep, or increase it if the API is throttling harder than usual
- split the run into smaller output directories if you need recoverable chunks

## Legacy OpenAI client compatibility

Symptoms:
- `Completion.create` is missing
- `openai.error.OpenAIError` or `openai_object` import paths fail
- modern `openai` 1.x code paths do not behave like the source expects

Fix:
- pin a legacy `openai` client compatible with the old completion API
- do not rewrite the prompt/debug scripts to use chat completions unless you also adapt the parsing and live workflow

## Network failures

Symptoms:
- DNS, proxy, TLS, or connection resets
- the live workflow never leaves the retry loop

Fix:
- confirm outbound HTTPS access
- check proxy and certificate environment variables
- if network access is intentionally unavailable, stay on the offline renderer/parser path

## Empty or over-filtered outputs

Symptoms:
- the parser returns no surviving records
- `regen.json` grows very slowly
- every candidate disappears during filtering

Fix:
- inspect the raw completion text before filtering
- check whether `finish_reason == 'length'` caused the last chunk to be discarded
- verify that candidate instructions are not too short, too long, blacklisted, punctuation-starting, or non-ASCII-starting
- remember that `Write a program...` is intentionally filtered
- if the prompt changed, compare against the bundled prompt template before changing the filters

## Multiprocessing cost

Symptoms:
- the generation loop spends most of its time computing ROUGE-L similarity
- CPU usage is high even when the API request itself is finished

Fix:
- lower `num_cpus` during debugging
- use a tiny fixture to check parsing before running a large dedup pass
- avoid multiple parallel live runs that all spawn their own worker pools

## ROUGE / tokenization issues

Symptoms:
- near-duplicate instructions are not filtered
- valid instructions disappear unexpectedly
- similarity scores look inconsistent across runs

Fix:
- compare tokenized forms, not just raw strings
- normalize whitespace and punctuation in the candidate instruction before judging similarity
- remember that the source uses ROUGE-L with `use_stemmer=False` and a `0.7` max-similarity cutoff

## Stale `regen.json`

Symptoms:
- a resumed run mixes old and new prompt policies
- the accepted record count looks larger than expected

Fix:
- start a fresh output directory when you change the prompt, seed file, or filtering behavior
- treat `regen.json` as the current resume ledger, not as a permanent archive of every rejected candidate
