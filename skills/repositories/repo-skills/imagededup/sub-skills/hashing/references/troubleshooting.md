# Hashing troubleshooting

## `Please provide a valid directory path!`

- The path passed to `encode_images` or directory-based search is not a directory.
- Fix: pass the directory root, not a single file.

## `Please provide either image file path or image array!`

- `encode_image` received the wrong input type.
- Fix: pass one real file path or one numpy image array.

## `Threshold must be an int between 0 and 64`

- The hash threshold is either not an integer or outside the valid range.
- Fix: use an integer in `0..64`.

## `Provide either an image directory or encodings!`

- `find_duplicates` or `find_duplicates_to_remove` was called without a valid input source.
- Fix: supply `image_dir` or `encoding_map`, but not neither.

## Warnings about `recursive` or `num_enc_workers`

- These warnings usually mean an encoding map was supplied and directory-only flags no longer matter.
- Fix: drop irrelevant directory flags when you already have hashes.

## Windows multiprocessing issues

- Running hash workflows directly from a script on Windows can fail unless the body is under `if __name__ == '__main__':`.
- Fix: wrap the runnable code in a main guard.

## Bad or unreadable images

- The hash workflows ignore unreadable files rather than crashing the entire directory pass.
- Fix: inspect the skipped files and verify the image format or corruption state.

## Cython backend problems

- A failure in `brute_force_cython` usually points to the editable install or compiled extension setup, not the hash API itself.
- Fix: reinstall the package after ensuring build dependencies are present.
- If you only need correctness, compare against `brute_force` or `bktree`.

## Heuristic removal-list surprises

- `find_duplicates_to_remove` can legitimately keep different members of a duplicate cluster depending on traversal order.
- Fix: treat the output as a candidate list, not a uniquely determined canonical deletion set.

## When to escalate

- If the request is about pretrained CNN encodings or custom PyTorch models, switch to the CNN sub-skill.
- If the request is about scoring or plotting the duplicate map, switch to the evaluation sub-skill.