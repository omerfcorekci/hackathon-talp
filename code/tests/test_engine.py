"""Contract tests with in-memory test doubles, never submission/model run data."""

import asyncio
import copy
import json
import tempfile
import subprocess
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sim.decisions import DecisionPlan
from sim.engine import SimulationEngine
from sim.io import RunWriter, load_personas
from sim.network import Message, Network
from sim.prompt import build_prompt
from sim.schema import parse_turn
from sim.settings import Settings
from sim.world import World

ROOT = Path(__file__).resolve().parents[1]
WORLD = json.loads((ROOT / "config/world.json").read_text())


def people(*ids):
    # Only identity keys for testing the interface, not authored customer personas.
    return [{"id": pid, "group": "test-group"} for pid in ids]


def answer(**changes):
    value = {"status": "main bank", "money": "kept", "new_money": "none", "balance": None,
             "active_in_last_30_days": False, "actions": [], "heard_from": [],
             "app_rating": None, "complaint": "none", "reason": "test response",
             "memory": "test memory", "messages": []}
    value.update(changes)
    return value


def decision_pair():
    return [
        {"week": 2, "target": "a", "actions": [{"action": "early_pay", "level": "on"}],
         "message": "Bank notice alpha: your eligible paycheck can arrive up to two days early.",
         "channels": ["email"], "why": "Test targeting.\nTest time.\nTest delivery."},
        {"week": 3, "target": "everyone", "actions": [{"action": "higher_offline_card_limit", "level": "on"}],
         "message": "Bank notice beta: the migration offline purchase limit increases to $250.",
         "channels": ["push"], "why": "Test mechanics.\nTest limits.\nTest budget."},
    ]


def message(mid="m", author="a", channel="social", target=None, text="A personal experience.", week=1, round=1):
    return Message(mid, author, week, round, channel, target, text, "test-call")


def rows(path, name):
    return [json.loads(line) for line in (Path(path) / name).read_text().splitlines() if line]


def prompt_data(prompt):
    """Recover persona, week, round and the first-turn answer from the rendered prompt text."""
    import re

    data = {"persona": {"id": re.search(r"Your ID in this simulation is (\S+)\.", prompt).group(1)},
            "week": int(re.search(r"=== THIS WEEK: week (\d+) of", prompt).group(1)),
            "round": int(re.search(r"Round (\d+) of this week", prompt).group(1))}
    marker = "Your earlier answer:\n"
    if marker in prompt:
        data["already_taken_this_week"] = json.JSONDecoder().raw_decode(prompt.split(marker, 1)[1])[0]
    return data


