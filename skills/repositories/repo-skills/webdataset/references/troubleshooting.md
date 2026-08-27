# WebDataset Troubleshooting Router

Use this root reference to choose the right failure surface. Then open the owning sub-skill for detailed recovery steps.

## Install and import failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ModuleNotFoundError: webdataset` | Package not installed in the active environment | Install `webdataset`, then run `python scripts/check_env.py`. |
| `ModuleNotFoundError: braceexpand`, `numpy`, or `yaml` | Broken base install | Reinstall the package or run `pip check`. |
| `decode("pil")` or image writing fails | Pillow missing | Install Pillow or choose a non-image field. Route to [reading-pipelines](../sub-skills/reading-pipelines/SKILL.md) or [shard-writing](../sub-skills/shard-writing/SKILL.md). |
| `WebLoader`/`DataLoader` behavior is wrong or torch is missing | PyTorch is not installed or the task expects a real torch loader | Run `python scripts/check_env.py --require-torch`, then use [reading-pipelines](../sub-skills/reading-pipelines/SKILL.md). |

## Reader failures

| Symptom | Owning guidance |
| --- | --- |
| Empty worker, too few shards, or `No samples found in dataset` | [reading-pipelines troubleshooting](../sub-skills/reading-pipelines/references/troubleshooting.md) |
| Missing keys in `to_tuple`, `rename`, or `extract_keys` | [reading-pipelines troubleshooting](../sub-skills/reading-pipelines/references/troubleshooting.md) |
| Decoder errors, shuffle/decode memory use, batch/unbatch mismatch | [reading-pipelines troubleshooting](../sub-skills/reading-pipelines/references/troubleshooting.md) |
| Column-store inner reader has empty shards | [reading-pipelines workflows](../sub-skills/reading-pipelines/references/workflows.md) |

## Writer failures

| Symptom | Owning guidance |
| --- | --- |
| Missing `__key__`, unsupported encoder, malformed sample dict | [shard-writing troubleshooting](../sub-skills/shard-writing/references/troubleshooting.md) |
| Image dtype/range failures or `txt.gz`/tar compression confusion | [shard-writing troubleshooting](../sub-skills/shard-writing/references/troubleshooting.md) |
| Read-after-write validation mismatch | [shard-writing workflows](../sub-skills/shard-writing/references/workflows.md) plus [reading-pipelines](../sub-skills/reading-pipelines/SKILL.md) |

## IO, cache, and security failures

| Symptom | Owning guidance |
| --- | --- |
| `pipe:` failure, broken pipe, or shell trust boundary | [io-caching-security troubleshooting](../sub-skills/io-caching-security/references/troubleshooting.md) |
| `cache directory ... does not exist`, flat cache-name failures, cache grows unexpectedly | [io-caching-security troubleshooting](../sub-skills/io-caching-security/references/troubleshooting.md) |
| Secure mode blocks local/file/pipe/rewrite/pickle/torch | [io-caching-security troubleshooting](../sub-skills/io-caching-security/references/troubleshooting.md) |
| Missing `curl`, `gsutil`, `ais`, `huggingface_hub`, cloud credentials | [io-caching-security](../sub-skills/io-caching-security/SKILL.md) and provider setup outside this skill |

## First response checklist

1. Identify whether the user is reading, writing, or configuring opening/caching/security.
2. Run `python scripts/check_env.py` only when the user asks to diagnose an environment or the failure is import/dependency-related.
3. Never tell the user to run original repository notebooks, examples, or tests for ordinary package usage.
4. Use the bundled sub-skill scripts for tiny local proofs; reserve source-repo native tests for skill verification or repository development tasks.
5. Keep network, credential, GPU, OCR, Transformers, and Ray workflows explicit as optional or out of scope unless the user requests and authorizes them.
