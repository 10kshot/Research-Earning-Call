# Your Customers Tell a Different Story: Counterparty Contradictions and Abnormal Disclosure in Earnings Calls

*One-page research proposal · October 3, 2026 · condensed from research plan v2, Sept 13, 2026 ([docs/research_plan_v2.html](../docs/research_plan_v2.html))*

**Problem.** Tone and risk-word measures of earnings calls are losing power because managers now write for machine readers. They avoid flagged words and rehearse their answers. Any measure built only on a manager's own words can be gamed by that manager. This study measures disclosure quality against benchmarks the manager does not control.

**Main idea.** The study uses two measures, each checked against what actually happened.

- **Counterparty contradictions (CC).** A supplier and its customer each describe the same relationship on their own calls. Where they disagree about demand, orders, inventory, prices or capacity, I resolve each claim later using hard data to see who was right. The focal manager can't script the counterparty's words.
- **Abnormal disclosure (AD).** This applies Jones-model logic to text. AD = what a manager claims − what fundamentals and public information imply, estimated as a regression residual on past data only. AD is built *without* counterparty data and validated against CC, so it can also be used for firms that have no observed links.

**Hypotheses.**
H1: AD predicts CC.
H2: Claims later resolved as wrong come from firms with high AD, incentives to spin (missed consensus, equity issuance, insider selling) and a weak credibility record.
H3a (descriptive): the stock of the firm that turns out to be wrong drifts toward the outcome rather than adjusting at once.
H3b (tradable, no look-ahead): firms with high *predicted* wrongness earn negative abnormal returns, especially where few analysts also cover the counterparty.
H4: AD and CC predict volatility, abnormal volume, earnings misses, guidance cuts and crash risk, beyond tone and risk words.

**Methods.**

1. **Claim extraction.** One structured-output LLM call per speaker turn, with the analyst's question attached to each Q&A answer. A statement counts as a claim only if it states what it is about (one of 9 fixed dimensions), which way it goes (a −2…+2 change), when (a horizon), and could later be shown false. Anything else goes to `rejected_candidates` with a reason code. Extraction is literal, and the LLM gives no self-reported confidence.
2. **Normalization in code.** Fiscal horizons are converted to calendar ranges using Compustat fiscal year-ends. Counterparty references are resolved through the supply-chain network. The claim-level table is the single source of truth.
3. **Matching.** Contradictions are scored with a fixed mapping table of expected signs and allowed lags, not an LLM judge. *Level* contradictions are kept separate from *timing* contradictions, which are often honest bullwhip effects. Silence and evasion (an analyst asked and the answer produced no claim) are separate rule-based passes.
4. **Resolution.** Each claim is scored against its own outcome, labeled right / wrong / flat / early-late / conflicted / unresolved. The evidence hierarchy is Tier A hard data (e.g. counterparty inventory, implied purchases = COGS + ΔInventory, capex, actuals vs. guidance, PPI), then Tier B proxies, then Tier C later manager statements, which are robustness only and can never clear a claim. The check date is fixed and outcomes use first-reported numbers. A firm's credibility score is the shrunk share of its past claims resolved wrong before the call date.
5. **Tests.** Fixed-effect panel regressions (H1, H4), a linear probability model and logit for being wrong (H2), and CARs over [t+2, t+60] plus calendar-time FF5+momentum alphas (H3). H3b uses predicted wrongness from an expanding-window H2 model. Moderators are fixed in advance and all reported: the share of firm *i*'s analysts who also cover *j* (I/B/E/S, 12 months), and whether an analyst on the later call referenced the counterparty. Robustness checks include placebo unlinked pairs, LLM look-ahead tests and Tier A-only results.

**Data.** Transcripts (StreetEvents / Capital IQ / FactSet), Compustat quarterly and customer segments, I/B/E/S detail, CRSP, Form 4, PPI and industry billings. **Pilot:** about 40 semiconductor supply-chain firms, 2018–2025, which covers the 2022–23 inventory correction. **Full sample:** Russell 1000 firms with links, 2010–2025.

**Validation and design principles.** The gold set is split into dev and held-out parts. The bar on held-out data is dimension accuracy ≥ 85%, direction accuracy ≥ 80% and rare opposite-sign errors, reported separately. A second coder labels claims for the paper. The rule book (gate, mapping table, resolution rules, moderators, specifications) is committed before any return data is examined. Every number traces back to a verbatim quote. The design favors reproducibility over sophistication.

**Pilot plan (8 weeks) and decision gate.** Weeks 1–2: rule book and data. Weeks 3–4: gold sets and extraction. Weeks 5–6: contradictions. Weeks 7–8: Tier A resolution and first evidence. The study scales up only if extraction passes the bar, there are at least ~20 level contradictions, the false-contradiction rate is well below half, and a meaningful share of claims resolve at Tier A. Otherwise the paper's weight shifts to AD, with CC as validation.

**Contribution.** An external, hard-to-game benchmark for disclosure quality. Abnormal-accrual logic applied to individual narrative claims. A real-time credibility record for managers. Evidence on whether investors read both sides of an economic link.
