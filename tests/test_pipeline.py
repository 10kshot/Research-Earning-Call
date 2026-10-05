import unittest

from ccad.fiscal import fiscal_to_calendar_qidx, qidx
from ccad.matching import Cell, flat_mismatches, score_link
from ccad.resolution import Signal, credibility_score, label_claim
from ccad.schema import TurnExtraction

TURN = {
    "transcript_id": "S_FY2024Q3_call",
    "call_date": "2024-10-24",
    "turn_index": 47,
    "segment": "prepared",
    "speaker_role": "CEO",
    "source_text": "Orders from our largest compute customer accelerated through the quarter, "
                   "and we expect that strength to continue into Q4.",
    "run": {"model": "pinned-model-id", "prompt_version": "extract_v1", "temperature": 0},
    "claims": [{
        "span": "we expect that strength to continue into Q4",
        "subject_scope": "anonymous_counterparty",
        "counterparty_ref": "our largest compute customer",
        "dimension": "orders_backlog",
        "direction": 2,
        "horizon_text": "into Q4",
        "horizon_ref": "fiscal_quarter",
        "comparison_basis": "sequential",
        "hedge": 1,
    }],
}


class SchemaTest(unittest.TestCase):
    def test_valid_turn(self):
        self.assertEqual(TurnExtraction.from_dict(TURN).errors(), [])

    def test_span_must_be_verbatim(self):
        bad = dict(TURN, claims=[dict(TURN["claims"][0], span="orders will boom")])
        self.assertIn("span not verbatim", " ".join(TurnExtraction.from_dict(bad).errors()))

    def test_round_trip(self):
        t = TurnExtraction.from_dict(TURN)
        self.assertEqual(TurnExtraction.from_dict(t.to_dict()), t)


class FiscalTest(unittest.TestCase):
    def test_december_fye(self):
        self.assertEqual(fiscal_to_calendar_qidx(2024, 4, 12), qidx(2024, 4))

    def test_january_fye(self):
        # FYR=1: fiscal 2024 ends Jan 2025; FQ3 ends Oct 2024.
        self.assertEqual(fiscal_to_calendar_qidx(2024, 3, 1), qidx(2024, 4))

    def test_september_fye(self):
        # FYR=9: fiscal 2024 Q1 ends Dec 2023.
        self.assertEqual(fiscal_to_calendar_qidx(2024, 1, 9), qidx(2023, 4))


class MatchingTest(unittest.TestCase):
    q = qidx(2024, 4)

    def test_level_contradiction(self):
        s = [Cell("orders_backlog", self.q, 2, 0)]
        c = [Cell("capex_procurement", self.q, -1, 0)]
        (hit,) = score_link(s, c)
        self.assertEqual((hit.kind, hit.lag), ("level", 0))

    def test_agreement_is_not_contradiction(self):
        s = [Cell("orders_backlog", self.q, 1, 0)]
        c = [Cell("capex_procurement", self.q, 2, 0)]
        self.assertEqual(score_link(s, c), [])

    def test_heavy_hedge_excluded(self):
        s = [Cell("orders_backlog", self.q, 2, 2)]
        c = [Cell("capex_procurement", self.q, -1, 0)]
        self.assertEqual(score_link(s, c), [])

    def test_timing_contradiction(self):
        s = [Cell("orders_backlog", self.q, 2, 0)]
        c = [Cell("capex_procurement", self.q, -1, 0), Cell("capex_procurement", self.q + 1, 1, 0)]
        (hit,) = score_link(s, c)
        self.assertEqual(hit.kind, "timing")

    def test_flat_is_not_contradiction_but_is_recorded(self):
        s = [Cell("orders_backlog", self.q, 2, 0)]
        c = [Cell("capex_procurement", self.q, 0, 0)]
        self.assertEqual(score_link(s, c), [])
        (m,) = flat_mismatches(s, c)
        self.assertEqual(m.flat_side, "customer")

    def test_both_flat_is_not_a_mismatch(self):
        s = [Cell("orders_backlog", self.q, 0, 0)]
        c = [Cell("capex_procurement", self.q, 0, 0)]
        self.assertEqual(flat_mismatches(s, c), [])


class ResolutionTest(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(label_claim(2, [Signal("A", 3.0, 1.0)]), ("right", "A"))
        self.assertEqual(label_claim(2, [Signal("A", -3.0, 1.0)]), ("wrong", "A"))
        self.assertEqual(label_claim(1, [Signal("A", 0.5, 1.0)]), ("flat", "A"))
        self.assertEqual(label_claim(1, []), ("unresolved", None))

    def test_best_tier_wins_and_conflict(self):
        self.assertEqual(label_claim(1, [Signal("A", 2.0, 1.0), Signal("B", -2.0, 1.0)]), ("right", "A"))
        self.assertEqual(label_claim(1, [Signal("A", 2.0, 1.0), Signal("A", -2.0, 1.0)]), ("conflicted", "A"))

    def test_late(self):
        sigs = [Signal("A", 0.2, 1.0), Signal("A", 2.0, 1.0, offset=1)]
        self.assertEqual(label_claim(1, sigs), ("late", "A"))

    def test_credibility_shrinks(self):
        self.assertAlmostEqual(credibility_score([], 0.2), 0.2)
        self.assertAlmostEqual(credibility_score(["wrong"] * 10, 0.2), 0.6)



class TranscriptTest(unittest.TestCase):
    def test_parse_fixture(self):
        from pathlib import Path
        from ccad.transcripts import parse_file

        call, turns = parse_file(Path(__file__).parent / "fixtures" / "sample_T.xml")
        self.assertEqual((call["call_date"], call["company_ticker"], call["has_qa"]), ("2016-10-24", "TSC", True))
        by_n = {t["turn_index"]: t for t in turns}
        self.assertEqual([by_n[n]["speaker_role"] for n in range(1, 6)],
                         ["operator", "CEO", "analyst", "CFO", "operator"])
        self.assertEqual(by_n[2]["text"], "Orders from our largest customer accelerated.\nWe expect that strength to continue into Q4.")
        self.assertEqual(by_n[3]["speaker_desc"], "Big Bank & Co. - Analyst")
        self.assertEqual(by_n[4]["question_turn_index"], 3)
        self.assertIsNone(by_n[5]["question_turn_index"])

    def test_n_turns_when_numbering_restarts_per_section(self):
        from pathlib import Path
        from ccad.transcripts import parse_file

        call, turns = parse_file(Path(__file__).parent / "fixtures" / "restart_numbering_T.xml")
        self.assertEqual(call["n_turns"], 5)
        qa = {t["turn_index"]: t for t in turns if t["segment"] == "qa"}
        self.assertEqual(qa[2]["question_turn_index"], 1)


if __name__ == "__main__":
    unittest.main()
