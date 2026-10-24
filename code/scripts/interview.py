#!/usr/bin/env python3
"""Ask one persona a question live, after a finished run (for the board Q&A).

    python3 code/scripts/interview.py --run runs/plan_1 --persona p07 "Why did you move your money?"
    python3 code/scripts/interview.py --run runs/plan_1 --persona p07            # interactive
    python3 code/scripts/interview.py --run runs/plan_1 --persona p07 --print-prompt "How was December?"
    python3 code/scripts/interview.py --run runs/plan_1 --persona p07 --fake "How was December?"

The persona sees its profile exactly as the engine rendered it (sim.prompt.render_profile, with the
run's network.json), then its own week-by-week record from the run: status, money, what happened to
it (read back from its own weekly prompt in calls.jsonl), what it did, what it said, what it heard,
its memory, and its check-in scores. Nothing from other personas' private state is shown.

The model and seed come from run.json. TALP_KEY is read from the environment (or the repo's .env);
it is never printed. Interviews are NOT added to the run's calls.jsonl; each one is appended to
logs/interviews.jsonl (git-ignored).
"""
import argparse
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE))

from sim.network import Network  # noqa: E402
from sim.prompt import render_profile  # noqa: E402

LOG = ROOT / "logs" / "interviews.jsonl"
CALENDAR = {1: "Nov 2-8", 2: "Nov 9-15", 3: "Nov 16-22", 4: "Nov 23-29", 5: "Nov 30-Dec 6",
            6: "Dec 7-13", 7: "Dec 14-20", 8: "Dec 21-27", 9: "Dec 28-Jan 3", 10: "Jan 4-10"}
STATUS_TEXT = {"main bank": "Cobalt was your main bank", "second bank": "Cobalt was your second bank",
               "dormant": "you had gone quiet on Cobalt (dormant)", "left": "you had left Cobalt"}
EXPERIENCE = re.compile(r"What happened to you this week:\n(.*?)(?:\n\n|\Z)", re.S)


def jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class People:
    """Just enough of sim.world.World for render_profile: names of other personas."""

    def __init__(self, personas):
        self.people = {p["id"]: p for p in personas}

    def person(self, pid):
        return self.people.get(pid, {"id": pid})


def load_run(run: Path, pid: str) -> dict:
    personas = jsonl(run / "personas.jsonl")
    persona = next((p for p in personas if p["id"] == pid), None)
    if persona is None:
        sys.exit(f"persona {pid!r} not in {run / 'personas.jsonl'} (have: {', '.join(p['id'] for p in personas)})")
    meta = json.loads((run / "run.json").read_text(encoding="utf-8"))
    network = None
    if (run / "network.json").is_file():
        try:
            network = Network([p["id"] for p in personas], json.loads((run / "network.json").read_text(encoding="utf-8")))
        except Exception as error:  # an old run with a different network format: profile without contacts
            print(f"(network.json not usable: {error}; profile shown without contacts)", file=sys.stderr)
    weekly = sorted((r for r in jsonl(run / "weekly.jsonl") if r.get("persona") == pid), key=lambda r: r["week"])
    calls = {}
    wanted = {r.get("round_1_call") or r.get("call") for r in weekly}
    for c in jsonl(run / "calls.jsonl"):
        if c.get("id") in wanted:
            calls[c["id"]] = c
    messages = jsonl(run / "messages.jsonl")
    probe = [r for r in jsonl(run / "probe.jsonl") if r.get("persona") == pid]
    return {"meta": meta, "personas": personas, "persona": persona, "network": network, "weekly": weekly,
            "calls": calls, "messages": messages, "probe": probe}


def history(data: dict) -> str:
    pid = data["persona"]["id"]
    names = {p["id"]: p.get("name", p["id"]) for p in data["personas"]}
    by_id = {m["id"]: m for m in data["messages"]}
    sent = {}
    for m in data["messages"]:
        if m.get("author") == pid:
            sent.setdefault(m["week"], []).append(m)
    lines = []
    for r in data["weekly"]:
        w = r["week"]
        out = [f"Week {w} ({CALENDAR.get(w, '')}): {STATUS_TEXT.get(r.get('status'), r.get('status'))}; money since Nov 2: {r.get('money')}"
               + (f"; new money in: {r['new_money']}" if r.get("new_money") not in (None, "none") else "") + "."]
        call = data["calls"].get(r.get("round_1_call") or r.get("call"))
        if call:
            m = EXPERIENCE.search(call.get("prompt") or "")
            if m:
                happened = [x.strip()[2:] for x in m.group(1).splitlines() if x.strip().startswith("- ")]
                if happened:
                    out.append("  What happened to you: " + " ".join(happened))
        acts = r.get("actions") or []
        out.append("  What you did: " + (", ".join(acts) if acts else "nothing in particular") + ".")
        if r.get("complaint") not in (None, "none"):
            out.append(f"  You complained: {'to the CFPB' if r['complaint'] == 'cfpb' else 'to Cobalt'}.")
        if r.get("app_rating") is not None:
            out.append(f"  You rated the app {r['app_rating']}/5 in the App Store.")
        heard = [by_id[i] for i in r.get("received_messages") or [] if i in by_id]
        for m in heard:
            out.append(f'  {names.get(m["author"], m["author"])} told you ({m["channel"]}): "{m["text"]}"')
        for m in sent.get(w, []):
            to = "publicly" if m["channel"] == "social" else f"to {names.get(m.get('target'), m.get('target'))}"
            out.append(f'  You said {to} ({m["channel"]}): "{m["text"]}"')
        if r.get("reason"):
            out.append(f'  Why, in your words: "{r["reason"]}"')
        if r.get("memory"):
            out.append(f'  What you remembered: "{r["memory"]}"')
        lines.append("\n".join(out))
    if not lines:
        lines.append("(no weeks recorded in this run)")
    for when in ("start", "end"):
        scores = {r["question"]: r["score"] for r in data["probe"] if r.get("when") == when}
        if scores:
            label = "before week 1" if when == "start" else "after the last week"
            lines.append(f"Your check-in answers {label} (1-5; 2b and 4b: 5 = strongly agree with the negative "
                         "statement): " + ", ".join(f"{q} {s}" for q, s in sorted(scores.items())) + ".")
    return "\n".join(lines)


