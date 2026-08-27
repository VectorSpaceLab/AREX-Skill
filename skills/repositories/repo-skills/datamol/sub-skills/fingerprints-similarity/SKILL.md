---
name: fingerprints-similarity
description: "Guides agents using datamol to compute molecular fingerprints and
  descriptors, distance matrices, clusters, diverse or centroid picks, MCS
  SMARTS, and graph matches."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Datamol Fingerprints and Similarity

Use this sub-skill when a task asks for molecular fingerprints, descriptor tables, Tanimoto/Jaccard distance matrices, Butina clustering, diversity selection, centroid assignment, maximum common substructures, or molecular graph isomorphism with `datamol`.

## Read First

- Start with [references/api-reference.md](references/api-reference.md) for signatures, defaults, return shapes, and parameter choices.
- Use [references/workflows.md](references/workflows.md) for recipes covering fingerprint matrices, pairwise/cross distances, clustering, diversity and centroid picking, MCS checks, and graph matching.
- Use [references/troubleshooting.md](references/troubleshooting.md) when molecules fail to parse, fingerprint types are unknown, arrays have inconsistent shapes, parallel jobs misbehave, clusters are empty, or MCS is slow/partial.
- Run [scripts/fingerprint_similarity_smoke.py](scripts/fingerprint_similarity_smoke.py) for a deterministic tiny smoke test of supported fingerprints, fingerprints, distance matrices, clusters, diverse picks, and MCS.

## Scope Boundaries

- In scope: `dm.to_fp`, `dm.fp_to_array`, `dm.fold_count_fp`, `dm.list_supported_fingerprints`, `dm.descriptors.compute_many_descriptors`, `dm.descriptors.batch_compute_many_descriptors`, `dm.pdist`, `dm.cdist`, `dm.cluster_mols`, `dm.pick_diverse`, `dm.pick_centroids`, `dm.assign_to_centroids`, `dm.find_mcs`, `dm.to_graph`, and `dm.match_molecular_graphs`.
- For invalid SMILES, salt cleanup, standardization, or molecule normalization before fingerprints, use `../molecule-io-prep/`.
- For scaffold extraction, fuzzy scaffolds, enumeration, fragments, reactions, or generated structures, use `../structure-generation/`.
- For drawing cluster representatives, highlighted molecules, or grids of picks, use `../visualization-utilities/`.

## Quick Routing

- Need numeric features for ML or similarity: read the fingerprint and descriptor sections in [references/api-reference.md](references/api-reference.md).
- Need all-vs-all or query-vs-library distances: follow the pairwise/cross-distance recipes in [references/workflows.md](references/workflows.md).
- Need representative molecules: choose Butina clustering, `pick_diverse`, or `pick_centroids` with guidance from [references/workflows.md](references/workflows.md).
- Need shared chemistry across related molecules: use `dm.find_mcs` and validate timeout behavior with [references/troubleshooting.md](references/troubleshooting.md).
- Need atom-index graph correspondence: use `dm.match_molecular_graphs` and watch explicit-hydrogen ambiguity.
