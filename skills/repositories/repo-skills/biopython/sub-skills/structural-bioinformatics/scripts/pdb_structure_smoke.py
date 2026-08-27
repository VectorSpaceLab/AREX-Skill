#!/usr/bin/env python3
"""Safe offline smoke test for Biopython Bio.PDB structure workflows."""

from __future__ import annotations

from pathlib import Path
import tempfile

from Bio.PDB import NeighborSearch, PDBIO, PDBParser


PDB_TEXT = """\
HEADER    TINY BIO.PDB SMOKE
ATOM      1  N   GLY A   1       0.000   0.000   0.000  1.00 10.00           N
ATOM      2  CA  GLY A   1       1.450   0.000   0.000  1.00 10.00           C
ATOM      3  C   GLY A   1       2.050   1.330   0.000  1.00 10.00           C
ATOM      4  O   GLY A   1       1.450   2.370   0.000  1.00 10.00           O
ATOM      5  N   ALA A   2       3.310   1.310   0.000  1.00 10.00           N
ATOM      6  CA  ALA A   2       4.020   2.560   0.000  1.00 10.00           C
ATOM      7  C   ALA A   2       5.520   2.350   0.000  1.00 10.00           C
ATOM      8  O   ALA A   2       6.020   1.240   0.000  1.00 10.00           O
TER       9      ALA A   2
END
"""


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        pdb_path = Path(tmpdir) / "tiny.pdb"
        pdb_path.write_text(PDB_TEXT, encoding="ascii")

        parser = PDBParser(PERMISSIVE=False, QUIET=True)
        structure = parser.get_structure("tiny", str(pdb_path))

        models = list(structure)
        assert len(models) == 1, models
        model = models[0]
        chain = model["A"]
        residues = list(chain)
        assert [res.get_resname() for res in residues] == ["GLY", "ALA"]

        atoms = list(structure.get_atoms())
        assert len(atoms) == 8
        assert [atom.get_name() for atom in atoms[:4]] == ["N", "CA", "C", "O"]

        ca1 = chain[1]["CA"]
        ca2 = chain[2]["CA"]
        ca_distance = ca1 - ca2
        assert 3.5 < ca_distance < 3.8, ca_distance

        neighbors = NeighborSearch(atoms)
        near_residues = neighbors.search(ca1.get_coord(), 2.1, level="R")
        assert chain[1] in near_residues
        assert chain[2] not in near_residues

        close_atom_pairs = neighbors.search_all(1.7, level="A")
        assert close_atom_pairs, "expected at least one bonded-distance atom pair"

        out_path = Path(tmpdir) / "roundtrip.pdb"
        writer = PDBIO()
        writer.set_structure(structure)
        writer.save(str(out_path))
        reparsed = parser.get_structure("roundtrip", str(out_path))
        assert len(list(reparsed.get_atoms())) == len(atoms)

    print("PASS Bio.PDB structural smoke")


if __name__ == "__main__":
    main()