class TestTransport:
    """Exists only in the test suite; the CLI always uses VertexTransport."""

    def __init__(self, handler=None, delay=False):
        self.handler = handler or (lambda payload: answer())
        self.requests = []
        self.active = 0
        self.peak = 0
        self.delay = delay

    async def generate(self, **request):
        self.requests.append(request)
        self.active += 1
        self.peak = max(self.peak, self.active)
        try:
            if self.delay:
                await asyncio.sleep(0.005)
            result = self.handler(prompt_data(request["prompt"]))
            if isinstance(result, Exception):
                raise result
            return result if isinstance(result, str) else json.dumps(result)
        finally:
            self.active -= 1


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings()
        self.network = Network(["a", "b", "c", "d"], {
            "follows": [["b", "a"], ["c", "a"]], "close_friends": [["a", "c"]],
            "groups": {"g": ["a", "b"]}})

    def route(self, messages, settings=None, used=None):
        return self.network.route(messages, week=1, round_number=2,
                                  settings=settings or self.settings, used={} if used is None else used,
                                  allow_message=lambda *args: True)

    def test_agreed_rates_and_precedence(self):
        _, audit = self.route([message()])
        rates = {row["recipient"]: row["probability"] for row in audit}
        self.assertEqual(rates, {"b": 0.35, "c": 0.65, "d": 0.05})
        _, audit = self.route([message(channel="whatsapp", target="g")])
        self.assertEqual([(r["recipient"], r["probability"]) for r in audit], [("b", 0.8)])

    def test_private_messages_only_go_to_recipient(self):
        for channel in ("phone", "direct"):
            inbox, audit = self.route([message(channel=channel, target="b")])
            self.assertEqual([r["recipient"] for r in audit], ["b"])
            self.assertEqual(len(inbox["b"]), 1)

    def test_inbox_cap_is_shared_across_rounds(self):
        settings = replace(self.settings, stranger_probability=1, following_probability=1, close_friend_probability=1)
        used = {"b": 1}
        inbox, audit = self.route([message("1"), message("2"), message("3")], settings, used)
        self.assertEqual(len(inbox["b"]), 1)
        self.assertEqual(used["b"], 2)
        self.assertEqual(sum(row["result"] == "inbox_limit" for row in audit if row["recipient"] == "b"), 2)

    def test_draws_do_not_depend_on_message_order(self):
        messages = [message("1"), message("2"), message("3")]
        self.assertEqual(self.route(messages), self.route(list(reversed(messages))))

    def test_seed_changes_visibility(self):
        messages = [message(str(i)) for i in range(20)]
        self.assertNotEqual(self.route(messages)[1], self.route(messages, replace(self.settings, seed=7))[1])

    def test_disabled_channel_and_zero_probability(self):
        self.network = Network(["a", "b"], {"disabled_channels": {"b": ["social"]}})
        inbox, audit = self.route([message()], replace(self.settings, stranger_probability=1))
        self.assertEqual(inbox["b"], [])
        self.assertEqual(audit[0]["probability"], 0)
        self.assertEqual(audit[0]["result"], "not_seen")

    def test_visibility_frequencies_match_rates(self):
        totals = {"b": 0, "c": 0, "d": 0}
        for seed in range(2000):
            _, audit = self.route([message()], replace(self.settings, seed=seed))
            for row in audit:
                totals[row["recipient"]] += row["result"] == "delivered"
        for person, rate in (("b", 0.35), ("c", 0.65), ("d", 0.05)):
            self.assertAlmostEqual(totals[person] / 2000, rate, delta=0.035)

    def test_unknown_network_members_are_rejected(self):
        for data in ({"follows": [["a", "missing"]]}, {"groups": {"g": ["a", "missing"]}},
                     {"close_friends": [["a", "a"]]}, {"disabled_channels": {"missing": []}}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                Network(["a", "b"], data)


class WorldTests(unittest.TestCase):
    def setUp(self):
        self.people = people("a", "b")
        self.plan = DecisionPlan(decision_pair(), self.people, targets={"decision-1": ["a"]})
        self.network = Network(["a", "b"])

    def build(self, world, person, week):
        return build_prompt(persona=self.people[0 if person == "a" else 1], week=week, round_number=1,
                            prior_state=None, ledger=[], world=world, network=self.network, inbox=[])

    def test_official_delivery_obeys_target_and_week(self):
        world = World(WORLD, self.plan)
        text = self.plan.raw[0]["message"]
        self.assertNotIn(text, self.build(world, "a", 1))
        self.assertIn(text, self.build(world, "a", 2))
        self.assertNotIn(text, self.build(world, "b", 2))
        self.assertIn(text, self.build(world, "a", 10))

    def test_no_decisions_keeps_bau_and_known_crisis(self):
        world = World(WORLD, self.plan, decisions_enabled=False)
        for person in ("a", "b"):
            prompt = self.build(world, person, 6)
            for decision in self.plan.raw:
                self.assertNotIn(decision["message"], prompt)
            self.assertIn("bau-migration-email", prompt)
            self.assertIn("migration-window", prompt)
            self.assertNotIn("early_pay_days", prompt)

    def test_history_shows_stretches_of_status_not_a_column_of_weeks(self):
        world = World(WORLD, self.plan, decisions_enabled=False)
        ledger = [{"week": w, "status": s, "money": m, "balance": None, "actions": ["UNIQUE_ACTION"], "call": "x"}
                  for w, s, m in ((1, "main bank", "kept"), (2, "main bank", "kept"), (3, "second bank", "moved some"))]
        prompt = build_prompt(persona=self.people[0], week=4, round_number=1, prior_state=None, ledger=ledger,
                              world=world, network=self.network, inbox=[])
        self.assertIn("- Weeks 1-2: main bank, money kept.\n- Week 3: second bank, money moved some.", prompt)
        self.assertNotIn("UNIQUE_ACTION", prompt)
        self.assertNotIn("Most weeks little changes", prompt)

    def test_surprise_updates_do_not_arrive_early(self):
        surprise = {"id": "s", "week": 3, "text": "ORIGINAL_UNIQUE_NOTICE",
                    "update": {"week": 4, "text": "UPDATED_UNIQUE_NOTICE"}}
        world = World(WORLD, self.plan, surprises=[surprise])
        self.assertNotIn("ORIGINAL_UNIQUE_NOTICE", self.build(world, "a", 2))
        self.assertIn("ORIGINAL_UNIQUE_NOTICE", self.build(world, "a", 3))
        self.assertNotIn("UPDATED_UNIQUE_NOTICE", self.build(world, "a", 3))
        self.assertIn("UPDATED_UNIQUE_NOTICE", self.build(world, "a", 4))
        off = World(WORLD, self.plan, surprises=[surprise], surprises_enabled=False)
        self.assertNotIn("ORIGINAL_UNIQUE_NOTICE", self.build(off, "a", 6))
        self.assertIn("migration-window", self.build(off, "a", 6))

    def test_action_duration_expires_but_message_remains(self):
        decisions = decision_pair()
        decisions[0]["actions"] = [{"action": "extra_support_staff", "level": "+50"}]
        plan = DecisionPlan(decisions, self.people, targets={"decision-1": ["a"]})
        self.assertTrue(any("extra_support_staff" in x["effect"] for x in plan.for_person("a", 5)[1]))
        self.assertFalse(any("extra_support_staff" in x["effect"] for x in plan.for_person("a", 6)[1]))
        self.assertEqual(plan.for_person("a", 6)[0][0]["text"], decisions[0]["message"])

    def test_private_state_is_not_in_other_prompts(self):
        self.people[1]["private_note"] = "ANOTHER_PERSON_PRIVATE_STATE"
        self.assertNotIn("ANOTHER_PERSON_PRIVATE_STATE", self.build(World(WORLD, self.plan), "a", 1))

    def test_customer_does_not_know_private_migration_schedule_before_notice(self):
        world = World(WORLD, self.plan, decisions_enabled=False)
        self.assertNotIn("December 12", self.build(world, "b", 4))
        self.assertIn("December 12", self.build(world, "b", 5))

    def test_bank_quotes_are_not_forwarded(self):
        quoted = message(text=self.plan.raw[0]["message"])
        self.assertFalse(self.plan.allow_peer_message(quoted, "b", 2))
        partial = message(text="your eligible paycheck can arrive up to two days early")
        self.assertFalse(self.plan.allow_peer_message(partial, "b", 2))
        self.assertTrue(self.plan.allow_peer_message(message(), "b", 2))

    def test_budget_and_recipient_caps(self):
        decisions = decision_pair()
        decisions[0]["actions"] = [{"action": "savings_rate_boost", "level": "+0.75 points"}]
        decisions[1]["actions"] = [{"action": "debit_cash_back", "level": "2%"}]
        with self.assertRaisesRegex(ValueError, "at most"):
            DecisionPlan(decisions, self.people, targets={"decision-1": ["a"]})
        decisions = decision_pair()
        decisions[0]["actions"] = [{"action": "goodwill_credit", "level": "$5"}]
        with self.assertRaisesRegex(ValueError, "weight_customers"):
            DecisionPlan(decisions, self.people, targets={"decision-1": ["a"]})
        # A target larger than the menu cap is served in part: reach = cap / weighted target size.
        weighted = copy.deepcopy(self.people)
        for person in weighted:
            person["weight_customers"] = 100_000
        plan = DecisionPlan(decisions, weighted, targets={"decision-1": ["a", "b"]}, seed=3)
        self.assertAlmostEqual(plan.reach[("decision-1", "goodwill_credit")], 0.5)
        reached = plan.recipients("decision-1", "goodwill_credit")
        self.assertTrue(reached <= {"a", "b"})
        for pid in ("a", "b"):
            got = any("goodwill_credit" in e["effect"] for e in plan.for_person(pid, 2)[1])
            self.assertEqual(got, pid in reached)
        self.assertEqual(reached, DecisionPlan(decisions, weighted, targets={"decision-1": ["a", "b"]}, seed=3)
                         .recipients("decision-1", "goodwill_credit"))

    def test_action_aliases_do_not_rewrite_locked_decisions(self):
        decisions = decision_pair()
        decisions[0]["actions"][0]["action"] = "Exact dashboard action label"
        original = copy.deepcopy(decisions)
        plan = DecisionPlan(decisions, self.people, targets={"decision-1": ["a"]},
                            action_aliases={"Exact dashboard action label": "early_pay"})
        self.assertEqual(plan.raw, original)
        self.assertEqual(plan.total_cost, 600_000)

    def test_sms_cost_and_bad_levels(self):
        decisions = decision_pair()
        for decision in decisions:
            decision["channels"] = ["SMS", "email"]
        self.assertEqual(DecisionPlan(decisions, self.people, targets={"decision-1": ["a"]}).total_cost, 650_000)
        decisions[0]["actions"][0]["level"] = "not a menu level"
        with self.assertRaises(ValueError):
            DecisionPlan(decisions, self.people, targets={"decision-1": ["a"]})


class SchemaTests(unittest.TestCase):
    def parse(self, value, previous=None):
        return parse_turn(json.dumps(value), contacts={"b"}, groups={"g"}, previous=previous)

    def test_rejects_fabricated_targets_and_invalid_scores(self):
        cases = [answer(messages=[{"channel": "direct", "target": "missing", "text": "x"}]),
                 answer(messages=[{"channel": "whatsapp", "target": "missing", "text": "x"}]),
                 answer(messages=[{"channel": "social", "target": "b", "text": "x"}]),
                 answer(app_rating=True), answer(app_rating=0), answer(balance=float("inf")),
                 answer(status="unknown"), answer(active_in_last_30_days=1)]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.parse(value)

    def test_a_rating_needs_the_review_action(self):
        review = "post a review (App Store / Google / Trustpilot)"
        allowed = [review, "wait and see"]

        def parse(value, previous=None):
            return parse_turn(json.dumps(value), contacts=set(), groups=set(), previous=previous, allowed_actions=allowed)

        with self.assertRaises(ValueError):
            parse(answer(actions=["wait and see"], app_rating=5))
        self.assertEqual(parse(answer(actions=[review], app_rating=5))["app_rating"], 5)
        self.assertIsNone(parse(answer(actions=[review], app_rating=None))["app_rating"])  # a review elsewhere
        # Round two keeps a round-one rating without repeating the action.
        self.assertEqual(parse(answer(actions=["wait and see"], app_rating=2),
                               previous=answer(actions=[review], app_rating=2))["app_rating"], 2)

    def test_money_moved_out_cannot_come_back_as_kept(self):
        for so_far, ok, refused in (("moved some", ("moved some", "moved most"), ("kept",)),
                                    ("moved most", ("moved most",), ("kept", "moved some")),
                                    (None, ("kept",), ())):
            for money in ok:
                self.assertEqual(parse_turn(json.dumps(answer(money=money)), contacts=set(), groups=set(),
                                            money_so_far=so_far)["money"], money)
            for money in refused:
                with self.assertRaises(ValueError):
                    parse_turn(json.dumps(answer(money=money)), contacts=set(), groups=set(), money_so_far=so_far)

    def test_second_round_cannot_erase_completed_actions(self):
        previous = answer(actions=["called_support"], complaint="bank", app_rating=2)
        for value in (answer(actions=["called_support"], app_rating=2),
                      answer(actions=["called_support"], complaint="bank")):
            with self.assertRaises(ValueError):
                self.parse(value, previous)
        # A rephrased or shortened action list is merged with what was already done, not rejected.
        merged = self.parse(answer(actions=["asked_friend"], complaint="bank", app_rating=2), previous)
        self.assertEqual(merged["actions"], ["called_support", "asked_friend"])
        final = answer(actions=["called_support", "asked_friend"], complaint="cfpb", app_rating=3)
        parsed = self.parse(final, previous)
        # The raw round-two list is preserved next to the merged week record.
        self.assertEqual(parsed.pop("actions_reported"), ["called_support", "asked_friend"])
        self.assertEqual(parsed, final)


class EngineTests(unittest.IsolatedAsyncioTestCase):
    def engine(self, transport, *, settings=None, network=None, personas=None, plan=None):
        personas = people("a", "b", "c") if personas is None else personas
        network = Network([p["id"] for p in personas], network)
        plan = DecisionPlan([], personas) if plan is None else plan
        return SimulationEngine(personas=personas, network=network,
                                world=World(WORLD, plan, decisions_enabled=bool(plan.raw)),
                                settings=settings or Settings(weeks=2, attempts=1), transport=transport)

    async def test_same_week_reaction_then_next_week_carry(self):
        def handler(data):
            person, week, turn = data["persona"]["id"], data["week"], data["round"]
            previous = data.get("already_taken_this_week", answer())
            changes = {"messages": []}
            if week == 1 and turn == 1 and person == "a":
                changes["messages"] = [{"channel": "social", "target": None, "text": "My app experience."}]
            if week == 1 and turn == 2 and person == "b":
                changes.update(status="second bank", actions=["called_support"],
                               messages=[{"channel": "direct", "target": "c", "text": "I called support."}])
            return {**previous, **changes}

        transport = TestTransport(handler, delay=True)
        settings = Settings(weeks=2, attempts=1, stranger_probability=1)
        with tempfile.TemporaryDirectory() as output:
            await self.engine(transport, settings=settings, network={"close_friends": [["b", "c"]]}).run(output)
            calls = rows(output, "calls.jsonl")
            weekly = rows(output, "weekly.jsonl")
            lookup = {row["id"]: row for row in calls}
            beta = next(row for row in weekly if row["persona"] == "b" and row["week"] == 1)
            self.assertEqual(beta["status"], "second bank")
            self.assertEqual(beta["round"], 2)
            self.assertEqual(json.loads(lookup[beta["call"]]["response"])["status"], beta["status"])
            week_one_calls = [row for row in calls if row["week"] == 1]
            self.assertEqual(len(week_one_calls), 5)
            self.assertFalse(any("I called support." in c["prompt"] for c in week_one_calls if c["persona"] == "c"))
            week_two_gamma = next(c for c in calls if c["persona"] == "c" and c["week"] == 2 and c["round"] == 1)
            self.assertIn("I called support.", week_two_gamma["prompt"])
            self.assertTrue(all(c["seed"] == 42 for c in calls))
            self.assertTrue(json.loads((Path(output) / "run.json").read_text())["complete"])

    async def test_no_peer_messages_means_no_second_round(self):
        transport = TestTransport()
        with tempfile.TemporaryDirectory() as output:
            await self.engine(transport).run(output)
            self.assertEqual(len(transport.requests), 6)
            self.assertEqual(len(rows(output, "weekly.jsonl")), 6)
            self.assertTrue(all(row["round"] == 1 for row in rows(output, "weekly.jsonl")))

    async def test_audit_ids_do_not_change_identical_run_prompts(self):
        def handler(data):
            return answer(messages=[{"channel": "social", "target": None, "text": "Some personal news."}]
                          if data["persona"]["id"] == "a" else [])
        settings = Settings(weeks=2, attempts=1, stranger_probability=1)
        left, right = TestTransport(handler), TestTransport(handler, delay=True)
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            await self.engine(left, settings=settings).run(first)
            await self.engine(right, settings=settings).run(second)
            self.assertEqual([r["prompt"] for r in left.requests], [r["prompt"] for r in right.requests])
            self.assertNotEqual(rows(first, "calls.jsonl")[0]["id"], rows(second, "calls.jsonl")[0]["id"])

    async def test_zero_inbox_limit_disables_peer_exposure(self):
        transport = TestTransport(lambda _: answer(messages=[{"channel": "social", "target": None, "text": "News"}]))
        with tempfile.TemporaryDirectory() as output:
            await self.engine(transport, settings=Settings(weeks=1, attempts=1, max_peer_messages=0,
                                                         stranger_probability=1)).run(output)
            self.assertEqual(len(rows(output, "calls.jsonl")), 3)
            self.assertTrue(all(not row["received_messages"] for row in rows(output, "weekly.jsonl")))

    async def test_timeout_aborts_and_cancels_inflight_calls(self):
        transport = TestTransport(delay=True)
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaises(RuntimeError):
                await self.engine(transport, settings=Settings(weeks=1, attempts=1, timeout_seconds=0.001)).run(output)
            self.assertEqual(transport.active, 0)
            self.assertEqual(rows(output, "weekly.jsonl"), [])
            self.assertTrue(any(row["error_type"] == "TimeoutError" for row in rows(output, "calls.jsonl")))

    async def test_left_personas_are_still_called_each_week(self):
        transport = TestTransport(lambda _: answer(status="left", money="moved most"))
        with tempfile.TemporaryDirectory() as output:
            await self.engine(transport).run(output)
            self.assertEqual(len(rows(output, "weekly.jsonl")), 6)

    async def test_parallel_calls_respect_concurrency(self):
        transport = TestTransport(delay=True)
        with tempfile.TemporaryDirectory() as output:
            await self.engine(transport, settings=Settings(weeks=1, attempts=1, concurrency=2)).run(output)
        self.assertEqual(transport.peak, 2)

    async def test_invalid_calls_are_logged_and_abort_without_default_status(self):
        transport = TestTransport(lambda _: "not JSON")
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaises(RuntimeError):
                await self.engine(transport, personas=people("a")).run(output)
            self.assertEqual(rows(output, "weekly.jsonl"), [])
            self.assertEqual(rows(output, "calls.jsonl")[0]["response"], "not JSON")
            self.assertFalse(json.loads((Path(output) / "run.json").read_text())["complete"])

    async def test_retry_attempts_keep_raw_responses_and_use_fallback(self):
        responses = iter(["not JSON", json.dumps(answer())])
        transport = TestTransport(lambda _: next(responses))
        with tempfile.TemporaryDirectory() as output, patch("sim.llm.asyncio.sleep", new_callable=AsyncMock):
            await self.engine(transport, personas=people("a"), settings=Settings(weeks=1, attempts=2)).run(output)
            calls = rows(output, "calls.jsonl")
            self.assertEqual([c["valid"] for c in calls], [False, True])
            self.assertEqual(calls[1]["model"], "gemini-3.1-flash-lite")
            self.assertEqual(rows(output, "weekly.jsonl")[0]["call"], calls[1]["id"])

    async def test_transport_error_details_are_not_logged(self):
        transport = TestTransport(lambda _: RuntimeError("sensitive authenticated URL"))
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaises(RuntimeError):
                await self.engine(transport, personas=people("a")).run(output)
            self.assertNotIn("sensitive authenticated URL", (Path(output) / "calls.jsonl").read_text())

    async def test_original_persona_file_is_copied_without_modification(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "external.jsonl"
            original = b'{"id":"a", "group":"external", "custom":{"untouched":true}}\n'
            source.write_bytes(original)
            supplied = load_personas(source)
            before = copy.deepcopy(supplied)
            output = Path(directory) / "output"
            await self.engine(TestTransport(), personas=supplied).run(output, persona_source=source)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual((output / "personas.jsonl").read_bytes(), original)
            self.assertEqual(supplied, before)

    async def test_bank_message_quotation_does_not_trigger_peer_second_round(self):
        supplied = people("a", "b")
        decisions = decision_pair()
        decisions[0]["week"] = 1
        plan = DecisionPlan(decisions, supplied, targets={"decision-1": ["a"]})
        def handler(data):
            return answer(messages=[{"channel": "social", "target": None, "text": decisions[0]["message"]}]
                          if data["persona"]["id"] == "a" else [])
        with tempfile.TemporaryDirectory() as output:
            await self.engine(TestTransport(handler), personas=supplied, plan=plan,
                              settings=Settings(weeks=1, attempts=1, stranger_probability=1)).run(output)
            self.assertEqual(len(rows(output, "calls.jsonl")), 2)
            self.assertEqual(rows(output, "exposures.jsonl")[0]["result"], "bank_message_quote")


class InputTests(unittest.TestCase):
    def test_cli_preflight_needs_no_key_and_writes_no_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.jsonl"
            source.write_text(json.dumps({"id": "external-test-id", "group": "external-test-group"}) + "\n")
            result = subprocess.run([sys.executable, "-m", "sim", "--personas", str(source), "--validate-only"],
                                    cwd=ROOT.parent, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("No model calls made", result.stdout)
            self.assertEqual(list(Path(directory).iterdir()), [source])

    def test_output_directory_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            writer = RunWriter(directory)
            writer.write("run.json", {})
            with self.assertRaises(ValueError):
                RunWriter(directory)

    def test_key_cannot_be_written(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"TALP_KEY": "test-only-secret-marker"}):
            writer = RunWriter(directory)
            with self.assertRaises(ValueError):
                writer.append("calls.jsonl", {"response": "test-only-secret-marker"})
            self.assertFalse((Path(directory) / "calls.jsonl").exists())

    def test_settings_reject_invalid_probabilities(self):
        for value in (-0.1, 1.1, float("nan"), True):
            with self.assertRaises(ValueError):
                Settings(whatsapp_probability=value)


if __name__ == "__main__":
    unittest.main()
