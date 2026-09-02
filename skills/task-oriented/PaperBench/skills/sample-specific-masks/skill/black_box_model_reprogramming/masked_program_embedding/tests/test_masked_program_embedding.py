import math
from masked_embedding import embed_sample, apply_program, embed_batch


def test_mask_preserves_embedded_patch_and_programs_border():
    sample = [[0.2, -0.3], [0.4, 0.5]]
    weights = [[1.0]*4 for _ in range(4)]
    embedded, mask = embed_sample(sample, (4, 4), (1, 1))
    programmed, program = apply_program(embedded, mask, weights)
    assert mask[1][1] == 0.0 and mask[2][2] == 0.0
    assert programmed[1][1] == sample[0][0]
    assert programmed[2][2] == sample[1][1]
    assert abs(programmed[0][0] - math.tanh(1.0)) < 1e-12
    assert program[1][1] == 0.0


def test_embed_batch_uses_universal_program():
    weights = [[0.5]*4 for _ in range(4)]
    out = embed_batch([[[1.0]], [[-1.0]]], (4, 4), weights)
    assert out["program"][0][0] == out["programmed"][0][0][0]
    assert out["program"][0][0] == out["programmed"][1][0][0]
