"""A dashboard announcement can carry world effects; they vanish together with the text."""

import json
import unittest
from pathlib import Path

from sim.decisions import DecisionPlan
from sim.world import World, expand_surprises

ROOT = Path(__file__).resolve().parents[1]
WORLD = json.loads((ROOT / "config/world.json").read_text())

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


if __name__ == "__main__":
    unittest.main()
