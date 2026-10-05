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
| `src/ccad/transcripts.py` | StreetEvents `*_T.xml` parser: call metadata, speaker roles, prepared/Q&A turns, question–answer pairing |
| `src/ccad/sources.py` | Transcript sources: local XML (now) or Supabase (stub until the database is unlocked; credentials go in a git-ignored `.env`) |
| `scripts/build_turns.py` | Batch parser → `data/interim/calls_<year>.csv`, `turns_<year>.jsonl` (`--source local\|supabase`). `turn_index` restarts at 1 in the Q&A section, so a turn is keyed by `(segment, turn_index)` |
| `data/raw` | `transcripts/<year>/*_T.xml` (StreetEvents), `legacy_keyword_exposure/` (old risk/activeness study output); later Compustat, I/B/E/S, CRSP (git-ignored; licensed) |
| `data/interim` | Turn-level records, raw extraction output (git-ignored) |
| `data/processed` | Normalized claim table, CC/AD panels (git-ignored) |
| `data/gold` | Hand-coded dev and held-out gold sets (tracked) |

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

No third-party dependencies yet.

## Status (2026-10-04)

- Rule book constants and core rules are coded and unit-tested.
- 2016 transcripts (18,401 StreetEvents `*_T.xml` files, all event types, plus 6 byte-identical `*_T(1).xml` copies that the loader ignores; an earlier note said 26,049, which does not match this folder) copied from `Quant Trading Project/research-main/data/earnings_calls/2016`. Only 2016 is available so far; the pilot needs 2018–2025.
- Build turns: `PYTHONPATH=src python3 scripts/build_turns.py 2016`
- Other years are in the lab Supabase database, locked as of 2026-10-04. Old code only read scores and matched sentences from it, so it is unconfirmed whether full transcript text is stored there.
- Open: 2018–2025 transcripts; WRDS access; supply-chain link file for the ~40-firm semiconductor pilot.
