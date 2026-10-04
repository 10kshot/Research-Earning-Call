"""Resolve each claim against its own outcome with the evidence hierarchy.

No winner is picked per pair. Tier C (later manager statements) can never
clear a claim, so it is ignored here and handled only in robustness runs.
"""

from dataclasses import dataclass

from . import rules


@dataclass(frozen=True)
class Signal:
    tier: str  # "A" or "B"
    change: float  # seasonal-adjusted change on the claim's comparison basis
    seasonal_sd: float  # SD of the firm's normal change in the same fiscal quarter
    offset: int = 0  # quarters from the claim's target quarter (-1 early, +1 late)
    source: str = ""


def _realized_sign(sig: Signal) -> int:
    if abs(sig.change) <= rules.NO_CALL_ZONE_SD * sig.seasonal_sd:
        return 0
    return 1 if sig.change > 0 else -1


def label_claim(direction: int, signals: list[Signal]) -> tuple[str, str | None]:
    """Return (label, tier used). Uses the best tier available only."""
    for tier in ("A", "B"):
        tier_sigs = [s for s in signals if s.tier == tier]
        if not tier_sigs:
            continue
        on_target = [s for s in tier_sigs if s.offset == 0]
        if not on_target:
            continue
        signs = {_realized_sign(s) for s in on_target}
        if len(signs) > 1:
            return "conflicted", tier
        realized = signs.pop()
        claimed = (direction > 0) - (direction < 0)
        if realized == claimed:
            return "right", tier
        if realized == -claimed and claimed != 0:
            return "wrong", tier
        # Flat on target, or a flat claim that moved: check one quarter off.
        for s in tier_sigs:
            if s.offset in (-1, 1) and claimed != 0 and _realized_sign(s) == claimed:
                return ("early" if s.offset == -1 else "late"), tier
        return ("flat" if realized == 0 else "wrong"), tier
    return "unresolved", None


def credibility_score(past_labels: list[str], sample_wrong_rate: float,
                      prior_weight: float = rules.CREDIBILITY_PRIOR_WEIGHT) -> float:
    """Shrunk share of a firm's past claims labeled wrong.

    `past_labels` must contain only claims whose check date precedes the call date.
    Unresolved and conflicted claims are excluded from the denominator.
    """
    resolved = [l for l in past_labels if l not in ("unresolved", "conflicted")]
    wrong = sum(l == "wrong" for l in resolved)
    return (wrong + prior_weight * sample_wrong_rate) / (len(resolved) + prior_weight)
