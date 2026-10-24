"""Deterministic facts, BAU, targeted decisions and time-filtered announcements."""

from copy import deepcopy


def validate_event(event):
    if not isinstance(event, dict) or not isinstance(event.get("id"), str) or not event["id"]:
        raise ValueError("Each world event needs a nonempty id")
    if type(event.get("week")) is not int or not 1 <= event["week"] <= 10:
        raise ValueError("Event week must be in 1-10")
    if not isinstance(event.get("text"), str) or not event["text"].strip():
        raise ValueError("Each event needs text")


def expand_surprises(events):
    if not isinstance(events, list):
        raise ValueError("Surprises must be a list of event objects")
    result = []
    for event in events:
        validate_event(event)
        result.append({k: v for k, v in event.items() if k not in ("update", "updates")})
        updates = list(event.get("updates", []))
        if event.get("update") is not None:
            updates.append(event["update"])
        for number, update in enumerate(updates, 1):
            if not isinstance(update, dict):
                raise ValueError("Surprise update must be an object")
            update = {**update, "id": f"{event['id']}-update-{number}"}
            validate_event(update)
            if update["week"] <= event["week"]:
                raise ValueError("A surprise update must arrive after the original announcement")
            result.append(update)
    ids = [event["id"] for event in result]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate surprise event ID")
    return sorted(result, key=lambda e: (e["week"], e["id"]))


class World:
    def __init__(self, config, plan, *, surprises=(), decisions_enabled=True, surprises_enabled=True):
        self.config = deepcopy(config)
        self.plan = plan
        self.decisions_enabled = decisions_enabled
        self.surprises_enabled = surprises_enabled
        self.surprises = expand_surprises(list(surprises))
        if not isinstance(config, dict) or not isinstance(config.get("baseline"), dict):
            raise ValueError("World configuration requires baseline facts")
        for name in ("known_schedule", "weekly_events", "bau_notices"):
            if not isinstance(config.get(name), list):
                raise ValueError(f"World configuration requires a {name} list")
            for event in config[name]:
                validate_event(event)
        # Avoid BAU accidentally making a no-decision run contain a locked message.
        for notice in config["bau_notices"]:
            plan.guard_prompt(notice["text"], "", notice["week"], enabled=False)

    def context(self, person, week):
        messages, effects = self.plan.for_person(person, week) if self.decisions_enabled else ([], [])
        incidents = [event for event in self.surprises if event["week"] <= week] if self.surprises_enabled else []
        holding = [
            {"id": f"bau-holding-{event['id']}", "week": week, "channel": "social",
             "text": "Cobalt has issued its normal holding statement within 24 hours of this week's incident. "
                     "Only the supplied announcement establishes what is known; no extra remedy is promised."}
            for event in incidents if event["week"] == week
        ]
        return {
            "week": week,
            "baseline": self.config["baseline"],
            "known_schedule": [e for e in self.config["known_schedule"] if e["week"] <= week],
            "events_this_week": [e for e in self.config["weekly_events"] if e["week"] == week],
            "announcements_so_far": incidents,
            "bau_notices_so_far": [e for e in self.config["bau_notices"] if e["week"] <= week] + holding,
            "active_action_effects": effects,
            "official_messages": messages,
        }

    def guard_prompt(self, text, person, week):
        self.plan.guard_prompt(text, person, week, enabled=self.decisions_enabled)

    def allow_peer_message(self, message, recipient, week):
        return self.plan.allow_peer_message(message, recipient, week)
