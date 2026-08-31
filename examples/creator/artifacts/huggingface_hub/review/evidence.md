# Routing decision evidence

- Repository: `huggingface/huggingface_hub`
- Source commit: `4237d95c603db491cb1070898c74c97e4d7c2582`
- Source URL: `https://github.com/huggingface/huggingface_hub`
- Skill id: `huggingface-hub`
- Taxonomy hash: `f8c306386015711634ddbb43a5eb95d1f58909c3513ce2063ba42efdd583a431`
- Routing status: `classified`
- Decision mode: agent-confirmed under the user's `auto decide` instruction.

## Assignment: MLOps → Model Hubs and Registries

**Decision:** assign the repository to the exact taxonomy path `MLOps → Model Hubs and Registries` with high confidence.

**Rationale:** The repository's stated purpose and dominant implementation are a Python client and CLI for discovering, downloading, versioning, publishing, and operating model, dataset, and Space repositories on the Hugging Face Hub. It provides repository metadata/info, refs, commits, file transfer, cache access, search/catalog APIs, cards, and registry-like Hub resource operations. This directly matches the taxonomy family scope: model discovery, versioning, caching, registry clients, and Hub APIs for pretrained models and datasets.

**Non-generated repository evidence:**

1. `README.md:20-87` calls the project “The official CLI and Python client for the Hugging Face Hub” and lists downloads, uploads, repository management, search, model cards, and the CLI as primary uses.
2. `setup.py:103-127` describes the package as a client to download and publish models, datasets, and other repos on the Hub, and exposes the `hf` console entry point.
3. `docs/source/en/guides/repository.md:1-35` is a first-class guide for creating/managing repositories, listing, deletion, duplication, upload/download, branches/tags, and settings.
4. `src/huggingface_hub/hf_api.py:2238-2285` defines the central `HfApi`; adjacent source defines model/dataset/Space info and repository/commit/ref operations.
5. `docs/source/en/guides/download.md`, `upload.md`, `search.md`, `manage-cache.md`, and their package references demonstrate the versioned Hub registry/client surface.

## Rejected near matches

- `LLM Applications → Agent Tools and Skills`: the package has optional MCP and `hf skills` integrations, but those are a small optional surface and not the repository's dominant capability; assigning on that basis would be an optional-integration match.
- `Model Deployment and Optimization → Inference Serving`: hosted inference and Endpoint client APIs are included, but the repository does not primarily expose a model-serving server/gateway; assigning it would confuse a client/deployment-management surface with serving infrastructure.
- `Data Science → Dataset Discovery`: dataset search is one client feature, not a standalone dataset catalog/registry product; the broader Hub registry family is the exact primary match.
- `MLOps → ML Platform Suites`: Jobs/Spaces/Sandboxes are optional hosted-resource integrations, while the core package is the Hub client/registry API; this would overstate platform-suite ownership.

The candidate runtime metadata contains only the minimal v2 projection. Evidence,
rationale, and confidence remain in this external decision file and are not
runtime routing content.
