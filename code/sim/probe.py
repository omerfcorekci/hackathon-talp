"""The organizers' eight check-in questions, asked before week 1 and after the last week.

Each persona answers all eight in one logged call: week 0 for "start", week 11 for "end".
Scores are stored exactly as the model gives them. 2b and 4b are worded the other way round
on purpose and are never flipped here. An invalid answer is rejected and retried under the
engine's attempt policy; no score is ever defaulted.
"""

import json

COMPANY = "Cobalt Bank"
WEEK = {"start": 0, "end": 11}

# Wording from brief/02-challenge.md, "The check-in questions", with the client's name filled in.
QUESTIONS = {
    "1a": f"How much do you trust {COMPANY}? 1 = not at all, 5 = completely.",
    "1b": f"\"I can count on {COMPANY} to treat me right.\" 1 = strongly disagree, 5 = strongly agree.",
    "2a": f"How likely are you to keep using {COMPANY} over the next three months? "
          "1 = very unlikely, 5 = very likely.",
    "2b": f"\"I am thinking about leaving {COMPANY}.\" 1 = strongly disagree, 5 = strongly agree.",
    "3a": f"How likely are you to recommend {COMPANY} to a friend or colleague? "
          "1 = very unlikely, 5 = very likely.",
    "3b": f"If a friend asked you about {COMPANY} today, what would you tell them? "
          "1 = stay away, 5 = go for it.",
    "4a": f"How fairly has {COMPANY} treated you? 1 = very unfairly, 5 = very fairly.",
    "4b": f"\"{COMPANY} takes advantage of people like me.\" 1 = strongly disagree, 5 = strongly agree.",
}
QUESTION_IDS = tuple(QUESTIONS)

PROBE_SCHEMA = {
    "type": "object",
    "properties": {qid: {"type": "integer", "minimum": 1, "maximum": 5} for qid in QUESTION_IDS},
    "required": list(QUESTION_IDS),
    "additionalProperties": False,
}

# One paragraph: no blank line before the JSON payload that follows it.
INSTRUCTIONS = (
    "You are the customer described below. Answer the eight check-in questions as yourself, "
    f"with a whole number 1–5 each; return JSON with keys {','.join(QUESTION_IDS)}. "
    "Read each question as it is worded and answer from your own situation and experience; "
    "use only what is written about you below and do not invent events."
)

MOMENTS = {
    "start": "Now: the start of November, before the ten weeks from Monday November 2 "
             "to Sunday January 10 begin.",
    "end": "Now: the end of the ten weeks that began on Monday November 2 (they end Sunday "
           "January 10). Your own record of those weeks follows.",
}


def require_profiles(personas):
    """The probe shows each persona its own narrative (and voice); the engine never writes one."""
    missing = [p["id"] for p in personas if not isinstance(p.get("narrative"), str) or not p["narrative"].strip()]
    if missing:
        raise ValueError(f"The check-in probe needs each persona's narrative; missing for {', '.join(missing)}")


def build_probe_prompt(person, when, *, world, ledger=(), state=None, include_memory=True):
    """Narrative and voice only, plus (at the end) the persona's own record and what went wrong for it in
    the weeks it lived through. No weights, ties or KPIs."""
    if when not in WEEK:
        raise ValueError("when must be 'start' or 'end'")
    about = {"narrative": person["narrative"]}
    if isinstance(person.get("voice"), str) and person["voice"].strip():
        about["voice"] = person["voice"]
    payload = {"check_in": when, "moment": MOMENTS[when], "about_you": about}
    if when == "end":
        payload["your_weekly_record"] = [
            {"week": row["week"], "status": row["status"], "money": row["money"], "actions": row["actions"]}
            for row in ledger]
        last = max((row["week"] for row in ledger), default=0)
        payload["what_went_wrong_for_you_since_nov_2"] = [
            {"week": week, "what": text} for week, text in world.went_wrong_before(person["id"], last + 1, ledger)]
        if include_memory and isinstance(state, dict):
            payload["your_latest_memory"] = state.get("memory")
            payload["your_latest_reason"] = state.get("reason")
    questions = "\n".join(f"{qid}: {text}" for qid, text in QUESTIONS.items())
    prompt = "\n\n".join([INSTRUCTIONS, json.dumps(payload, ensure_ascii=False, allow_nan=False),
                          "Check-in questions:\n" + questions])
    world.guard_prompt(prompt, person["id"], WEEK[when])
    return prompt


def probe_prompt(person, when, *, world, ledger=(), state=None):
    try:
        return build_probe_prompt(person, when, world=world, ledger=ledger, state=state)
    except ValueError:
        if when != "end":
            raise
        # A persona's own memory may quote a locked message it was not sent; leave memory out.
        return build_probe_prompt(person, when, world=world, ledger=ledger, state=state, include_memory=False)


def parse_probe(raw):
    """Exactly keys 1a..4b, each a JSON whole number 1-5. Rejects; never repairs."""
    def reject_constant(value):
        raise ValueError(f"Non-JSON numeric constant: {value}")

    result = json.loads(raw, parse_constant=reject_constant)
    if not isinstance(result, dict) or set(result) != set(QUESTION_IDS):
        raise ValueError("Check-in answer must contain exactly the keys 1a-4b")
    for qid in QUESTION_IDS:
        score = result[qid]
        if type(score) is not int or not 1 <= score <= 5:
            raise ValueError(f"Check-in score {qid} must be a whole number 1-5")
    return {qid: result[qid] for qid in QUESTION_IDS}


async def run_probe(*, world, when, personas, states, ledgers, model, writer):
    """Ask every persona once (concurrently), then append 8 rows per persona to probe.jsonl."""
    from .engine import gather_or_cancel  # imported here: engine imports this module

    week = WEEK[when]
    # Build every prompt first so a guard failure costs no model call.
    prompts = {p["id"]: probe_prompt(p, when, world=world, ledger=ledgers.get(p["id"], ()),
                                     state=states.get(p["id"]))
               for p in personas}

    async def ask(pid):
        result = await model.turn(persona=pid, week=week, round_number=0, prompt=prompts[pid],
                                  validate=parse_probe, schema=PROBE_SCHEMA)
        return pid, result

    results = dict(await gather_or_cancel([ask(pid) for pid in prompts]))
    for pid in sorted(results):
        result = results[pid]
        for qid in QUESTION_IDS:
            writer.append("probe.jsonl", {"persona": pid, "when": when, "question": qid,
                                          "score": result.data[qid], "call": result.call})
    return {pid: result.data for pid, result in results.items()}
