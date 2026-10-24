"""Menu mechanics only: no policy selection or generated decision messages."""

import re
import math
import unicodedata
from dataclasses import dataclass

from .settings import draw


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


# Dashboard wording -> engine identifier. Matching is on normalized text: every keyword group listed
# must appear. Order matters: the first match wins, so the more specific rows come first.
ACTION_KEYWORDS = [
    ("savings_rate_boost_new_money", [["new money"]]),
    ("savings_rate_boost", [["savings"], ["rate"]]),
    ("savings_rate_boost", [["rate boost"]]),
    ("instant_dispute_credit", [["dispute"]]),
    ("free_instant_transfers", [["instant transfer"]]),
    ("free_instant_transfers", [["free"], ["transfer"]]),
    ("debit_cash_back", [["cash back"]]),
    ("debit_cash_back", [["cashback"]]),
    ("goodwill_credit", [["goodwill"]]),
    ("early_pay", [["early pay"]]),
    ("early_pay", [["early"], ["paycheck"]]),
    ("zero_interest_advance", [["advance"]]),
    ("extra_support_staff", [["support"]]),
    ("security_pack", [["security"]]),
    ("security_pack", [["replacement card"]]),
    ("higher_offline_card_limit", [["offline"]]),
    ("higher_offline_card_limit", [["card limit"]]),
]
CHANNEL_KEYWORDS = [("in-app", ["in-app", "in app", "inapp", "app message"]), ("sms", ["sms", "text"]),
                    ("ceo video", ["video", "ceo"]), ("push", ["push"]), ("email", ["email", "e-mail", "mail"])]


def resolve_action(text, aliases=None):
    """Engine action id for a dashboard label: explicit alias, exact id, else keyword match."""
    if aliases and text in aliases:
        return aliases[text]
    if text in MENU:
        return text
    plain = normalize(text).replace("-", " ")
    for ident, groups in ACTION_KEYWORDS:
        if all(any(k in plain for k in group) for group in groups):
            return ident
    raise ValueError(f"Cannot map action {text!r} to the menu; add it to --action-aliases")


def resolve_level(ident, level):
    """Menu level string for a dashboard level: '+0.25', '0.25 pt', '1 percent', '$5 each', '2w', 'yes'…"""
    levels = list(MENU[ident])
    if level in levels:
        return level
    plain = normalize("" if level is None else str(level)).replace("+", "").replace(",", "")
    if levels == ["on"]:
        if plain in ("", "on", "yes", "true", "1", "enabled", "active"):
            return "on"
        raise ValueError(f"Action {ident} has no levels; use \"on\"")
    numbers = re.findall(r"\d+(?:\.\d+)?", plain)
    if not numbers:
        raise ValueError(f"Level {level!r} for {ident} has no number; menu levels are {levels}")
    wanted = float(numbers[0])
    for candidate in levels:
        if float(re.findall(r"\d+(?:\.\d+)?", candidate)[0]) == wanted:
            return candidate
    raise ValueError(f"Level {level!r} is not a menu level for {ident}; use one of {levels}")


def resolve_channel(text):
    plain = normalize(text)
    for ident, keys in CHANNEL_KEYWORDS:
        if any(k in plain for k in keys):
            return ident
    raise ValueError(f"Unknown channel {text!r}; use push, email, in-app, SMS or CEO video")


def select_by_filter(personas, spec):
    """Persona IDs whose attributes equal the given values (a list means any of them)."""
    if not isinstance(spec, dict) or not spec:
        raise ValueError("target_filter must be a nonempty object of attribute -> value(s)")
    chosen = set()
    for p in personas:
        ok = True
        for key, value in spec.items():
            have = p.get(key)
            if isinstance(value, list):
                ok = ok and have in value
            else:
                ok = ok and have == value
        if ok:
            chosen.add(p["id"])
    return chosen


