"""Check-in probe, metrics.json and the five-run driver, with in-memory test doubles only."""

import importlib.util
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sim import metrics
from sim.decisions import DecisionPlan
from sim.engine import SimulationEngine
from sim.network import Network
from sim.probe import PROBE_SCHEMA, QUESTION_IDS, QUESTIONS, build_probe_prompt, parse_probe
from sim.schema import TURN_SCHEMA
from sim.settings import Settings
from sim.world import World

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
WORLD = json.loads((ROOT / "config/world.json").read_text())


def people(*ids):
    # Identity keys, placeholder narrative/voice and weights for interface tests; not authored personas.
    return [{"id": pid, "group": "test-group", "narrative": f"Test narrative {pid}.", "voice": f"Test voice {pid}.",
             "weight_customers": 100, "weight_deposits_usd": 1000, "neighbors": ["zz"], "wave": 7}
            for pid in ids]


def answer(**changes):
    value = {"status": "main bank", "money": "kept", "new_money": "none", "balance": None,
             "active_in_last_30_days": True, "actions": [], "heard_from": [],
             "app_rating": None, "complaint": "none", "reason": "test reason",
             "memory": "test memory", "messages": []}
    value.update(changes)
    return value


def scores(**changes):
    value = {qid: 3 for qid in QUESTION_IDS}
    value.update(changes)
    return value


def rows(path, name):
    return [json.loads(line) for line in (Path(path) / name).read_text().splitlines() if line]


def payload(prompt):
    return json.JSONDecoder().raw_decode(prompt.split("\n\n", 1)[1].lstrip())[0]


class ProbeTransport:
    """Exists only in the test suite; dispatches on the schema the engine sends.

    Weekly handlers get the raw prompt (its layout belongs to prompt.py); probe handlers get the
    parsed check-in payload.
    """

    def __init__(self, weekly=None, probe=None):
        self.weekly = weekly or (lambda prompt: answer())
        self.probe = probe or (lambda data: scores())
        self.requests = []

    async def generate(self, **request):
        self.requests.append(request)
        if request["schema"] is PROBE_SCHEMA:
            result = self.probe(payload(request["prompt"]))
        else:
            result = self.weekly(request["prompt"])
        return result if isinstance(result, str) else json.dumps(result)


