---
name: hashing
description: "Find exact or near-duplicate images with perceptual, average,
  difference, or wavelet hashing in imagededup."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# hashing

Use this sub-skill when the user wants hash-based duplicate detection or hash generation with `PHash`, `AHash`, `DHash`, or `WHash`.

## Best-fit tasks

- Generate a hash for one image or a whole directory.
- Find near duplicates by Hamming distance.
- Produce a list of files to remove from a duplicate map.
- Compare hash backends such as `bktree`, `brute_force`, and `brute_force_cython`.
- Work from a directory of images or from a precomputed encoding map.

## Read this sub-skill first when the request mentions

- `PHash`, `AHash`, `DHash`, or `WHash`
- `encode_image` or `encode_images`
- `find_duplicates` or `find_duplicates_to_remove`
- `max_distance_threshold`
- `search_method`
- `bktree`, `brute_force`, or `brute_force_cython`
- Hamming distance, exact duplicates, or near duplicates

## Workflow overview

1. Pick the hash family.
   - `PHash` for perceptual hashing.
   - `AHash` for average hashing.
   - `DHash` for difference hashing.
   - `WHash` for wavelet hashing.
2. Encode either a single image or a directory.
3. Search duplicates from the directory or from the encoding map.
4. If the user wants a removal list, turn the duplicate map into filenames to remove.
5. If the user is on Windows, keep the multiprocessing warning and main-guard behavior in mind.

## Common decisions

- Use `encode_image` when the user already has one image file or one image array.
- Use `encode_images` when the user has a directory.
- Use `find_duplicates` when the user needs a full duplicate map.
- Use `find_duplicates_to_remove` when the user wants one heuristic list of files to delete later.
- Use `encoding_map` when hashes were already computed earlier.
- Use `search_method` only when the user needs to compare backends or override the default.

## Helpful facts

- Hash encodings are hexadecimal strings.
- `find_duplicates` returns lists of duplicate filenames, or `(filename, score)` tuples when `scores=True`.
- `find_duplicates_to_remove` never deletes files; it only returns a candidate list.
- Hash thresholds are integer Hamming distances from `0` to `64`.
- The default hash search backend is `brute_force_cython` on Unix-like systems and `bktree` on Windows.
- Recursive directory scanning is optional and off by default.

## Image handling notes

- The hash path accepts either an image file path or a numpy image array.
- Invalid or unreadable images are skipped rather than crashing the whole directory workflow.
- Supported formats are the Pillow formats documented by the repo, but loadability still depends on the actual image file and Pillow plugins.
- If you pass an encoding map, directory-only flags such as `recursive` do not matter.

## Troubleshooting pointer

Read [`references/troubleshooting.md`](references/troubleshooting.md) for threshold errors, Windows multiprocessing, invalid image input, and Cython-backend issues.

## Script helper

Run [`scripts/hash_smoke.py`](scripts/hash_smoke.py) to exercise the hash workflow on synthetic images without depending on the original checkout.

## When to escalate elsewhere

- If the task is really about CNN features or custom PyTorch models, switch to the CNN sub-skill.
- If the task is about scoring or visualizing a retrieved duplicate map, switch to the evaluation sub-skill.

## Good output expectations

A good hash-oriented answer should usually include:

- the hash class selected
- the input type expected by the method
- the threshold semantics
- the search backend if it matters
- the shape or type of the returned value
- any Windows or multiprocessing caveat that applies