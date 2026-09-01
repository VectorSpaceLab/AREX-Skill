#!/usr/bin/env python3
"""BAR-style masked target embedding utilities using only the standard library."""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

Matrix = List[List[float]]


def zeros(shape: Sequence[int]) -> Matrix:
    if len(shape) != 2:
        raise ValueError("this lightweight implementation expects 2D shapes")
    return [[0.0 for _ in range(int(shape[1]))] for _ in range(int(shape[0]))]


def center_offset(sample_shape: Sequence[int], canvas_shape: Sequence[int]) -> Tuple[int, int]:
    return ((int(canvas_shape[0]) - int(sample_shape[0])) // 2, (int(canvas_shape[1]) - int(sample_shape[1])) // 2)


def validate_shapes(sample: Matrix, canvas_shape: Sequence[int], offset: Sequence[int]) -> None:
    if len(canvas_shape) != 2 or len(offset) != 2:
        raise ValueError("canvas_shape and offset must be 2D")
    rows = len(sample)
    cols = len(sample[0]) if rows else 0
    if rows == 0 or cols == 0 or any(len(row) != cols for row in sample):
        raise ValueError("sample must be a non-empty rectangular matrix")
    if offset[0] < 0 or offset[1] < 0 or offset[0] + rows > canvas_shape[0] or offset[1] + cols > canvas_shape[1]:
        raise ValueError("sample does not fit in canvas at the requested offset")


def embed_sample(sample: Matrix, canvas_shape: Sequence[int], offset: Sequence[int] | None = None) -> tuple[Matrix, Matrix]:
    off = tuple(offset) if offset is not None else center_offset((len(sample), len(sample[0])), canvas_shape)
    validate_shapes(sample, canvas_shape, off)
    canvas = zeros(canvas_shape)
    mask = [[1.0 for _ in range(int(canvas_shape[1]))] for _ in range(int(canvas_shape[0]))]
    for r, row in enumerate(sample):
        for c, value in enumerate(row):
            rr, cc = off[0] + r, off[1] + c
            canvas[rr][cc] = float(value)
            mask[rr][cc] = 0.0
    return canvas, mask


def apply_program(embedded: Matrix, mask: Matrix, weights: Matrix) -> tuple[Matrix, Matrix]:
    rows, cols = len(embedded), len(embedded[0])
    if len(mask) != rows or len(weights) != rows:
        raise ValueError("mask/weights row count mismatch")
    programmed = zeros((rows, cols))
    program = zeros((rows, cols))
    for r in range(rows):
        if len(mask[r]) != cols or len(weights[r]) != cols:
            raise ValueError("mask/weights column count mismatch")
        for c in range(cols):
            program[r][c] = math.tanh(float(weights[r][c]) * float(mask[r][c]))
            programmed[r][c] = embedded[r][c] + program[r][c]
    return programmed, program


def embed_batch(samples: Iterable[Matrix], canvas_shape: Sequence[int], weights: Matrix, offset: Sequence[int] | None = None) -> dict:
    embedded_batch = []
    programmed_batch = []
    mask = None
    program = None
    for sample in samples:
        embedded, this_mask = embed_sample(sample, canvas_shape, offset)
        programmed, this_program = apply_program(embedded, this_mask, weights)
        if mask is None:
            mask, program = this_mask, this_program
        embedded_batch.append(embedded)
        programmed_batch.append(programmed)
    return {"embedded": embedded_batch, "mask": mask, "program": program, "programmed": programmed_batch}