def load_checker():
    spec = importlib.util.spec_from_file_location("organizer_check", REPO / "brief/check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProbeUnitTests(unittest.TestCase):
    def test_wording_is_the_brief_with_the_client_name(self):
        self.assertEqual(QUESTION_IDS, ("1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b"))
        self.assertEqual(QUESTIONS["2b"], "\"I am thinking about leaving Cobalt Bank.\" "
                                          "1 = strongly disagree, 5 = strongly agree.")
        self.assertEqual(QUESTIONS["4b"], "\"Cobalt Bank takes advantage of people like me.\" "
                                          "1 = strongly disagree, 5 = strongly agree.")
        self.assertTrue(all("Cobalt Bank" in text and "{company}" not in text for text in QUESTIONS.values()))
        self.assertEqual(PROBE_SCHEMA["required"], list(QUESTION_IDS))
        self.assertFalse(PROBE_SCHEMA["additionalProperties"])

    def test_parse_accepts_whole_numbers_and_rejects_everything_else(self):
        self.assertEqual(parse_probe(json.dumps(scores(**{"2b": 5, "4b": 1}))), scores(**{"2b": 5, "4b": 1}))
        bad = [scores(**{"1a": 0}), scores(**{"1a": 6}), scores(**{"1a": 3.0}), scores(**{"1a": True}),
               scores(**{"1a": "3"}), scores(**{"1a": None}), {**scores(), "extra": 3},
               {k: v for k, v in scores().items() if k != "4b"}, [3] * 8]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_probe(json.dumps(value))
        for raw in ("not JSON", '{"1a": NaN}'):
            with self.assertRaises(ValueError):
                parse_probe(raw)

    def test_prompt_holds_narrative_voice_and_own_record_only(self):
        person = people("a")[0]
        world = World(WORLD, DecisionPlan([], [person]), decisions_enabled=False)
        start = build_probe_prompt(person, "start", world=world)
        for text in ("Test narrative a.", "Test voice a.", *QUESTIONS.values()):
            self.assertIn(text, start)
        for hidden in ("weight_customers", "weight_deposits_usd", "neighbors", "wave", "zz", "baseline",
                       "test memory"):
            self.assertNotIn(hidden, start)
        ledger = [{"week": 1, "status": "second bank", "money": "moved some", "balance": 987654,
                   "actions": ["UNIQUE_ACTION"], "call": "CALL_ID_SECRET"}]
        end = build_probe_prompt(person, "end", world=world, ledger=ledger, state=answer(memory="UNIQUE_MEMORY"))
        data = payload(end)
        self.assertEqual(data["your_record_since_nov_2"], [{"weeks": "1", "status": "second bank", "money": "moved some"}])
        self.assertEqual(data["what_you_did_beyond_routine"], [{"week": 1, "did": ["UNIQUE_ACTION"]}])
        self.assertEqual(data["your_latest_memory"], "UNIQUE_MEMORY")
        self.assertEqual(data["your_latest_reason"], "test reason")
        self.assertEqual(data["what_went_wrong_for_you_since_nov_2"], [])
        # Both check-ins show the same frame; at the start it is empty.
        self.assertEqual(list(payload(start)), list(data))
        self.assertEqual({k: payload(start)[k] for k in ("your_record_since_nov_2", "what_you_did_beyond_routine",
                                                         "what_went_wrong_for_you_since_nov_2", "your_latest_memory")},
                         {"your_record_since_nov_2": [], "what_you_did_beyond_routine": [],
                          "what_went_wrong_for_you_since_nov_2": [], "your_latest_memory": None})
        for hidden in ("987654", "CALL_ID_SECRET", "weight_customers", "baseline"):
            self.assertNotIn(hidden, end)

    def test_end_prompt_lists_what_went_wrong_in_the_weeks_that_ran(self):
        person = {**people("a")[0], "migration_weekend": {"type": "card_purchase", "what": "a $140 ticket", "amount": 140}}
        world = World(WORLD, DecisionPlan([], [person]), decisions_enabled=False)

        def ledger(weeks):
            return [{"week": week, "status": "main bank", "money": "kept", "actions": []} for week in range(1, weeks + 1)]

        full = payload(build_probe_prompt(person, "end", world=world, ledger=ledger(10)))
        self.assertEqual([item["week"] for item in full["what_went_wrong_for_you_since_nov_2"]], [6])
        self.assertIn("declined for a $140 ticket", full["what_went_wrong_for_you_since_nov_2"][0]["what"])
        short = payload(build_probe_prompt(person, "end", world=world, ledger=ledger(2)))
        self.assertEqual(short["what_went_wrong_for_you_since_nov_2"], [])  # a 2-week run never reached week 6


class ProbeEngineTests(unittest.IsolatedAsyncioTestCase):
    def engine(self, transport, *, personas=None, plan=None, settings=None):
        personas = people("a", "b", "c") if personas is None else personas
        plan = DecisionPlan([], personas) if plan is None else plan
        return SimulationEngine(personas=personas, network=Network([p["id"] for p in personas]),
                                world=World(WORLD, plan, decisions_enabled=bool(plan.raw)),
                                settings=settings or Settings(weeks=2, attempts=1), transport=transport)

    async def test_probe_start_and_end_are_logged_and_stored_unflipped(self):
        def probe(data):
            pid = data["about_you"]["narrative"].split()[-1].rstrip(".")
            # Contradictory on purpose: the engine must store what it is given, not "fix" 2b/4b.
            return scores(**{"1a": 1 if data["check_in"] == "start" else 2, "2b": 5, "4b": 5,
                             "3a": {"a": 1, "b": 4, "c": 5}[pid]})

        transport = ProbeTransport(probe=probe)
        with tempfile.TemporaryDirectory() as output:
            await self.engine(transport).run(output, probe=True)
            calls = rows(output, "calls.jsonl")
            probe_rows = rows(output, "probe.jsonl")
            by_id = {c["id"]: c for c in calls}
            self.assertEqual([c["week"] for c in calls], [0] * 3 + [1] * 3 + [2] * 3 + [11] * 3)
            self.assertTrue(all(c["round"] == 0 for c in calls if c["week"] in (0, 11)))
            self.assertEqual(len(probe_rows), 3 * 2 * 8)
            self.assertEqual({tuple(sorted(r)) for r in probe_rows},
                             {("call", "persona", "question", "score", "when")})
            for row in probe_rows:
                call = by_id[row["call"]]
                self.assertEqual(call["persona"], row["persona"])
                self.assertEqual(call["week"], 0 if row["when"] == "start" else 11)
                self.assertEqual(json.loads(call["response"])[row["question"]], row["score"])
            self.assertTrue(all(r["score"] == 5 for r in probe_rows if r["question"] in ("2b", "4b")))
            self.assertEqual({(r["persona"], r["score"]) for r in probe_rows if r["question"] == "3a"},
                             {("a", 1), ("b", 4), ("c", 5)})
            self.assertEqual({(r["when"], r["score"]) for r in probe_rows if r["question"] == "1a"},
                             {("start", 1), ("end", 2)})
            probe_requests = [r for r in transport.requests if r["schema"] is PROBE_SCHEMA]
            self.assertEqual(len(probe_requests), 6)
            self.assertTrue(all("Check-in questions:" in r["prompt"] for r in probe_requests))
            self.assertTrue(all(r["schema"] is TURN_SCHEMA for r in transport.requests if r not in probe_requests))
            end_prompt = next(c["prompt"] for c in calls if c["week"] == 11 and c["persona"] == "a")
            self.assertEqual(payload(end_prompt)["your_record_since_nov_2"], [{"weeks": "1-2", "status": "main bank", "money": "kept"}])
            run = json.loads((Path(output) / "run.json").read_text())
            self.assertTrue(run["complete"])
            self.assertTrue(run["probe"])
            self.assertTrue((Path(output) / "metrics.json").exists())

    async def test_probe_off_leaves_an_empty_file_and_no_probe_calls(self):
        transport = ProbeTransport()
        with tempfile.TemporaryDirectory() as output:
            await self.engine(transport).run(output)
            self.assertEqual((Path(output) / "probe.jsonl").read_text(), "")
            self.assertTrue(all(1 <= c["week"] <= 2 for c in rows(output, "calls.jsonl")))
            self.assertTrue(all(r["schema"] is TURN_SCHEMA for r in transport.requests))
            self.assertEqual(json.loads((Path(output) / "metrics.json").read_text())["weeks_completed"], 2)

    async def test_invalid_probe_answers_retry_then_abort_without_default(self):
        transport = ProbeTransport(probe=lambda data: scores(**{"1a": 6}))
        with tempfile.TemporaryDirectory() as output, patch("sim.llm.asyncio.sleep", new_callable=AsyncMock):
            with self.assertRaises(RuntimeError):
                await self.engine(transport, personas=people("a"), settings=Settings(weeks=1, attempts=2)).run(
                    output, probe=True)
            calls = rows(output, "calls.jsonl")
            self.assertEqual([(c["week"], c["valid"]) for c in calls], [(0, False), (0, False)])
            self.assertEqual(rows(output, "probe.jsonl"), [])
            self.assertEqual(rows(output, "weekly.jsonl"), [])
            run = json.loads((Path(output) / "run.json").read_text())
            self.assertFalse(run["complete"])
            written = json.loads((Path(output) / "metrics.json").read_text())
            self.assertEqual(written["weeks_completed"], 0)

    async def test_probe_retry_uses_the_valid_call(self):
        answers = iter(["not JSON", json.dumps(scores())])
        transport = ProbeTransport(probe=lambda data: next(answers) if data["check_in"] == "start" else scores())
        with tempfile.TemporaryDirectory() as output, patch("sim.llm.asyncio.sleep", new_callable=AsyncMock):
            await self.engine(transport, personas=people("a"), settings=Settings(weeks=1, attempts=2)).run(
                output, probe=True)
            start_calls = [c for c in rows(output, "calls.jsonl") if c["week"] == 0]
            self.assertEqual([c["valid"] for c in start_calls], [False, True])
            self.assertEqual({r["call"] for r in rows(output, "probe.jsonl") if r["when"] == "start"},
                             {start_calls[1]["id"]})

    async def test_probe_needs_narratives_before_any_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "out"
            bare = [{"id": "a", "group": "test-group"}]
            with self.assertRaisesRegex(ValueError, "narrative"):
                await self.engine(ProbeTransport(), personas=bare).run(output, probe=True)
            self.assertFalse(output.exists())

    async def test_end_probe_drops_memory_that_would_leak_a_locked_message(self):
        supplied = people("a", "b")
        decisions = [
            {"week": 1, "target": "a", "actions": [{"action": "early_pay", "level": "on"}],
             "message": "Bank notice alpha: your eligible paycheck can arrive up to two days early.",
             "channels": ["email"], "why": "Test targeting.\nTest time.\nTest delivery."},
            {"week": 1, "target": "everyone", "actions": [{"action": "higher_offline_card_limit", "level": "on"}],
             "message": "Bank notice beta: the migration offline purchase limit increases to $250.",
             "channels": ["push"], "why": "Test mechanics.\nTest limits.\nTest budget."},
        ]
        plan = DecisionPlan(decisions, supplied, targets={"decision-1": ["a"]})
        alpha = decisions[0]["message"]
        transport = ProbeTransport(weekly=lambda prompt: answer(memory=f"I remember: {alpha}"))
        with tempfile.TemporaryDirectory() as output:
            await self.engine(transport, personas=supplied, plan=plan, settings=Settings(weeks=1, attempts=1)).run(
                output, probe=True)
            calls = rows(output, "calls.jsonl")
            end = {c["persona"]: payload(c["prompt"]) for c in calls if c["week"] == 11}
            self.assertIn(alpha, end["a"]["your_latest_memory"])
            self.assertNotIn("your_latest_memory", end["b"])
            self.assertNotIn("your_latest_reason", end["b"])
            self.assertFalse(any(d["message"] in c["prompt"] for c in calls if c["week"] == 0 for d in decisions))
            self.assertEqual(len(rows(output, "probe.jsonl")), 2 * 2 * 8)

    async def test_organizer_checker_accepts_probe_and_metrics(self):
        transport = ProbeTransport()
        personas = people("a", "b", "c")
        with tempfile.TemporaryDirectory() as output:
            await self.engine(transport, personas=personas).run(output, probe=True)
            check = load_checker()
            report = check.Report()
            run = {"run": json.loads((Path(output) / "run.json").read_text()), "personas": personas,
                   "calls": rows(output, "calls.jsonl"), "weekly": rows(output, "weekly.jsonl"),
                   "metrics": json.loads((Path(output) / "metrics.json").read_text()),
                   "probe": rows(output, "probe.jsonl")}
            check.check_run("plan_1", "cobalt", run, report)
            fixes = [line for line in report.lines if line.startswith(" FIX") and
                     ("probe" in line or "metrics" in line or "calls.jsonl" in line)]
            self.assertEqual(fixes, [])
            self.assertTrue(any("check-in questions answered by every persona" in line for line in report.lines))
            self.assertTrue(any("metrics.json has goal_1 to goal_3" in line for line in report.lines))


def week_rows(pid, weeks=range(1, 11), **changes):
    return [{"persona": pid, "week": week, **answer(**changes)} for week in weeks]


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.personas = [
            {"id": "a", "group": "g1", "weight_customers": 100_000, "weight_deposits_usd": 1000},
            {"id": "b", "group": "g1", "weight_customers": 500_000, "weight_deposits_usd": 1000},
            {"id": "c", "group": "g2", "weight_customers": 1_500_000, "weight_deposits_usd": 2000},
        ]

    def scenario(self):
        weekly = week_rows("a") + week_rows("b", range(1, 10)) + week_rows("c", range(1, 10))
        weekly.append({"persona": "b", "week": 10, **answer(status="dormant", money="moved some")})
        weekly.append({"persona": "c", "week": 10, **answer(status="left", money="kept",
                                                            active_in_last_30_days=False)})
        for row in weekly:
            if row["persona"] == "a" and row["week"] == 3:
                row.update(app_rating=1, complaint="bank")
            if row["persona"] == "c" and row["week"] in (5, 6):
                row.update(app_rating=2, complaint="cfpb")
            if row["persona"] == "b" and row["week"] == 1:
                row["complaint"] = "cfpb"
        return weekly

    def test_goals_follow_the_stated_formulas(self):
        result = metrics.compute_metrics(self.personas, self.scenario())
        # No profile fields: every persona has the neutral follow share 0.25.
        self.assertEqual(result["follow_share"], {"a": 0.25, "b": 0.25, "c": 0.25})
        self.assertEqual(result["goal_1"], 76.19)  # (2.1M - 0.25 × 500k - 0.25 × 1.5M) / 2.1M
        self.assertEqual(result["goal_2"], 85.0)   # (4000 - 0.25 × 1000 × 0.4 - 0.25 × 2000) / 4000
        self.assertEqual(result["goal_3"], 4.41)   # c's two ratings count once: (966,000 + 1,000 + 30,000) / 226,000
        self.assertEqual(result["goal_3b"], 15_186.7)  # window 2-5: 120 + c once (1% × 1.5M) + a (1% × 100k / 15)
        self.assertEqual(result["weeks_completed"], 10)
        # Window 1-4: b took a complaint to the CFPB, a complained to Cobalt (1/15 of it reaches the CFPB).
        self.assertEqual(result["series"]["cfpb_extra_by_window"],
                         {"1-4": 5_066.7, "2-5": 15_066.7, "3-6": 15_066.7, "4-7": 15_000.0,
                          "5-8": 15_000.0, "6-9": 15_000.0, "7-10": 0.0})
        self.assertEqual(result["by_group"]["g1"]["goal_1"], 79.17)
        self.assertEqual(result["by_group"]["g1"]["goal_2"], 95.0)
        self.assertEqual(result["by_group"]["g2"]["goal_2"], 75.0)
        self.assertEqual(result["by_group"]["g1"]["goal_3b"], 5_186.7)  # 120 + 1% × 500k + 1% × 100k / 15
        self.assertEqual(result["units"], metrics.UNITS)
        json.dumps(result, allow_nan=False)

    def test_balance_is_ignored(self):
        weekly = [dict(row, balance=0) for row in self.scenario()]
        self.assertEqual(metrics.compute_metrics(self.personas, weekly)["goal_2"], 85.0)

    def test_incomplete_and_empty_runs_still_give_finite_goals(self):
        weekly = [row for row in self.scenario() if row["week"] <= 3]
        result = metrics.compute_metrics(self.personas, weekly)
        self.assertEqual(result["weeks_completed"], 3)
        self.assertEqual(result["goal_1"], 100.0)
        self.assertEqual(list(result["series"]["cfpb_extra_by_window"]), ["1-3"])
        empty = metrics.compute_metrics(self.personas, [])
        self.assertEqual((empty["goal_1"], empty["goal_2"], empty["goal_3"], empty["goal_3b"]), (0.0, 0.0, 4.6, 120.0))
        self.assertTrue(empty["notes"])
        for value in (result, empty):
            self.assertTrue(all(math.isfinite(value[k]) for k in ("goal_1", "goal_2", "goal_3", "goal_3b")))

    def test_quiet_user_counts_until_it_stops_using_the_app(self):
        weekly = [dict(row, status="main bank", active_derived=False) for row in self.scenario()]
        self.assertEqual(metrics.compute_metrics(self.personas, weekly)["goal_1"], 100.0)
        stopped = [dict(row, status="main bank", active_derived=row["week"] < 5) for row in self.scenario()]
        self.assertLess(metrics.compute_metrics(self.personas, stopped)["goal_1"], 100.0)

    def test_zero_baseline_and_missing_weights_are_noted(self):
        weekly = [dict(row, active_in_last_30_days=False) for row in self.scenario()]
        result = metrics.compute_metrics(self.personas, weekly)
        # Never used the app but still a customer = a quiet user: only dormant/left statuses count.
        self.assertEqual(result["goal_1"], 76.19)
        bare = [{"id": p["id"], "group": p["group"]} for p in self.personas]
        result = metrics.compute_metrics(bare, self.scenario())
        self.assertEqual(result["goal_1"], 0.0)
        self.assertTrue(any("B = 0" in note for note in result["notes"]))
        self.assertTrue(any("no valid weight_customers" in note for note in result["notes"]))
        json.dumps(result, allow_nan=False)

    def test_docstring_and_metrics_file_state_the_same_assumptions(self):
        doc = " ".join(metrics.__doc__.split())
        for assumption in metrics.ASSUMPTIONS:
            self.assertIn(" ".join(assumption.split()), doc)
        self.assertEqual(metrics.compute_metrics(self.personas, self.scenario())["assumptions"], metrics.ASSUMPTIONS)

    def test_recompute_cli_rewrites_metrics_from_a_run_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            (run / "personas.jsonl").write_text("".join(json.dumps(p) + "\n" for p in self.personas))
            (run / "weekly.jsonl").write_text("".join(json.dumps(r) + "\n" for r in self.scenario()))
            with redirect_stdout(io.StringIO()) as printed:
                self.assertEqual(metrics.main(["metrics", str(run)]), 0)
            self.assertIn('"goal_2": 85.0', printed.getvalue())
            self.assertEqual(json.loads((run / "metrics.json").read_text())["goal_2"], 85.0)


    def real_personas(self):
        return [json.loads(line) for line in (ROOT / "personas/personas.jsonl").read_text().splitlines() if line.strip()]

    def test_follow_share_maps_the_persona_fields(self):
        self.assertEqual(metrics.follow_share({}), 0.25)
        second = {"cobalt_role": "second bank", "paycheck_into_cobalt": False,
                  "moves_money_for_rate": True, "baseline_anxiety": "high"}
        self.assertEqual(metrics.follow_share(second), 0.44)  # 0.25 + 0.10 + 0.06 + 0.03
        paycheck = {"cobalt_role": "main bank", "paycheck_into_cobalt": True,
                    "moves_money_for_rate": False, "baseline_anxiety": "low"}
        self.assertEqual(metrics.follow_share(paycheck), 0.09)  # 0.25 - 0.10 - 0.03 - 0.03
        for person in self.real_personas():
            self.assertTrue(0.05 <= metrics.follow_share(person) <= 0.5)

    def test_nothing_happens_gives_the_baseline_exactly(self):
        personas = self.real_personas()
        weekly = [row for p in personas for row in week_rows(p["id"])]
        result = metrics.compute_metrics(personas, weekly)
        self.assertEqual((result["goal_1"], result["goal_2"], result["goal_3"], result["goal_3b"]),
                         (100.0, 100.0, 4.6, 120.0))

    def test_one_persona_moving_most_moves_goal_2_by_at_most_five_points(self):
        personas = self.real_personas()
        for person in personas:
            for change in ({"money": "moved most"}, {"status": "left"}):
                weekly = [row for p in personas for row in week_rows(p["id"])]
                for row in weekly:
                    if row["persona"] == person["id"] and row["week"] == 10:
                        row.update(change)
                result = metrics.compute_metrics(personas, weekly)
                self.assertGreaterEqual(result["goal_2"], 95.0, (person["id"], change))
                self.assertGreaterEqual(result["goal_1"], 94.0, (person["id"], change))  # E2 leaving: -5.3

    def test_one_complaint_or_rating_moves_goals_3_and_3b_in_proportion(self):
        personas = self.real_personas()
        for person in personas:
            for change, goal, low, high in (({"complaint": "bank"}, "goal_3b", 120.1, 390.0),
                                            ({"app_rating": 1}, "goal_3", 4.52, 4.6)):
                weekly = [row for p in personas for row in week_rows(p["id"])]
                for row in weekly:
                    if row["persona"] == person["id"] and row["week"] == 6:
                        row.update(change)
                value = metrics.compute_metrics(personas, weekly)[goal]
                self.assertTrue(low <= value <= high, (person["id"], change, value))  # E1 is the extreme

    def test_a_persona_counts_with_its_latest_rating_only(self):
        personas = self.real_personas()
        weekly = [row for p in personas for row in week_rows(p["id"])]
        for row in weekly:
            if row["persona"] == "E1" and row["week"] in (6, 7, 8):
                row["app_rating"] = {6: 1, 7: 1, 8: 5}[row["week"]]
        result = metrics.compute_metrics(personas, weekly)
        self.assertEqual(result["goal_3"], 4.61)  # (966,000 + 4,000 × 5) / 214,000: the week-8 5 replaces the 1s
        self.assertEqual(result["series"]["rated_personas"], 1)

    def test_a_bank_wide_wave_crosses_the_board_lines(self):
        personas = self.real_personas()
        cases = (({"complaint": "bank"}, "goal_3b", lambda v: v > 240),
                 ({"app_rating": 1}, "goal_3", lambda v: v < 4.3))
        for change, goal, crosses in cases:
            weekly = [row for p in personas for row in week_rows(p["id"])]
            for row in weekly:
                if row["week"] == 6:
                    row.update(change)
            value = metrics.compute_metrics(personas, weekly)[goal]
            self.assertTrue(crosses(value), (change, value))

    def test_goal_1_never_exceeds_100(self):
        personas = self.real_personas()
        weekly = [row for p in personas for row in week_rows(p["id"], range(2, 11))]
        weekly += [{"persona": p["id"], "week": 1, **answer(status="dormant", active_in_last_30_days=False)}
                   for p in personas]  # a bad week 1 must not become the baseline
        result = metrics.compute_metrics(personas, weekly)
        self.assertEqual(result["goal_1"], 100.0)
        self.assertTrue(all(value <= 100 for value in result["series"]["goal_1_by_week"].values()))

    def test_new_money_adds_growth_through_the_follow_share(self):
        weekly = [row for pid in "abc" for row in week_rows(pid, new_money="a lot")]
        result = metrics.compute_metrics(self.personas, weekly)
        self.assertEqual(result["goal_2"], 107.5)  # 100 × (4000 + 0.25 × 4000 × 0.3) / 4000


class CliTests(unittest.TestCase):
    def test_validate_only_with_probe_checks_narratives(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.jsonl"
            source.write_text(json.dumps({"id": "external-test-id", "group": "external-test-group"}) + "\n")
            command = [sys.executable, "-m", "sim", "--personas", str(source), "--validate-only", "--probe"]
            result = subprocess.run(command, cwd=REPO / "code", capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("narrative", result.stderr)
            source.write_text(json.dumps(people("external-test-id")[0]) + "\n")
            result = subprocess.run(command, cwd=REPO / "code", capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("check-in probe on", result.stdout)
            self.assertEqual(list(Path(directory).iterdir()), [source])


FAKE_PYTHON = """#!/bin/sh
echo "$@" >> "$(dirname "$0")/../../invocations.log"
out=""; previous=""
for word in "$@"; do [ "$previous" = "--out" ] && out="$word"; previous="$word"; done
[ -n "$out" ] && mkdir -p "$out" && echo done > "$out/run.json"
exit 0
"""


@unittest.skipUnless(shutil.which("bash"), "bash is needed for the driver script")
class RunAllScriptTests(unittest.TestCase):
    """Runs code/scripts/run_all.sh in a throwaway tree whose .venv python is a stub: no model calls."""

    def test_five_runs_get_the_right_seeds_flags_and_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            tree = Path(directory)
            for folder in ("code/scripts", "code/personas", "code/config/decisions", "code/config/surprises", ".venv/bin"):
                (tree / folder).mkdir(parents=True)
            shutil.copy(ROOT / "scripts/run_all.sh", tree / "code/scripts/run_all.sh")
            (tree / "code/scripts/make_submission.sh").write_text("#!/bin/sh\necho \"packaged $1\"\n")
            for name in ("code/personas/personas.jsonl", "code/config/engine.json",
                         "code/config/decisions/plan.json", "code/config/surprises/s.json"):
                (tree / name).write_text("{}\n")
            (tree / ".venv/bin/python").write_text(FAKE_PYTHON)
            for name in ("code/scripts/run_all.sh", "code/scripts/make_submission.sh", ".venv/bin/python"):
                os.chmod(tree / name, 0o755)
            env = {k: v for k, v in os.environ.items() if k != "TALP_KEY"}
            script = ["bash", str(tree / "code/scripts/run_all.sh"), "--weeks", "2"]
            refused = subprocess.run(script, cwd=tree, env=env, capture_output=True, text=True)
            self.assertEqual(refused.returncode, 1)
            self.assertFalse((tree / "invocations.log").exists())
            result = subprocess.run(script, cwd=tree, env={**env, "TALP_KEY": "test-only-placeholder", "TEAM": "42",
                                                           "ALLOW_SHORT_RUNS": "1"},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("packaged 42", result.stdout)
            self.assertNotIn("test-only-placeholder", result.stdout + result.stderr)
            runs = {}
            for line in (tree / "invocations.log").read_text().splitlines():
                words = line.split()
                if "--out" in words:
                    runs[Path(words[words.index("--out") + 1]).name] = words
            self.assertEqual(set(runs), {"plan_1", "plan_2", "nodecision_1", "nodecision_2", "plan_nosurprises"})
            seeds = {name: words[words.index("--seed") + 1] for name, words in runs.items()}
            self.assertEqual(seeds, {"plan_1": "1", "plan_2": "2", "nodecision_1": "1", "nodecision_2": "2",
                                     "plan_nosurprises": "1"})
            self.assertEqual({n for n, w in runs.items() if "--probe" in w}, {"plan_1", "nodecision_1"})
            self.assertEqual({n for n, w in runs.items() if "--decisions" in w}, {"plan_1", "plan_2", "plan_nosurprises"})
            self.assertEqual({n for n, w in runs.items() if "--no-surprises" in w}, {"plan_nosurprises"})
            self.assertTrue(all("--surprises" in w and w[w.index("--weeks") + 1] == "2" for w in runs.values()))
            self.assertTrue(all((tree / "runs" / name / "run.json").exists() for name in runs))


if __name__ == "__main__":
    unittest.main()