class DecisionPlan:
    def __init__(self, decisions, personas, targets=None, action_aliases=None, seed=0):
        if not isinstance(decisions, list) or len(decisions) not in (0, 2):
            raise ValueError("Supply either no decisions or exactly two locked decisions")
        self.raw = decisions
        self.people = {p["id"]: p for p in personas}
        self.targets = {}
        self.actions = {}
        self.reach = {}  # (decision key, action id) -> share of the target that a capped offer reaches
        self.resolved = {}  # decision key -> [(action id, menu level, cost)] as the engine understood them
        self.channels = {}
        self.seed = seed
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
            why = decision.get("why")  # the dashboard exports why as a list of three lines
            if not (isinstance(why, str) and why.strip()) and not (
                    isinstance(why, list) and why and all(isinstance(x, str) and x.strip() for x in why)):
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
            elif normalize(target) in ("everyone", "all customers", "all", "everybody"):
                selected = set(self.people)
            elif isinstance(decision.get("target_ids"), list):
                selected = set(decision["target_ids"])
                if not selected <= set(self.people):
                    raise ValueError(f"{key}: target_ids contains an unknown persona")
            elif decision.get("target_filter") is not None:
                selected = select_by_filter(personas, decision["target_filter"])
            else:
                groups = {normalize(p["group"]): p["group"] for p in personas}
                selected = {p["id"] for p in personas if normalize(p["group"]) == normalize(target)}
                if not selected:
                    raise ValueError(f"{key}: target {target!r} is not a persona group ({', '.join(groups.values())}); "
                                     "add target_filter / target_ids to the decision or supply --targets")
            if not selected:
                raise ValueError(f"{key} does not target any supplied persona")
            self.targets[key] = selected
            channels = decision.get("channels")
            if not isinstance(channels, list) or not channels or not all(isinstance(c, str) for c in channels):
                raise ValueError("Use menu channels: push, email, in-app, SMS, CEO video")
            resolved_channels = [resolve_channel(c) for c in channels]
            if len(set(resolved_channels)) != len(resolved_channels):
                raise ValueError("Decision channels must not contain duplicates")
            self.channels[key] = resolved_channels
            self.total_cost += 25_000 * resolved_channels.count("sms")
            actions = decision.get("actions")
            if not isinstance(actions, list) or not 1 <= len(actions) <= 3:
                raise ValueError("Each decision needs 1-3 menu actions")
            self.actions[key] = []
            seen = set()
            for action in actions:
                if not isinstance(action, dict) or not isinstance(action.get("action"), str):
                    raise ValueError("Invalid action")
                name = resolve_action(action["action"], aliases)
                level = resolve_level(name, action.get("level"))
                if name in seen:
                    raise ValueError("An action cannot be repeated in one decision")
                seen.add(name)
                spec = MENU[name][level]
                self.total_cost += spec.cost
                if "recipient_cap" in spec.effect:
                    weights = [self.people[p].get("weight_customers") for p in selected]
                    if any(type(w) not in (int, float) or not math.isfinite(w) or w <= 0 for w in weights):
                        raise ValueError("Capped offers require external weight_customers for targeted personas")
                    # The menu caps recipients ("up to 100,000 customers"). A target larger than the cap
                    # is served in part: each persona is drawn as a recipient with probability cap/total,
                    # seeded, so the expected reach matches the cap and plan runs on one seed agree.
                    self.reach[(key, name)] = min(1.0, spec.effect["recipient_cap"] / sum(weights))
                self.actions[key].append((action, spec))
                self.resolved.setdefault(key, []).append((name, level, spec.cost))
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
                if spec.duration is not None and week >= decision["week"] + spec.duration:
                    continue
                name = next(n for n, levels in MENU.items() if spec in levels.values())
                share = self.reach.get((key, name), 1.0)
                if share < 1.0 and draw(self.seed, "reach", key, name, person) >= share:
                    continue  # this persona was not among the capped number of recipients
                effects.append({"decision": key, "action": original,
                                "starts_week": decision["week"], "effect": spec.effect, "reach": share})
        return messages, effects

    def recipients(self, key, name):
        """Persona IDs a capped action actually reaches (all targeted personas when uncapped)."""
        share = self.reach.get((key, name), 1.0)
        return {p for p in self.targets[key] if share >= 1.0 or draw(self.seed, "reach", key, name, p) < share}

    def describe(self):
        """Human-readable preflight: how the engine read each locked decision. Check this before locking."""
        lines = [f"Total cost (incl. SMS sends): ${self.total_cost:,} of $4,000,000"]
        for index, decision in enumerate(self.raw, 1):
            key = f"decision-{index}"
            names = sorted(self.targets[key])
            lines.append(f"\n{key}: week {decision['week']}, target {decision['target']!r} -> {len(names)} personas "
                         f"({', '.join(self.people[p].get('name', p) for p in names)})")
            lines.append(f"  channels: {', '.join(self.channels[key])}   message: {len(decision['message'])} chars")
            for name, level, cost in self.resolved.get(key, []):
                extra = ""
                if (key, name) in self.reach and self.reach[(key, name)] < 1.0:
                    got = sorted(self.recipients(key, name))
                    extra = f"  reach {self.reach[(key, name)]:.0%} -> {', '.join(got) or 'nobody'}"
                lines.append(f"  action: {name} @ {level}  ${cost:,}{extra}")
        return "\n".join(lines)

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
