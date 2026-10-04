"""Claim schema for one LLM extraction call (one speaker turn).

The LLM fills these fields literally. Dates, counterparty IDs and confidence
are never produced by the LLM; normalization happens in code.
"""

from dataclasses import asdict, dataclass, field

from . import rules


@dataclass
class Claim:
    span: str
    subject_scope: str
    dimension: str
    direction: int
    horizon_text: str
    horizon_ref: str
    comparison_basis: str = "unspecified"
    hedge: int = 0
    counterparty_ref: str | None = None
    quantified: bool = False
    quant_value: float | None = None
    quant_unit: str | None = None
    is_denial: bool = False
    condition: str | None = None

    def errors(self) -> list[str]:
        errs = []
        if not self.span.strip():
            errs.append("empty span")
        if self.subject_scope not in rules.SUBJECT_SCOPES:
            errs.append(f"bad subject_scope {self.subject_scope!r}")
        if self.dimension not in rules.DIMENSIONS:
            errs.append(f"bad dimension {self.dimension!r}")
        lo, hi = rules.DIRECTION_RANGE
        if not isinstance(self.direction, int) or not lo <= self.direction <= hi:
            errs.append(f"bad direction {self.direction!r}")
        if self.horizon_ref not in rules.HORIZON_REFS:
            errs.append(f"bad horizon_ref {self.horizon_ref!r}")
        if self.comparison_basis not in rules.COMPARISON_BASES:
            errs.append(f"bad comparison_basis {self.comparison_basis!r}")
        if self.hedge not in rules.HEDGE_LEVELS:
            errs.append(f"bad hedge {self.hedge!r}")
        if self.subject_scope in ("named_counterparty", "anonymous_counterparty") and not self.counterparty_ref:
            errs.append("counterparty scope without counterparty_ref")
        return errs


@dataclass
class RejectedCandidate:
    span: str
    reason: str
    dimension: str | None = None

    def errors(self) -> list[str]:
        errs = []
        if self.reason not in rules.REJECTION_REASONS:
            errs.append(f"bad reason {self.reason!r}")
        if self.dimension is not None and self.dimension not in rules.DIMENSIONS:
            errs.append(f"bad dimension {self.dimension!r}")
        return errs


@dataclass
class TurnExtraction:
    transcript_id: str
    call_date: str  # ISO date
    turn_index: int
    segment: str
    speaker_role: str
    source_text: str
    run: dict  # {"model", "prompt_version", "temperature"}
    question_turn_index: int | None = None
    claims: list[Claim] = field(default_factory=list)
    rejected_candidates: list[RejectedCandidate] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "TurnExtraction":
        d = dict(d)
        d["claims"] = [Claim(**c) for c in d.get("claims", [])]
        d["rejected_candidates"] = [RejectedCandidate(**r) for r in d.get("rejected_candidates", [])]
        return cls(**d)

    def to_dict(self) -> dict:
        return asdict(self)

    def errors(self) -> list[str]:
        errs = []
        if self.segment not in rules.SEGMENTS:
            errs.append(f"bad segment {self.segment!r}")
        for key in ("model", "prompt_version", "temperature"):
            if key not in self.run:
                errs.append(f"run missing {key}")
        for i, c in enumerate(self.claims):
            errs += [f"claims[{i}]: {e}" for e in c.errors()]
            if c.span not in self.source_text:
                errs.append(f"claims[{i}]: span not verbatim in source_text")
        for i, r in enumerate(self.rejected_candidates):
            errs += [f"rejected_candidates[{i}]: {e}" for e in r.errors()]
        return errs