def build_prompt(data: dict, question: str, earlier=()) -> str:
    """`earlier`: (question, answer) pairs already asked in this conversation, oldest first."""
    world = People(data["personas"])
    profile = render_profile(data["persona"], world, data["network"])
    last = data["weekly"][-1]["week"] if data["weekly"] else 0
    when = "It is mid-January, after the ten weeks." if last >= 10 else f"It is the end of week {last}."
    return "\n\n".join([
        "You are the Cobalt Bank customer described below. You are a real person, not a bank adviser and not "
        "an assistant. Stay consistent with what you actually did and felt, as recorded in your own history. "
        "Do not invent events that are not in it; if you do not know something, say so the way you would.",
        profile,
        "=== YOUR OWN HISTORY, WEEK BY WEEK ===\n" + history(data),
        *(["=== EARLIER IN THIS CONVERSATION ===\n" + "\n".join(f'Board: "{q}"\nYou: "{a}"' for q, a in earlier)]
          if earlier else []),
        f"=== NOW ===\n{when} Someone from Cobalt Bank's board asks you:\n\"{question}\"\n\n"
        "Answer in the first person, in your own voice, honestly, in 2-5 sentences. Plain text only.",
    ])


def load_key(*roots: Path) -> str | None:
    """TALP_KEY from the environment, else from .env in this checkout or in one of `roots`."""
    if os.environ.get("TALP_KEY"):
        return os.environ["TALP_KEY"]
    for env in [ROOT / ".env", *(Path(r) / ".env" for r in roots)]:
        if not env.is_file():
            continue
        for line in env.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*(?:export\s+)?TALP_KEY\s*=\s*(.*?)\s*$", line)
            if m and m.group(1).strip("'\""):
                return m.group(1).strip("'\"")
    return None


class Asker:
    def __init__(self, model: str, seed, temperature: float, fake: bool, key_roots=()):
        self.model, self.seed, self.temperature, self.fake = model, seed, temperature, fake
        self.client = None
        if not fake:
            key = load_key(*key_roots)
            if not key:
                sys.exit("TALP_KEY is not set (environment or .env). Use --fake or --print-prompt to test.")
            from google import genai
            self.client = genai.Client(vertexai=True, api_key=key)

    def ask(self, prompt: str, persona: dict) -> str:
        if self.fake:
            return (f"[fake answer from {persona.get('name', persona['id'])}] I'd tell you what I told my friends: "
                    "it was a stressful few weeks, but I am still deciding how much I trust Cobalt.")
        config = {"temperature": self.temperature}
        if isinstance(self.seed, int):
            config["seed"] = self.seed
        response = self.client.models.generate_content(model=self.model, contents=prompt, config=config)
        return (response.text or "").strip()


def log(record: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record, ensure_ascii=False)
    key = os.environ.get("TALP_KEY")
    if key and key in text:
        return  # never write the key
    with LOG.open("a", encoding="utf-8") as f:
        f.write(text + "\n")


def interview(a, data, asker, question: str) -> None:
    prompt = build_prompt(data, question)
    if a.print_prompt:
        print(prompt)
        return
    started = time.monotonic()
    try:
        answer = asker.ask(prompt, data["persona"])
        error = None
    except Exception as e:  # SDK messages can carry URLs: log only the type
        answer, error = "", type(e).__name__
    p = data["persona"]
    log({"id": uuid.uuid4().hex, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "run": str(a.run), "persona": p["id"],
         "question": question, "prompt": prompt, "response": answer, "model": "fake:interview" if a.fake else asker.model,
         "seed": asker.seed, "temperature": asker.temperature, "elapsed_seconds": round(time.monotonic() - started, 3),
         "error_type": error})
    if error:
        print(f"(model call failed: {error})", file=sys.stderr)
    else:
        print(f"\n{p.get('name', p['id'])} ({p['id']}, {p.get('group')}):\n{answer}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("question", nargs="?", help="omit for interactive mode")
    ap.add_argument("--run", required=True, type=Path, help="run folder, e.g. runs/plan_1")
    ap.add_argument("--persona", required=True)
    ap.add_argument("--model", help="default: the run's model from run.json")
    ap.add_argument("--seed", type=int, help="default: the run's seed")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--fake", action="store_true", help="canned answer, no network")
    ap.add_argument("--print-prompt", action="store_true", help="print the prompt and exit, no call")
    a = ap.parse_args()
    data = load_run(a.run, a.persona)
    model = a.model or data["meta"].get("model")
    if not a.fake and not a.print_prompt and (not model or str(model).startswith("fake:")):
        sys.exit(f"run.json model is {model!r}; pass --model (e.g. gemini-3.1-flash-lite) or --fake")
    seed = a.seed if a.seed is not None else data["meta"].get("seed")
    asker = None if a.print_prompt else Asker(model, seed, a.temperature, a.fake)
    if a.question:
        interview(a, data, asker, a.question)
        return
    p = data["persona"]
    print(f"Interviewing {p.get('name', p['id'])} ({p['id']}, {p.get('group')}). Empty line or Ctrl-D to stop.")
    while True:
        try:
            q = input("board> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            break
        interview(a, data, asker, q)


if __name__ == "__main__":
    main()
