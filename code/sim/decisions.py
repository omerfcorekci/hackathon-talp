"""Menu mechanics only: no policy selection or generated decision messages."""

import re
import math
import unicodedata
from dataclasses import dataclass


def normalize(text):
    text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), text)
    text = text.replace("\\n", " ").replace("\\t", " ").replace('\\"', '"')
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"',
                                        "–": "-", "—": "-", "…": "..."}))
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


@dataclass(frozen=True)
class Action:
    cost: int
    duration: int | None
    effect: dict


# These are input identifiers, not replacements for the dashboard's locked text.
MENU = {
    "savings_rate_boost": {
        "+0.25 points": Action(800_000, 4, {"rate_boost_points": 0.25, "balance_cap": 50_000}),
        "+0.5 points": Action(1_600_000, 4, {"rate_boost_points": 0.5, "balance_cap": 50_000}),
        "+0.75 points": Action(2_400_000, 4, {"rate_boost_points": 0.75, "balance_cap": 50_000}),
    },
    "savings_rate_boost_new_money": {
        "+0.25 points": Action(400_000, 4, {"rate_boost_points": 0.25, "balance_cap": 50_000, "new_money_only": True}),
        "+0.5 points": Action(800_000, 4, {"rate_boost_points": 0.5, "balance_cap": 50_000, "new_money_only": True}),
        "+0.75 points": Action(1_200_000, 4, {"rate_boost_points": 0.75, "balance_cap": 50_000, "new_money_only": True}),
    },
    "instant_dispute_credit": {"on": Action(400_000, 8, {"instant_dispute_credit_cap": 100})},
    "free_instant_transfers": {
        "2 weeks": Action(100_000, 2, {"instant_transfer_fee": 0}),
        "4 weeks": Action(200_000, 4, {"instant_transfer_fee": 0}),
    },
    "debit_cash_back": {
        "1%": Action(1_200_000, 4, {"cash_back_percent": 1, "cash_back_cap": 5}),
        "2%": Action(2_200_000, 4, {"cash_back_percent": 2, "cash_back_cap": 10}),
    },
    "goodwill_credit": {
        "$5": Action(500_000, 1, {"goodwill_credit": 5, "recipient_cap": 100_000}),
        "$10": Action(1_000_000, 1, {"goodwill_credit": 10, "recipient_cap": 100_000}),
    },
    "early_pay": {"on": Action(500_000, None, {"early_pay_days": 2})},
    "zero_interest_advance": {"on": Action(400_000, 1, {"advance_cap": 500, "recipient_cap": 20_000})},
    "extra_support_staff": {
        "+50": Action(250_000, 4, {"extra_support_staff": 50}),
        "+150": Action(700_000, 4, {"extra_support_staff": 150}),
    },
    "security_pack": {"on": Action(300_000, None, {"free_replacement_card": True, "card_payment_alerts": True})},
    "higher_offline_card_limit": {"on": Action(100_000, None, {"migration_offline_card_limit": 250})},
}


