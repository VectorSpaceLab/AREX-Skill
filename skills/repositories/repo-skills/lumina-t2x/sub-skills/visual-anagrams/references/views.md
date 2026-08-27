# Visual Anagram Views

## Purpose

Read this when you need to choose view names or supply `view_args` for the visual-anagram generator.

## Supported views

The repository's `get_anagrams_views()` helper accepts these names:

- `identity`
- `flip`
- `rotate_cw`
- `rotate_ccw`
- `rotate_180`
- `negate`
- `skew`
- `patch_permute`
- `pixel_permute`
- `jigsaw`
- `inner_circle`
- `square_hinge`
- `inner_circle_failure`
- `blur_failure`
- `white_balance_failure`
- `low_pass`
- `high_pass`
- `triple_low_pass`
- `triple_medium_pass`
- `triple_high_pass`
- `grayscale`
- `color`
- `motion`
- `motion_res`
- `scale`

## Common `view_args` defaults

- `patch_permute`: `8`
- `pixel_permute`: `64`
- `skew`: `1.5`
- `low_pass` / `high_pass`: `2.0`
- `scale`: `0.5`

## Selection guidance

- Use `identity`, `flip`, or `rotate_*` for the simplest two-view experiments.
- Use `patch_permute` or `pixel_permute` when you want a stronger shuffling effect.
- Use the `motion*` variants when the animation path should emphasize motion blur.
- Keep the number of views equal to the number of prompts.
