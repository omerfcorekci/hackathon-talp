"""A dashboard announcement can carry world effects; they vanish together with the text."""

import json
import unittest
from pathlib import Path

from sim.decisions import DecisionPlan
from sim.network import Network
from sim.prompt import build_prompt
from sim.world import World, expand_surprises

ROOT = Path(__file__).resolve().parents[1]
WORLD = json.loads((ROOT / "config/world.json").read_text())
# These tests describe an on-time switch; the real world.json carries the announced overrun.
WORLD["migration"]["overrun_hours"] = 0
WORLD["migration"]["overrun_minutes"] = 0

OVERRUN = {"id": "overrun", "week": 7,
           "text": "Cobalt Bank: the migration took longer than planned and finished eight hours late.",
           "effects": {"migration_overrun_hours": 8,
                       "support_wait_by_week": {"7": 30},
                       "experience": [{"week": 6, "text": "Your Sunday morning payment attempts failed until the evening.",
                                       "if": {"uses_p2p": True}}]}}


def world(surprises, enabled=True):
    people = [{"id": "a", "group": "g", "uses_p2p": True}, {"id": "b", "group": "g", "uses_p2p": False}]
    return World(WORLD, DecisionPlan([], people), surprises=surprises, decisions_enabled=False,
                 surprises_enabled=enabled)


class SurpriseEffectTests(unittest.TestCase):
    def test_overrun_from_surprise_shapes_the_migration_week_even_if_announced_later(self):
        w = world([OVERRUN])
        week6 = " ".join(w.context("a", 6)["experience"])
        week7 = " ".join(w.context("a", 7)["experience"])
        self.assertIn("8 hours later than announced", week6)
        self.assertIn("8 hours late", week7)
        self.assertEqual(w.context("a", 7)["support_wait_minutes"], 30)

    def test_experience_effect_respects_persona_condition(self):
        w = world([OVERRUN])
        self.assertIn("Your Sunday morning payment attempts failed until the evening.", w.context("a", 6)["experience"])
        self.assertNotIn("Your Sunday morning payment attempts failed until the evening.", w.context("b", 6)["experience"])

    def test_surprises_off_removes_effects_with_the_text(self):
        w = world([OVERRUN], enabled=False)
        self.assertIn("on schedule", " ".join(w.context("a", 7)["experience"]))
        self.assertEqual(w.context("a", 7)["support_wait_minutes"], WORLD["support_wait"]["by_week"]["7"])
        self.assertEqual(w.context("a", 7)["announcements_so_far"], [])

    def test_the_announced_end_is_kept_to_the_minute(self):
        world_cfg = json.loads((ROOT / "config/world.json").read_text())
        person = {"id": "a", "group": "g", "migration_weekend": {"type": "autopay", "what": "rent", "amount": 900,
                                                                 "scheduled": "Sunday 08:00", "late_after_hour": 16, "late_fee": 25}}
        w = World(world_cfg, DecisionPlan([], [person]), decisions_enabled=False)
        week6, week7 = " ".join(w.context("a", 6)["experience"]), " ".join(w.context("a", 7)["experience"])
        self.assertIn("until Sunday Dec 13 16:10 Central Time, 4 hours and 10 minutes later than announced", week6)
        self.assertIn("it went through at Sunday 16:10. That was after the payee's cutoff", week6)
        self.assertIn("4 hours and 10 minutes late, at Sunday Dec 13 16:10", week7)

    def test_a_surprise_can_pause_a_persona_s_pay(self):
        payee = {"id": "p", "group": "g", "pay_weeks": [2, 4, 6, 8], "pay_schedule": "every other Friday"}
        other = {**payee, "id": "q"}
        event = {"id": "s", "week": 7, "text": "Cobalt Bank: a shutdown.",
                 "effects": {"pay_paused": [{"from_week": 7, "if": {"id": "p"}, "text": "NO_PAY_THIS_TIME"}]}}
        w = World(WORLD, DecisionPlan([], [payee, other]), surprises=[event], decisions_enabled=False)
        self.assertIn("NO_PAY_THIS_TIME", w.context("p", 8)["experience"])
        self.assertFalse(any("landed in your Cobalt account" in t for t in w.context("p", 8)["experience"]))
        self.assertTrue(any("landed in your Cobalt account" in t for t in w.context("p", 6)["experience"]))  # before
        self.assertTrue(any("landed in your Cobalt account" in t for t in w.context("q", 8)["experience"]))  # not targeted
        off = World(WORLD, DecisionPlan([], [payee, other]), surprises=[event], decisions_enabled=False, surprises_enabled=False)
        self.assertNotIn("NO_PAY_THIS_TIME", off.context("p", 8)["experience"])
        with self.assertRaises(ValueError):
            expand_surprises([{**event, "effects": {"pay_paused": [{"from_week": 7, "text": ""}]}}])

    def test_weekend_transfers_are_queued_not_failed(self):
        person = {"id": "a", "group": "g", "migration_weekend": {"type": "p2p", "what": "the babysitter's pay", "amount": 120,
                                                                 "scheduled": "Saturday 10:00"}}
        week6 = " ".join(World(WORLD, DecisionPlan([], [person]), decisions_enabled=False).context("a", 6)["experience"])
        self.assertIn("The babysitter's pay ($120), sent Saturday 10:00, was queued while the app was read-only and went "
                      "through only after the system came back at Sunday 12:00: 26 hours late.", week6)
        self.assertNotIn("service unavailable", week6)

    def test_no_surprise_means_on_schedule(self):
        self.assertIn("on schedule", " ".join(world([]).context("a", 7)["experience"]))

    def test_effects_are_validated(self):
        bad = {**OVERRUN, "effects": {"migration_overrun_hours": -1}}
        with self.assertRaises(ValueError):
            expand_surprises([bad])
        unknown = {**OVERRUN, "effects": {"rate_cut": 1}}
        with self.assertRaises(ValueError):
            expand_surprises([unknown])

    def test_update_can_carry_effects(self):
        event = {"id": "mig", "week": 6, "text": "Migration is running.",
                 "update": {"week": 7, "text": "It overran.", "effects": {"migration_overrun_hours": 5}}}
        self.assertEqual(world([event]).overrun_hours(), 5)


