---
name: target-preparation
description: "Validate a BindCraft target PDB and construct a target JSON with
  explicit chains, hotspots, binder length range, naming, and output-path
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Prepare a BindCraft target

Use this sub-skill before launching a design campaign. It turns a target PDB
and design intent into a checked, portable target-settings JSON; it does not
run AF2, ProteinMPNN, PyRosetta, or a design trajectory.

## Route

1. Keep the target PDB trimmed to the smallest biologically justified region.
   Preserve the target chains and standard amino-acid residues needed for the
   intended interface; do not assume that trimming is harmless for a
   target-dependent result.
2. Copy the seven-key template and replace every path with a path valid on the
   machine that will launch BindCraft. Do not make the checked-in example's
   absolute paths a runtime dependency.
3. Set `chains` to the target chain IDs. Use explicit chain-qualified hotspots
   for a multi-chain target when residue numbering could be ambiguous.
4. Set `target_hotspot_residues` to `null` for AF2-selected site discovery, or
   to the documented residue/range syntax for a deliberate site. Validate
   every selected chain and hotspot against the PDB when the PDB is available.
5. Run the bundled read-only validator:

   ```bash
   python skills/disco/bindcraft/sub-skills/target-preparation/scripts/validate_target.py \
     --target-json ./settings_target/my_target.json \
     --pdb ./inputs/my_target.pdb
   ```

   Omitting `--pdb` still validates JSON and reports declared paths, but cannot
   prove that chains or residue numbers exist. The validator never creates,
   rewrites, downloads, or imports from the BindCraft checkout.
6. Hand the validated JSON to the design route. For GPU/model, algorithm,
   filter, and launch decisions, see [design-pipeline](../design-pipeline/SKILL.md).
   For post-run artifacts and metrics, see [results-analysis](../results-analysis/SKILL.md).

Schema and syntax details are in [data-formats](references/data-formats.md);
input and filesystem failure recovery is in
[troubleshooting](references/troubleshooting.md).

## Safety boundary

The JSON/PDB checks are CPU-safe inspection only. BindCraft's actual AF2/MPNN
binder-design loop requires the prepared CUDA environment, model weights, and
other documented prerequisites; a successful target validation is not evidence
that a design can run or that a target will yield binders. PyRosetta licensing,
AF2-weight availability, GPU memory, and target-dependent behavior remain
separate launch gates.
