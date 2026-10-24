"""Seeded exposure over an externally supplied graph, with a weekly inbox cap."""

from dataclasses import asdict, dataclass
from copy import deepcopy

from .schema import CHANNELS
from .settings import Settings, draw


@dataclass(frozen=True)
class Message:
    id: str
    author: str
    week: int
    round: int
    channel: str
    target: str | None
    text: str
    call: str

    def to_dict(self):
        return asdict(self)


class Network:
    """No synthetic people, inferred friendships, or generated group memberships."""

    def __init__(self, persona_ids, data=None):
        self.ids = set(persona_ids)
        data = {} if data is None else data
        self.raw = deepcopy(data)
        if not isinstance(data, dict):
            raise ValueError("Network input must be a JSON object")
        unknown = set(data) - {"follows", "close_friends", "groups", "disabled_channels"}
        if unknown:
            raise ValueError(f"Unknown network fields: {sorted(unknown)}")
        self.follows = set()
        self.friends = set()
        for field, output in (("follows", self.follows), ("close_friends", self.friends)):
            links = data.get(field, [])
            if not isinstance(links, list):
                raise ValueError(f"{field} must be a list of pairs")
            for pair in links:
                if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(x, str) for x in pair):
                    raise ValueError(f"{field} must contain [id, id] pairs")
                a, b = pair
                if a not in self.ids or b not in self.ids or a == b:
                    raise ValueError(f"{field} contains unknown or identical persona IDs")
                output.add((a, b))
                if field == "close_friends":
                    output.add((b, a))
        raw_groups = data.get("groups", {})
        if not isinstance(raw_groups, dict):
            raise ValueError("groups must map group IDs to member IDs")
        self.groups = {}
        for name, members in raw_groups.items():
            if not isinstance(name, str) or not name or not isinstance(members, list):
                raise ValueError("Invalid group")
            if not all(isinstance(x, str) and x in self.ids for x in members):
                raise ValueError("Group contains an unknown persona ID")
            if len(members) != len(set(members)):
                raise ValueError("Duplicate group member")
            self.groups[name] = set(members)
        disabled = data.get("disabled_channels", {})
        if not isinstance(disabled, dict):
            raise ValueError("disabled_channels must map persona IDs to channel lists")
        self.disabled = {}
        for person, channels in disabled.items():
            if person not in self.ids or not isinstance(channels, list) or not all(x in CHANNELS for x in channels):
                raise ValueError("Invalid disabled_channels entry")
            self.disabled[person] = set(channels)

    def contacts(self, person):
        result = {author for follower, author in self.follows if follower == person}
        result |= {friend for owner, friend in self.friends if owner == person}
        for members in self.groups.values():
            if person in members:
                result |= members - {person}
        return result

    def context(self, person):
        return {
            "contacts": sorted(self.contacts(person)),
            "whatsapp_groups": sorted(name for name, members in self.groups.items() if person in members),
            "disabled_channels": sorted(self.disabled.get(person, set())),
        }

    def enabled(self, person, channel):
        return channel not in self.disabled.get(person, set())

    def _candidates(self, message):
        if message.channel == "social":
            return self.ids - {message.author}
        if message.channel == "whatsapp":
            return self.groups[message.target] - {message.author}
        return {message.target}

    def _probability(self, message, recipient, settings):
        if not self.enabled(message.author, message.channel) or not self.enabled(recipient, message.channel):
            return 0.0
        if message.channel == "whatsapp":
            return settings.whatsapp_probability
        if message.channel in ("direct", "phone"):
            return 1.0
        if (recipient, message.author) in self.friends:
            return settings.close_friend_probability
        if (recipient, message.author) in self.follows:
            return settings.following_probability
        return settings.stranger_probability

    def route(self, messages, *, week, round_number, settings: Settings, used, allow_message):
        """Return inboxes and audit rows. `used` counts both rounds' peer deliveries."""
        if len({m.id for m in messages}) != len(messages):
            raise ValueError("Duplicate message IDs")
        inboxes = {person: [] for person in sorted(self.ids)}
        candidates = []
        for message in messages:
            for recipient in sorted(self._candidates(message)):
                probability = self._probability(message, recipient, settings)
                roll = draw(settings.seed, "visibility", week, round_number, message.id, recipient)
                priority = draw(settings.seed, "inbox", week, round_number, recipient, message.id)
                candidates.append((recipient, priority, message.id, message, probability, roll))
        audit = []
        for recipient, _, _, message, probability, roll in sorted(candidates):
            reason = "delivered"
            if not allow_message(message, recipient, week):
                reason = "bank_message_quote"
            elif roll >= probability:
                reason = "not_seen"
            elif used.get(recipient, 0) >= settings.max_peer_messages:
                reason = "inbox_limit"
            else:
                inboxes[recipient].append(message)
                used[recipient] = used.get(recipient, 0) + 1
            audit.append({"week": week, "round": round_number, "message": message.id,
                          "author": message.author, "recipient": recipient,
                          "channel": message.channel, "probability": probability,
                          "draw": roll, "result": reason})
        return inboxes, audit