# Identity keys plus the one weekend commitment each test needs; not authored customer personas.
DECLINED = {"id": "d", "group": "g", "migration_weekend": {"type": "card_purchase", "what": "a $140 ticket", "amount": 140}}
UNDER = {"id": "u", "group": "g", "migration_weekend": {"type": "card_purchase", "what": "a $60 dinner", "amount": 60}}
NEWS = {"id": "news", "week": 3, "text": "Cobalt Bank: an incident is being investigated.",
        "effects": {"experience": [{"week": 3, "text": "EVERYONE_NEWS_LINE"},
                                   {"week": 3, "text": "PERSONAL_HARM_LINE", "if": {"id": "d"}},
                                   {"week": 3, "text": "PERSONAL_GOOD_LINE", "if": {"id": "d"}, "went_wrong": False},
                                   {"week": 4, "text": "FLAGGED_FOR_ALL_LINE", "went_wrong": True}]}}


def history_world(surprises=()):
    return World(WORLD, DecisionPlan([], [DECLINED, UNDER]), surprises=list(surprises), decisions_enabled=False)


class WentWrongHistoryTests(unittest.TestCase):
    def test_a_declined_card_is_remembered_and_a_working_one_is_not(self):
        w = history_world()
        self.assertEqual(w.went_wrong_before("d", 6), [])  # the migration week itself is not history yet
        history = w.went_wrong_before("d", 10)
        self.assertEqual([week for week, _ in history], [6])
        self.assertIn("declined for a $140 ticket", history[0][1])
        self.assertEqual(w.went_wrong_before("u", 10), [])  # an on-time migration is not a grievance

    def test_an_overrun_marks_the_migration_window_for_everyone(self):
        w = World(WORLD, DecisionPlan([], [UNDER]), surprises=[OVERRUN], decisions_enabled=False)
        self.assertTrue(any("8 hours later than announced" in text for _, text in w.went_wrong_before("u", 7)))

    def test_surprise_lines_count_when_personal_or_flagged(self):
        w = history_world([NEWS])
        texts = [text for _, text in w.went_wrong_before("d", 5)]
        self.assertEqual(texts, ["PERSONAL_HARM_LINE", "FLAGGED_FOR_ALL_LINE"])
        self.assertEqual([text for _, text in w.went_wrong_before("u", 5)], ["FLAGGED_FOR_ALL_LINE"])
        # The weekly experience still shows every line, marked or not.
        self.assertIn("EVERYONE_NEWS_LINE", w.context("u", 3)["experience"])
        self.assertIn("PERSONAL_GOOD_LINE", w.context("d", 3)["experience"])

    def test_unless_leaves_out_matching_personas(self):
        event = {"id": "u", "week": 3, "text": "Cobalt Bank: an incident.",
                 "effects": {"experience": [{"week": 3, "text": "NOT_FOR_D", "unless": {"id": "d"}, "went_wrong": False}]}}
        w = history_world([event])
        self.assertIn("NOT_FOR_D", w.context("u", 3)["experience"])
        self.assertNotIn("NOT_FOR_D", w.context("d", 3)["experience"])
        self.assertEqual(w.went_wrong_before("u", 5), [])
        with self.assertRaises(ValueError):
            expand_surprises([{**event, "effects": {"experience": [{"week": 3, "text": "x", "unless": "d"}]}}])

    def test_went_wrong_flag_is_validated(self):
        bad = {**NEWS, "effects": {"experience": [{"week": 3, "text": "x", "went_wrong": "yes"}]}}
        with self.assertRaises(ValueError):
            expand_surprises([bad])

    def test_a_long_support_wait_the_persona_reported_is_remembered(self):
        w = history_world()
        ledger = [{"week": 2, "actions": ["call or chat with support"]},
                  {"week": 6, "actions": ["call or chat with support"]}]
        support = [(week, text) for week, text in w.went_wrong_before("u", 8, ledger) if "support" in text]
        self.assertEqual(len(support), 1)  # week 2 had the usual wait
        self.assertEqual(support[0][0], 6)
        self.assertIn(f"about {WORLD['support_wait']['by_week']['6']} minutes", support[0][1])

    def test_pay_follows_the_persona_to_its_other_bank(self):
        payee = {"id": "p", "group": "g", "pay_weeks": [2, 4, 6, 8], "pay_schedule": "every other Friday"}
        w = World(WORLD, DecisionPlan([], [payee]), decisions_enabled=False)

        def pay(week, ledger):
            return [t for t in w.context("p", week, ledger)["experience"] if "every other Friday" in t]

        row = lambda week, status="main bank", actions=(): {"week": week, "status": status, "actions": list(actions)}
        self.assertIn("landed in your Cobalt account this week", pay(4, [row(1), row(2), row(3)])[0])
        moved = [row(1), row(2, actions=["move direct deposit to another bank"]), row(3)]
        self.assertIn("now goes to your other bank", pay(4, moved)[0])
        self.assertIn("landed in your Cobalt account", pay(2, moved[:1])[0])  # not before the move
        self.assertIn("now goes to your other bank", pay(8, [row(1), row(7, status="left")])[0])

    def test_weekly_prompt_carries_the_history(self):
        w = history_world()
        network = Network(["d", "u"])

        def prompt(week):
            return build_prompt(persona=DECLINED, week=week, round_number=1, prior_state=None, ledger=[],
                                world=w, network=network, inbox=[])

        self.assertIn("=== WHAT WENT WRONG FOR YOU SINCE NOV 2 ===\n", prompt(1))
        self.assertIn("- Nothing has gone wrong for you so far.", prompt(6))
        later = prompt(9)
        self.assertIn("- Week 6 (Mon Dec 7 - Sun Dec 13): Your Cobalt card was declined for a $140 ticket", later)
        self.assertNotIn("Nothing has gone wrong", later)


if __name__ == "__main__":
    unittest.main()
