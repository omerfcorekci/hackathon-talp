"""Two parallel barriers per week, bounded peer exposure and model-owned state."""

import asyncio
from copy import deepcopy

from .io import RunWriter
from .llm import LoggedModel
from .network import Message
from .prompt import build_prompt
from .schema import parse_turn


async def gather_or_cancel(coroutines):
    tasks = [asyncio.create_task(coroutine) for coroutine in coroutines]
    try:
        return await asyncio.gather(*tasks)
    except BaseException:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise


class SimulationEngine:
    def __init__(self, *, personas, network, world, settings, transport):
        self.personas = deepcopy(personas)
        ids = [person.get("id") for person in self.personas]
        if not ids or not all(isinstance(p, str) and p for p in ids) or len(set(ids)) != len(ids):
            raise ValueError("Supply external personas with unique, nonempty string IDs")
        if set(ids) != network.ids or set(ids) != set(world.plan.people):
            raise ValueError("Persona, world and network IDs must match")
        if not all(isinstance(p.get("group"), str) and p["group"] for p in self.personas):
            raise ValueError("Each supplied persona must have a group")
        self.personas.sort(key=lambda p: p["id"])
        self.network = network
        self.world = world
        self.settings = settings
        self.transport = transport

    def _validate(self, raw, persona, previous):
        result = parse_turn(raw, contacts=self.network.contacts(persona),
                            groups=set(self.network.context(persona)["whatsapp_groups"]), previous=previous)
        if any(not self.network.enabled(persona, message["channel"]) for message in result["messages"]):
            raise ValueError("Cannot send through a disabled channel")
        return result

    async def run(self, output, *, persona_source=None, on_week=None):
        writer = RunWriter(output)
        model = LoggedModel(self.transport, writer, self.settings)
        if persona_source is not None:
            writer.copy_personas(persona_source)
        kind = "nodecision" if not self.world.decisions_enabled else (
            "plan" if self.world.surprises_enabled else "plan_nosurprises")
        metadata = {"company": "cobalt", "type": kind, "seed": self.settings.seed,
                    "model": self.settings.model,
                    "decisions": self.world.plan.raw if self.world.decisions_enabled else [],
                    "engine": "two-round", "settings": self.settings.to_dict(),
                    "complete": False, "completed_weeks": 0}
        writer.write("run.json", metadata)
        writer.write("network.json", self.network.raw)
        writer.write("world.json", self.world.config)
        writer.write("announcements.json", self.world.surprises if self.world.surprises_enabled else [])
        writer.write("decision_targets.json", {key: sorted(ids) for key, ids in self.world.plan.targets.items()}
                     if self.world.decisions_enabled else {})
        for filename in ("calls.jsonl", "weekly.jsonl", "messages.jsonl", "exposures.jsonl"):
            (writer.path / filename).touch()
        states = {p["id"]: deepcopy(p.get("initial_state")) for p in self.personas}
        ledgers = {p["id"]: [] for p in self.personas}
        carry = []
        try:
            for week in range(1, self.settings.weeks + 1):
                used = {p["id"]: 0 for p in self.personas}
                first_inbox = self._route(carry, week, 1, used, writer)
                first = await self._round(self.personas, week, 1, states, ledgers, first_inbox, model)
                first_messages = self._messages(first, week, 1, writer)
                second_inbox = self._route(first_messages, week, 2, used, writer)
                recipients = [p for p in self.personas if second_inbox[p["id"]]]
                second = await self._round(recipients, week, 2, states, ledgers, second_inbox, model, first)
                carry = self._messages(second, week, 2, writer)
                # No further routing in this week. Only round-two messages cross the week boundary.
                for person in self.personas:
                    pid = person["id"]
                    final = second.get(pid, first[pid])
                    row = {"persona": pid, "week": week, **final.data, "call": final.call,
                           "round": 2 if pid in second else 1,
                           "round_1_call": first[pid].call,
                           "round_2_call": second[pid].call if pid in second else None,
                           "received_messages": [m.id for m in first_inbox[pid] + second_inbox[pid]]}
                    writer.append("weekly.jsonl", row)
                    states[pid] = deepcopy(final.data)
                    ledgers[pid].append({"week": week, "status": final.data["status"],
                                         "money": final.data["money"], "balance": final.data["balance"],
                                         "actions": final.data["actions"], "call": final.call})
                metadata["completed_weeks"] = week
                writer.write("run.json", metadata)
                writer.write("state.json", {"week": week, "personas": states,
                                             "pending_messages": [m.to_dict() for m in carry]})
                if on_week is not None:
                    on_week(week, len(first), len(second))
            metadata["complete"] = True
            writer.write("run.json", metadata)
        except BaseException as error:
            metadata["failure_type"] = type(error).__name__
            writer.write("run.json", metadata)
            raise
        return metadata

    def _route(self, messages, week, round_number, used, writer):
        inboxes, audit = self.network.route(
            messages, week=week, round_number=round_number, settings=self.settings,
            used=used, allow_message=self.world.allow_peer_message)
        for row in audit:
            writer.append("exposures.jsonl", row)
        return inboxes

    async def _round(self, people, week, round_number, states, ledgers, inboxes, model, first=None):
        async def evaluate(person):
            pid = person["id"]
            previous = first[pid].data if first is not None else None
            prompt = build_prompt(persona=person, week=week, round_number=round_number,
                                  prior_state=states[pid], ledger=ledgers[pid], world=self.world,
                                  network=self.network, inbox=inboxes[pid], first_turn=previous)
            result = await model.turn(persona=pid, week=week, round_number=round_number, prompt=prompt,
                                      validate=lambda raw: self._validate(raw, pid, previous))
            return pid, result

        return dict(await gather_or_cancel([evaluate(person) for person in people]))

    @staticmethod
    def _messages(results, week, round_number, writer):
        messages = []
        for person, result in sorted(results.items()):
            for index, outgoing in enumerate(result.data["messages"]):
                message = Message(id=f"w{week}:r{round_number}:{person}:{index}", author=person,
                                  week=week, round=round_number, call=result.call, **outgoing)
                writer.append("messages.jsonl", message.to_dict())
                messages.append(message)
        return messages
