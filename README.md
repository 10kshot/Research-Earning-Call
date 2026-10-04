# Counterparty Contradictions & Abnormal Disclosure in Earnings Calls

- **Proposal (1 page):** [proposal/proposal.md](proposal/proposal.md)
- **Full research plan v2 (Sept 13, 2026):** [docs/research_plan_v2.html](docs/research_plan_v2.html)

## Layout

| Path | Contents |
|---|---|
| `proposal/` | One-page proposal |
| `docs/` | Full plan; future rule book changelog |
| `prompts/` | Versioned LLM extraction prompts (`extract_v1.md` is a draft) |
| `src/ccad/rules.py` | Rule book v1: dimensions, claim gate codes, mapping table, resolution constants, validation bar |
| `src/ccad/schema.py` | Claim / rejected-candidate / turn schema with validation (span must be verbatim) |
| `src/ccad/fiscal.py` | Fiscal → calendar quarter conversion (Compustat FYR convention) |
| `src/ccad/matching.py` | Deterministic level / timing contradiction scoring |
| `src/ccad/resolution.py` | Claim labels with evidence hierarchy; real-time credibility score |
| `data/raw` | Transcripts, Compustat, I/B/E/S, CRSP extracts (git-ignored; licensed) |
| `data/interim` | Turn-level records, raw extraction output (git-ignored) |
| `data/processed` | Normalized claim table, CC/AD panels (git-ignored) |
| `data/gold` | Hand-coded dev and held-out gold sets (tracked) |

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

No third-party dependencies yet.

## Status (2026-10-04)

- Rule book constants and core rules are coded and unit-tested. No data loaded yet.
- Open: transcript source and format; WRDS access; supply-chain link file for the ~40-firm semiconductor pilot.
