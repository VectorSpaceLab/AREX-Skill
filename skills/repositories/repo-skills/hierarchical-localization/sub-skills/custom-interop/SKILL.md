---
name: custom-interop
description: "Support custom HLoc features, retrieval descriptors, match files,
  modules, and data-format interoperability."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# custom-interop

Use this sub-skill when the user already has, or wants to create, non-standard inputs for HLoc: externally computed local features, global image descriptors, sparse match files, custom PyTorch extractors or matchers, query/image/retrieval/pose lists, or an interoperability validator before routing into HLoc workflows.

## Route here for

- Supplying local feature HDF5 files instead of running a built-in extractor.
- Supplying global descriptor HDF5 files for retrieval pair generation.
- Supplying sparse match HDF5 files instead of running a built-in matcher.
- Adding a custom extractor or matcher module that follows HLoc's `BaseModel` and `dynamic_load` contracts.
- Checking pair names, image/query lists, retrieval files, pose result files, and HDF5 schema compatibility.

## Route elsewhere

- To choose or run built-in feature, retrieval, sparse matching, or dense matching configurations, load sibling [feature-retrieval](../feature-retrieval/SKILL.md).
- To reconstruct, triangulate, generate mapping/localization pairs, or localize queries from validated artifacts, load sibling [mapping-localization](../mapping-localization/SKILL.md).
- To plan Aachen, InLoc, 4Seasons, 7Scenes, CMU, Cambridge, RobotCar, or other benchmark-scale dataset procedures, load sibling [dataset-pipelines](../dataset-pipelines/SKILL.md).

## Operating flow

1. Identify whether the user is extending HLoc with a Python module or exporting external artifacts.
2. For Python modules/configs, follow [references/extension-guide.md](references/extension-guide.md) for `BaseModel`, `dynamic_load`, module naming, `default_conf`, `required_inputs`, and config dictionary rules.
3. For external files, follow [references/data-formats.md](references/data-formats.md) for feature, global descriptor, match, retrieval, list, and pose schemas.
4. Validate candidate artifacts before using them downstream:

   ```bash
   python sub-skills/custom-interop/scripts/validate_hloc_formats.py \
     --features outputs/features.h5 \
     --matches outputs/matches.h5 \
     --retrieval pairs-query-db.txt \
     --image-list queries_with_intrinsics.txt
   ```

   Add `--strict` when files are intended for HLoc sparse matching and should contain all matcher-friendly fields such as `image_size` and `matching_scores0`.
5. If validation passes, route the next step to [feature-retrieval](../feature-retrieval/SKILL.md) for retrieval-pair generation or built-in matching, or to [mapping-localization](../mapping-localization/SKILL.md) for SfM/localization.
6. If validation fails, use [references/troubleshooting.md](references/troubleshooting.md) to map symptoms to likely schema, naming, parser, or custom-module contract errors.

## Quick decisions

- Prefer exporting HDF5 artifacts when the user's model is not PyTorch-based, cannot be cleanly imported into the `hloc.extractors` or `hloc.matchers` namespaces, or already runs in another framework.
- Prefer a custom module when the user wants to call `hloc.extract_features.main`, `hloc.match_features.main`, or the corresponding CLIs with a reusable named config.
- Always keep image names consistent across image lists, feature groups, retrieval pairs, match groups, SfM model image names, and localization queries. A single slash, prefix, or basename mismatch is enough to make downstream code report missing images, missing pairs, or absent HDF5 groups.
