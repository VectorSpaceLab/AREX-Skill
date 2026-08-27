# Target preparation troubleshooting

Use the validator in read-only mode first. It returns a non-zero status for
invalid JSON/schema, an unreadable explicitly supplied PDB, missing selected
chains/residues, or invalid hotspot syntax. It may emit warnings for portability
or conservative structural checks; warnings do not imply that a design is safe
or likely to succeed.

## Malformed or incomplete JSON

**Symptoms:** `JSONDecodeError`, missing-key messages, wrong-type errors, or a
validator report that does not name all seven keys.

1. Check that the file is UTF-8 JSON, uses double-quoted keys/strings, and has
   no trailing comma or comments.
2. Compare the object with the seven-key table in
   [data-formats](data-formats.md). Do not rename `starting_pdb`, `chains`, or
   `target_hotspot_residues`.
3. Keep `target_hotspot_residues` as JSON `null` for AF2-selected sites; do not
   use an unquoted Python `None`.
4. Make `lengths` exactly two positive integers in ascending order and make
   `number_of_final_designs` a positive integer, not a string.
5. Re-run with `--target-json` after editing. The checker does not rewrite the
   configuration.

## Missing chains or residues

**Symptoms:** selected chain is absent, or a hotspot/range is outside the PDB
residue summary.

- Inspect the PDB with `--pdb` and compare the reported chain IDs and residue
  numbers. PDB chain IDs are case-sensitive; `a` is not `A`.
- For a multi-chain structure, use `chains: "A,B"` and explicit hotspot tokens
  such as `A56-60,B102`. Do not use an unqualified number when the same site
  could be confused across chains.
- Confirm that the PDB has not been renumbered during trimming, converted from
  mmCIF, or reduced to a sequence-only file. Residues are author numbers, not
  positions in a zero-based array.
- Check alternate locations, insertion codes, and missing backbone atoms by
  inspecting the target in a structural viewer or a domain-appropriate parser.
  The validator reports insertion codes but does not invent a mapping for them.
- A missing hotspot in a PDB is a hard input error for a constrained design;
  choose a present residue/range or intentionally use `null` after reviewing
  the target biology.

## Invalid hotspot ranges or syntax

**Symptoms:** malformed-token/range errors, a range with its end before its
start, a chain-qualified token for an unselected chain, or a number outside the
PDB.

- Supported documented forms are `56`, `56,60-61`, `A56-60,B102`, and `A`.
  Use commas as separators and hyphens only for inclusive numeric ranges.
- Do not insert spaces inside `A56-60`, use negative numbers, or rely on
  insertion-code syntax without testing the exact downstream parser.
- `null` means AF2 chooses the site; it is not equivalent to a malformed or
  empty token. The current source treats an empty string as no hotspot, but
  `null` is the recommended portable representation.
- A whole-chain hotspot (`A`) requires that `A` is in `chains`. For a selected
  chain list, every chain-qualified hotspot must be selected.
- If the intended site is not represented in a trimmed PDB, stop and repair the
  target rather than weakening validation merely to make JSON pass.

## Oversized or unsuitable targets

**Symptoms:** memory exhaustion, slow preprocessing, AF2 out-of-memory errors,
or a target that includes unrelated chains/domains.

- Trim to the smallest biologically justified target region and remove
  irrelevant chains, waters, and unrelated assembly components while retaining
  interface context. Preserve numbering and document any preprocessing.
- BindCraft's README recommends at least 32 GB GPU memory for larger complexes;
  actual requirements depend on target plus binder size and settings. A CPU
  validator cannot predict a successful GPU design run.
- Large targets may need a lower binder range or a less memory-intensive
  algorithm, but these are design-pipeline decisions. Link to
  [design-pipeline](../../design-pipeline/SKILL.md) rather than changing advanced
  settings in this sub-skill.
- Do not claim that a trimmed or validated target will produce binders; target
  site choice and target-dependent AF2 behavior remain experimental variables.

## Output permissions and paths

**Symptoms:** `PermissionError`, inability to create the design tree, or output
files appearing in an unexpected location.

- Resolve `design_path` to an intended directory and verify the launch user can
  traverse its parent and create a small test file there. Remove the test file
  before launch; do not ask the validator to mutate the destination.
- Prefer a user-owned local or scratch path, with one directory per campaign.
  Avoid read-only mounted drives, unexpanded `~` in automation, and stale
  notebook- or cloud-specific absolute paths unless that environment really exists.
- Check that `binder_name` is a label without path separators. A path-like name
  can cause confusing artifact locations and filename collisions.
- `starting_pdb` and `design_path` are interpreted by the eventual launcher;
  the validator reports their declared values and only reads the optional PDB
  passed with `--pdb`. It does not require repository-specific absolute paths
  to exist and does not create output directories.

## What this check cannot prove

A successful report proves only basic JSON semantics and, when `--pdb` is
provided, conservative chain/residue presence and PDB record parsing. It does
not validate AF2 parameter weights, CUDA/JAX/ColabDesign, ProteinMPNN,
PyRosetta licensing, DSSP, DAlphaBall, filter/advanced JSONs, structural
biological correctness, or final binder quality. Use the sibling design and
results routes for those concerns.
