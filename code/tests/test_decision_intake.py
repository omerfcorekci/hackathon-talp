"""Dashboard wording for actions, levels, channels and targets resolves to the engine's menu."""

import unittest

from sim.decisions import DecisionPlan, resolve_action, resolve_channel, resolve_level


def people():
    return [
        {"id": "a", "group": "paycheck customers", "paid_fri_dec11": True, "weight_customers": 60_000, "name": "A"},
        {"id": "b", "group": "paycheck customers", "paid_fri_dec11": False, "weight_customers": 50_000, "name": "B"},
        {"id": "c", "group": "savers with large balances", "paid_fri_dec11": True, "weight_customers": 1_000, "name": "C"},
    ]


def decision(**changes):
    base = {"week": 5, "target": "everyone", "actions": [{"action": "security_pack", "level": "on"}],
            "message": "A message.", "channels": ["push"], "why": "a\nb\nc"}
    base.update(changes)
    return base


class ResolutionTests(unittest.TestCase):
    def test_actions_from_dossier_wording(self):
        cases = {
            "Savings rate boost for 4 weeks, on balances up to $50,000": "savings_rate_boost",
            "The same boost on new money only": "savings_rate_boost_new_money",
            "Instant dispute credit: credit disputed card charges at once": "instant_dispute_credit",
            "Free instant transfers to other banks (normally 1.5%, up to $15)": "free_instant_transfers",
            "Debit card cash back for 4 weeks": "debit_cash_back",
            "Goodwill credit to a group you define, up to 100,000 customers": "goodwill_credit",
            "Early pay: show paycheck deposits up to 2 days early": "early_pay",
            "Zero-interest advance up to $500 for a group you define": "zero_interest_advance",
            "Extra support staff for 4 weeks": "extra_support_staff",
            "Security pack: a free new card on request and an alert for every card payment": "security_pack",
            "Higher offline card limit during the migration ($100 → $250 per payment)": "higher_offline_card_limit",
            "early_pay": "early_pay",
        }
        for text, ident in cases.items():
            self.assertEqual(resolve_action(text), ident, text)
        self.assertEqual(resolve_action("Weird label", {"Weird label": "early_pay"}), "early_pay")
        with self.assertRaises(ValueError):
            resolve_action("Lower all fees forever")

    def test_levels_by_number(self):
        self.assertEqual(resolve_level("savings_rate_boost", "+0.25"), "+0.25 points")
        self.assertEqual(resolve_level("savings_rate_boost", "0.5 pt"), "+0.5 points")
        self.assertEqual(resolve_level("goodwill_credit", "$10 each"), "$10")
        self.assertEqual(resolve_level("goodwill_credit", "5"), "$5")
        self.assertEqual(resolve_level("free_instant_transfers", "2w"), "2 weeks")
        self.assertEqual(resolve_level("debit_cash_back", "1 percent, up to $5"), "1%")
        self.assertEqual(resolve_level("extra_support_staff", "150"), "+150")
        for level in ("on", "yes", "", None, "true"):
            self.assertEqual(resolve_level("security_pack", level), "on")
        with self.assertRaises(ValueError):
            resolve_level("savings_rate_boost", "+0.4 points")
        with self.assertRaises(ValueError):
            resolve_level("security_pack", "+2")

    def test_channels(self):
        self.assertEqual([resolve_channel(c) for c in ("Push notification", "E-mail", "In-app message", "Text message", "CEO video")],
                         ["push", "email", "in-app", "sms", "ceo video"])
        with self.assertRaises(ValueError):
            resolve_channel("carrier pigeon")


class TargetTests(unittest.TestCase):
    def test_filter_ids_group_and_everyone(self):
        plan = DecisionPlan([decision(target="paid on Dec 11", target_filter={"paid_fri_dec11": True}),
                             decision(week=7, target="Paycheck Customers")], people(), seed=1)
        self.assertEqual(plan.targets["decision-1"], {"a", "c"})
        self.assertEqual(plan.targets["decision-2"], {"a", "b"})
        plan = DecisionPlan([decision(target="two people", target_ids=["a", "b"]), decision(week=7, target="All customers")],
                            people(), seed=1)
        self.assertEqual(plan.targets["decision-1"], {"a", "b"})
        self.assertEqual(plan.targets["decision-2"], {"a", "b", "c"})
        with self.assertRaisesRegex(ValueError, "target_filter"):
            DecisionPlan([decision(target="nobody knows"), decision(week=7)], people())

    def test_sms_cost_and_describe(self):
        plan = DecisionPlan([decision(channels=["Push notification", "Text message"]),
                             decision(week=7, actions=[{"action": "Goodwill credit to a group you define", "level": "$10 each"}],
                                      target="paycheck customers")], people(), seed=1)
        self.assertEqual(plan.total_cost, 300_000 + 25_000 + 1_000_000)
        text = plan.describe()
        self.assertIn("security_pack @ on", text)
        self.assertIn("goodwill_credit @ $10", text)
        self.assertIn("reach 91%", text)  # 100,000 / 110,000 targeted customers


if __name__ == "__main__":
    unittest.main()