class DecisionPlan:
    def __init__(self, decisions, personas, targets=None, action_aliases=None):
        if not isinstance(decisions, list) or len(decisions) not in (0, 2):
            raise ValueError("Supply either no decisions or exactly two locked decisions")
        self.raw = decisions
        self.people = {p["id"]: p for p in personas}
        self.targets = {}
        self.actions = {}
        self.total_cost = 0
        targets = {} if targets is None else targets
        aliases = {} if action_aliases is None else action_aliases
        if not isinstance(targets, dict) or not isinstance(aliases, dict):
            raise ValueError("Target and action mappings must be JSON objects")
        valid_keys = {f"decision-{i + 1}" for i in range(len(decisions))}
        if set(targets) - valid_keys:
            raise ValueError("Target mapping has an unknown decision key")
        for index, decision in enumerate(decisions, 1):
            key = f"decision-{index}"
            if not isinstance(decision, dict):
                raise ValueError("Each decision must be an object")
            if type(decision.get("week")) is not int or not 1 <= decision["week"] <= 10:
                raise ValueError("Decision week must be in 1-10")
            message = decision.get("message")
            if not isinstance(message, str) or not message.strip() or len(message) > 600:
                raise ValueError("Decision message must be nonempty and at most 600 characters")
            if not isinstance(decision.get("why"), str) or not decision["why"].strip():
                raise ValueError("Decision why is required")
            target = decision.get("target")
            if not isinstance(target, str) or not target:
                raise ValueError("Decision target is required")
            if key in targets:
                members = targets[key]
                if not isinstance(members, list) or not all(isinstance(p, str) and p in self.people for p in members):
                    raise ValueError("Target mapping contains an unknown persona")
                selected = set(members)
                if len(selected) != len(members):
                    raise ValueError("Target mapping has duplicate persona IDs")
                if target == "everyone" and selected != set(self.people):
                    raise ValueError("An everyone target cannot exclude personas")
            elif target == "everyone":
                selected = set(self.people)
            else:
                selected = {p["id"] for p in personas if p["group"] == target}
                if not selected:
                    raise ValueError(f"{key}: supply an explicit --targets mapping for this target description")
            if not selected:
                raise ValueError(f"{key} does not target any supplied persona")
            self.targets[key] = selected
            channels = decision.get("channels")
            allowed = {"push", "email", "in-app", "sms", "ceo video"}
            if not isinstance(channels, list) or not channels or not all(isinstance(c, str) and c.lower() in allowed for c in channels):
                raise ValueError("Use menu channels: push, email, in-app, SMS, CEO video")
            if len({c.lower() for c in channels}) != len(channels):
                raise ValueError("Decision channels must not contain duplicates")
            self.total_cost += 25_000 * sum(c.lower() == "sms" for c in channels)
            actions = decision.get("actions")
            if not isinstance(actions, list) or not 1 <= len(actions) <= 3:
                raise ValueError("Each decision needs 1-3 menu actions")
            self.actions[key] = []
            seen = set()
            for action in actions:
                if not isinstance(action, dict) or not isinstance(action.get("action"), str):
                    raise ValueError("Invalid action")
                name = aliases.get(action["action"], action["action"])
                level = action.get("level")
                if not isinstance(name, str) or name not in MENU or not isinstance(level, str) or level not in MENU[name]:
                    raise ValueError("Unknown menu action/level; use --action-aliases to map dashboard action names")
                if name in seen:
                    raise ValueError("An action cannot be repeated in one decision")
                seen.add(name)
                spec = MENU[name][level]
                self.total_cost += spec.cost
                if "recipient_cap" in spec.effect:
                    weights = [self.people[p].get("weight_customers") for p in selected]
                    if any(type(w) not in (int, float) or not math.isfinite(w) or w <= 0 for w in weights):
                        raise ValueError("Capped offers require external weight_customers for targeted personas")
                    if sum(weights) > spec.effect["recipient_cap"]:
                        raise ValueError("Targeted population exceeds the menu recipient cap")
                self.actions[key].append((action, spec))
        if self.total_cost > 4_000_000:
            raise ValueError("Both decisions, including SMS sends, must cost at most $4M")

    def for_person(self, person, week):
        messages, effects = [], []
        for index, decision in enumerate(self.raw, 1):
            key = f"decision-{index}"
            if person not in self.targets[key] or week < decision["week"]:
                continue
            messages.append({"id": key, "starts_week": decision["week"],
                             "channels": decision["channels"], "text": decision["message"]})
            for original, spec in self.actions[key]:
                if spec.duration is None or week < decision["week"] + spec.duration:
                    effects.append({"decision": key, "action": original,
                                    "starts_week": decision["week"], "effect": spec.effect})
        return messages, effects

    def guard_prompt(self, text, person, week, *, enabled):
        normalized = normalize(text)
        for index, decision in enumerate(self.raw, 1):
            if normalize(decision["message"]) in normalized:
                if not enabled or week < decision["week"] or person not in self.targets[f"decision-{index}"]:
                    raise ValueError("Prompt would expose a locked message outside its permitted audience/time")

    def allow_peer_message(self, message, recipient, week):
        # Keep the raw model response unchanged; only refuse forwarding quotes.
        words = re.findall(r"\w+", normalize(message.text))
        for decision in self.raw:
            bank_words = re.findall(r"\w+", normalize(decision["message"]))
            size = min(6, len(bank_words))
            phrases = {tuple(bank_words[i:i + size]) for i in range(len(bank_words) - size + 1)}
            if any(tuple(words[i:i + size]) in phrases for i in range(len(words) - size + 1)):
                return False
        return True
