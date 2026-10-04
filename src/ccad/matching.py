"""Deterministic contradiction scoring with the fixed mapping table (no LLM judge).

Input cells are aggregated from the claim table at the
(firm, subject, dimension, target quarter) level for one supplier -> customer link.
"""

from dataclasses import dataclass

from . import rules


@dataclass(frozen=True)
class Cell:
    dimension: str
    quarter: int  # calendar quarter index (see calendar.qidx)
    direction: int  # aggregated net direction, -2..+2
    hedge: int  # max hedge across the claims in the cell
    claim_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Contradiction:
    kind: str  # "level" or "timing"
    supplier: Cell
    customer: Cell
    expected_sign: int
    lag: int


def _sign(x: int) -> int:
    return (x > 0) - (x < 0)


def _agrees(s: Cell, c: Cell, expected: int) -> bool:
    return _sign(s.direction) * expected == _sign(c.direction)


def _opposes(s: Cell, c: Cell, expected: int) -> bool:
    # Only strictly opposite non-zero signs count; a flat claim never contradicts.
    return _sign(s.direction) * expected == -_sign(c.direction) != 0


def _linked_pairs(supplier_cells: list[Cell], customer_cells: list[Cell]):
    """Yield (supplier, customer, expected sign, lag, customer cells by quarter, lag window)
    for every mapped pair within the allowed lag. Cells with hedge above
    MAX_HEDGE_FOR_CC are skipped."""
    usable = lambda cells: [x for x in cells if x.hedge <= rules.MAX_HEDGE_FOR_CC]
    sup, cus = usable(supplier_cells), usable(customer_cells)
    for s_dim, c_dim, expected, window in rules.MAPPING_TABLE:
        c_by_q = {x.quarter: x for x in cus if x.dimension == c_dim}
        for s in (x for x in sup if x.dimension == s_dim):
            for lag in range(window[0], window[1] + 1):
                c = c_by_q.get(s.quarter + lag)
                if c is not None:
                    yield s, c, expected, lag, c_by_q, window


def score_link(supplier_cells: list[Cell], customer_cells: list[Cell]) -> list[Contradiction]:
    """Return contradictions for one link.

    Level: within the allowed lag, directions oppose the expected sign.
    Timing: the same disagreement, but the customer agrees with the supplier
    at a lag one quarter outside the allowed window (bullwhip-style shift).
    """
    out = []
    for s, c, expected, lag, c_by_q, (lag_lo, lag_hi) in _linked_pairs(supplier_cells, customer_cells):
        if not _opposes(s, c, expected):
            continue
        shifted = [c_by_q.get(s.quarter + l) for l in (lag_lo - 1, lag_hi + 1)]
        kind = "timing" if any(x and _agrees(s, x, expected) for x in shifted) else "level"
        out.append(Contradiction(kind, s, c, expected, lag))
    return out


@dataclass(frozen=True)
class FlatMismatch:
    flat_side: str  # "supplier" or "customer": the side whose cell is flat (direction 0)
    supplier: Cell
    customer: Cell
    expected_sign: int
    lag: int


def flat_mismatches(supplier_cells: list[Cell], customer_cells: list[Cell]) -> list[FlatMismatch]:
    """Pairs where one side is flat and the other moves. These never count as
    contradictions (rule book v1) but are kept for later analysis."""
    out = []
    for s, c, expected, lag, _, _ in _linked_pairs(supplier_cells, customer_cells):
        s_flat, c_flat = s.direction == 0, c.direction == 0
        if s_flat != c_flat:
            out.append(FlatMismatch("supplier" if s_flat else "customer", s, c, expected, lag))
    return out
