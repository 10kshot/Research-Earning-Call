# extract_v1 — claim extraction prompt (DRAFT, tune on dev gold set only)

Run settings: temperature 0, pinned model ID, structured output matching `src/ccad/schema.py`.
Context sent with each turn: call date, fiscal year-end month, segment, speaker role,
and for Q&A answers the preceding analyst question.

---

You extract forward-looking business claims from one speaker turn of an earnings call.

A statement is a **claim** only if it answers all of these:
1. **About what**: one of these dimensions: end_demand, orders_backlog, inventory_own,
   inventory_downstream, selling_price, input_cost, capacity_supply, capex_procurement, margin.
2. **Which way**: a direction for the *change* in that variable, from −2 (sharp decrease) to +2 (sharp increase).
   A level ("inventory is elevated") is not a direction. A change ("we're working inventory down") is −1.
3. **When**: a horizon, copied as written ("into Q4", "second half", "next year").
4. **Falsifiable**: later data could show it to be wrong.

Anything that fails the test goes to `rejected_candidates` with exactly one reason:
`no_direction`, `no_horizon`, `reported_fact` (describes a past, already-reported period), or `boilerplate`.

Rules:
- Extract literally. Do not infer one dimension from another ("adding a second shift" is capacity_supply only).
- `span` must be an exact substring of the turn.
- `subject_scope`: own | named_counterparty | anonymous_counterparty | end_market | industry.
  Copy counterparty wording into `counterparty_ref` ("our largest compute customer").
- `horizon_ref`: fiscal_quarter | calendar | relative | unspecified. Do NOT convert dates.
- `hedge`: 0 plain assertion, 1 qualified ("we expect"), 2 heavily hedged ("could see some softness"). Keep hedged claims.
- Keep denials (`is_denial: true`, e.g. "we're not seeing double-ordering") and conditional claims (`condition`).
- Do not report confidence.

## Examples (to fill from dev set: denial, heavy hedge, fiscal-quarter reference, evasion)

<!-- TODO: 4–5 worked examples from the dev gold set -->
