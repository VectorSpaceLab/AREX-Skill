# Structure-curation troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| PDB import fails | Malformed records, unsupported formatting, or truncated file | Preserve the original, identify the offending record, repair with a reviewed structure tool, and revalidate. Do not patch coordinates by hand without recording it. |
| Required chain is absent | Wrong structure, chain renaming, or an extraction already removed it | Check the source ID and chain map; stop and report the mismatch rather than selecting a similarly named chain. |
| Range selector rejects a residue ID | Insertion code or non-numeric ID | Use an explicit reviewed selection workflow that preserves the identifier; do not coerce it to an integer. |
| Selection writes zero atoms | Chain/range syntax does not match parsed IDs | Run `--dry-run`, inspect chain and residue reports, and correct the selector. |
| Duplicate atom names remain | Names were duplicated across a residue or an external tool reintroduced them | Run the validator with duplicate rejection, then normalize only the uniquely selected residue; verify downstream chemistry afterward. |
| PDB parses but simulation template matching fails | Residue names, termini, hydrogens, or caps do not match the force field | Route to protonation/capping and system-preparation review; a parse is not a force-field match. |
| Ligand is disconnected or has wrong bonds | PDB conversion lost SDF bond/charge information or the residue edit was ambiguous | Return to the SDF/chemistry source, compare atom mapping and bonds with a chemical toolkit, and refuse generic protein parameterization. |
| Missing hydrogens or caps | External preparation was skipped or output was altered | Record the blocked preparation step and run the intended external tool or a reviewed alternative, then revalidate. |
| Maestro/PyMOL is unavailable | Historical workflow used a proprietary/manual step | State the limitation. Do not claim automatic protonation or extraction; provide a reproducible replacement only if its chemistry is verified. |
| Output overwrites input or prior result | Same path was supplied or an old artifact was reused | Choose a new output path; helpers refuse existing outputs unless `--overwrite` is explicit. |
| Domain selection looks plausible but is wrong | A filename or common domain name was treated as an identity | Cross-check chain/residue provenance against the source structure and record the exact selection. |
| FASTA/SDF was treated as a simulation-ready PDB | Format roles were conflated | Use FASTA for sequence cross-checks and SDF for chemistry evidence; create and validate an explicit coordinate/topology artifact. |
