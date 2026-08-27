---
name: restful-clients
description: "Guides lightweight HanLP RESTful clients, parse payloads,
  Python/Java/Golang setup, endpoint routing, auth, language, timeout, and HTTP
  troubleshooting without requiring local model downloads."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Restful Clients

Use this sub-skill when the user wants to call a HanLP-compatible RESTful service instead of loading native models locally. It covers Python `HanLPClient`, request payloads, Java/Golang binding notes, auth/language controls, and HTTP troubleshooting.

## Read First

- Read `references/restful-api-reference.md` for verified Python client signatures, endpoint methods, and payload shapes.
- Read `references/java-golang-notes.md` for distilled non-Python quick starts.
- Read `references/troubleshooting.md` for auth, rate limit, JSON, network, SSL, and unsupported-language failures.
- Run `scripts/restful_payload_preview.py` to validate a `/parse` payload locally without sending it.

## Minimal Python Client

```python
from hanlp_restful import HanLPClient
HanLP = HanLPClient('https://hanlp.hankcs.com/api', auth=None, language='zh')
# HanLP.parse(...) contacts the service and may need auth/quota/network.
```

## Route by RESTful Task

| User need | Use |
| --- | --- |
| Parse raw text, a list of sentences, or tokenized sentences | `HanLPClient.parse(text=..., tokens=..., tasks=..., skip_tasks=...)` |
| Tokenize with fine/coarse or multilingual settings | `HanLPClient.tokenize(text, coarse=..., language=...)` |
| Call coreference, style transfer, STS, AMR, summarization, GEC, classification, sentiment, or language ID endpoints | advanced methods in `references/restful-api-reference.md` |
| Build payloads without sending network requests | `scripts/restful_payload_preview.py` |
| Use Java or Go from non-Python applications | `references/java-golang-notes.md` |

Do not run live RESTful tests as a default verification step; they require network, service availability, quota, and sometimes auth.
