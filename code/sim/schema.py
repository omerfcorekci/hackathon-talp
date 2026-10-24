"""Structured model output. Validation rejects answers; it never repairs behavior."""

import json
import math

STATUSES = ("main bank", "second bank", "dormant", "left")
MONEY = ("kept", "moved some", "moved most")
NEW_MONEY = ("none", "some", "a lot")
HEARD_FROM = ("bank", "friend", "rival", "news", "social media", "none")
CHANNELS = ("social", "whatsapp", "direct", "phone")
# Saying you posted or told people is only real if a message goes out through the simulation.
TALK_ACTIONS = ("post on social media", "tell friends or family")

TURN_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": list(STATUSES)},
        "money": {"type": "string", "enum": list(MONEY)},
        "balance": {"type": ["number", "null"], "minimum": 0,
                    "description": "Current Cobalt balance, or null if no starting balance was provided."},
        "active_in_last_30_days": {"type": "boolean"},
        "actions": {"type": "array", "maxItems": 12, "items": {"type": "string"}},
        "heard_from": {"type": "array", "maxItems": 6,
                       "items": {"type": "string", "enum": list(HEARD_FROM)}},
        "new_money": {"type": "string", "enum": list(NEW_MONEY),
                      "description": "Money you brought INTO Cobalt from elsewhere since Nov 2, cumulative."},
        "app_rating": {"type": ["integer", "null"], "minimum": 1, "maximum": 5},
        "complaint": {"type": "string", "enum": ["none", "bank", "cfpb"]},
        "reason": {"type": "string", "maxLength": 600},
        "memory": {"type": "string", "maxLength": 1200},
        "messages": {
            "type": "array", "maxItems": 2,
            "items": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "enum": list(CHANNELS)},
                    "target": {"type": ["string", "null"],
                               "description": "null for social; group ID for whatsapp; contact ID for direct/phone."},
                    "text": {"type": "string", "minLength": 1, "maxLength": 200},
                },
                "required": ["channel", "target", "text"],
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}
TURN_SCHEMA["required"] = list(TURN_SCHEMA["properties"])


def parse_turn(raw: str, *, contacts: set[str], groups: set[str], previous=None, allowed_actions=None):
    def reject_constant(value):
        raise ValueError(f"Non-JSON numeric constant: {value}")

    result = json.loads(raw, parse_constant=reject_constant)
    if not isinstance(result, dict) or set(result) != set(TURN_SCHEMA["required"]):
        missing = set(TURN_SCHEMA["required"]) - set(result) if isinstance(result, dict) else set()
        extra = set(result) - set(TURN_SCHEMA["required"]) if isinstance(result, dict) else set()
        raise ValueError(f"Response must contain exactly the required turn fields (missing {sorted(missing)}, extra {sorted(extra)})")
    if result["status"] not in STATUSES or result["money"] not in MONEY:
        raise ValueError("Invalid status or money value")
    balance = result["balance"]
    if balance is not None and (type(balance) not in (int, float)
                                or not math.isfinite(balance) or balance < 0):
        raise ValueError("balance must be a nonnegative finite number or null")
    if type(result["active_in_last_30_days"]) is not bool:
        raise ValueError("active_in_last_30_days must be boolean")
    rating = result["app_rating"]
    if rating is not None and (type(rating) is not int or not 1 <= rating <= 5):
        raise ValueError("app_rating must be an integer 1-5 or null")
    if result["complaint"] not in ("none", "bank", "cfpb"):
        raise ValueError("Invalid complaint value")
    for field, limit in (("actions", 12), ("heard_from", 6)):
        value = result[field]
        if not isinstance(value, list) or len(value) > limit or not all(isinstance(x, str) for x in value):
            raise ValueError(f"Invalid {field}")
    if result["new_money"] not in NEW_MONEY:
        raise ValueError(f"new_money must be one of {', '.join(NEW_MONEY)}")
    unknown_sources = [h for h in result["heard_from"] if h not in HEARD_FROM]
    if unknown_sources:
        raise ValueError(f"heard_from must use only: {', '.join(HEARD_FROM)} (got {unknown_sources})")
    if allowed_actions:
        unknown_actions = [a for a in result["actions"] if a not in allowed_actions]
        if unknown_actions:
            raise ValueError(f"actions must use the exact wording from 'What you can do' (not {unknown_actions})")
    if any(a in TALK_ACTIONS for a in result["actions"]) and not result["messages"]:
        raise ValueError("You listed posting or telling people in actions but sent no messages; either include "
                         "what you said in messages or remove that action")
    for field, limit in (("reason", 600), ("memory", 1200)):
        if not isinstance(result[field], str) or len(result[field]) > limit:
            raise ValueError(f"Invalid {field}")
    messages = result["messages"]
    if not isinstance(messages, list) or len(messages) > 2:
        raise ValueError("At most two outgoing messages are allowed per turn")
    for message in messages:
        if not isinstance(message, dict) or set(message) != {"channel", "target", "text"}:
            raise ValueError("Invalid message fields")
        channel, target, text = message["channel"], message["target"], message["text"]
        if channel not in CHANNELS:
            raise ValueError(f"Invalid message channel {channel!r}; use one of {', '.join(CHANNELS)}")
        if not isinstance(text, str) or not 1 <= len(text) <= 200:
            raise ValueError("Each message text must be 1 to 200 characters")
        if channel == "social" and target is not None:
            raise ValueError("Social posts must have a null target")
        if channel == "whatsapp" and (not isinstance(target, str) or target not in groups):
            raise ValueError("WhatsApp messages must target one of your groups")
        if channel in ("phone", "direct") and (not isinstance(target, str) or target not in contacts):
            raise ValueError("Private messages must target one of your contacts")
    if previous is not None:
        # Actions already taken this week stay taken: the week's record is the union of both rounds.
        # The raw round-two list is kept as actions_reported so nothing the model said is lost.
        result["actions_reported"] = list(result["actions"])
        result["actions"] = list(previous["actions"]) + [a for a in result["actions"] if a not in previous["actions"]]
        ranks = {"none": 0, "bank": 1, "cfpb": 2}
        if ranks[result["complaint"]] < ranks[previous["complaint"]]:
            raise ValueError("Round two cannot erase a complaint already filed")
        if previous["app_rating"] is not None and result["app_rating"] is None:
            raise ValueError("Round two cannot erase a review already submitted")
    return result
