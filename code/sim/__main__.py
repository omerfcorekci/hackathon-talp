"""Run with PYTHONPATH=code python3 -m sim --help."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .decisions import DecisionPlan, MENU
from .engine import SimulationEngine
from .io import load_json, load_personas
from .llm import VertexTransport
from .network import Network
from .settings import Settings
from .world import World

DEFAULT_WORLD = Path(__file__).resolve().parents[1] / "config" / "world.json"


def parser():
    result = argparse.ArgumentParser(description="Two-round weekly engine; reads externally created personas.")
    result.add_argument("--personas", type=Path, help="External JSONL: id, group, and your own fields")
    result.add_argument("--network", type=Path, help="External follows/friends/groups JSON; omitted = no declared ties")
    result.add_argument("--decisions", type=Path, help="Locked decision list, copied unchanged; omitted = no decisions")
    result.add_argument("--targets", type=Path, help="Explicit decision-N -> persona-ID list for descriptive targets")
    result.add_argument("--action-aliases", type=Path, help="Exact dashboard action name -> engine menu identifier")
    result.add_argument("--surprises", type=Path, help="One JSON file or directory of dashboard announcements")
    result.add_argument("--world", type=Path, default=DEFAULT_WORLD)
    result.add_argument("--no-surprises", action="store_true")
    result.add_argument("--probe", action="store_true",
                        help="Ask the eight check-in questions before week 1 and after the last week "
                             "(official runs plan_1 and nodecision_1 only)")
    result.add_argument("--out", type=Path, help="New empty output directory, e.g. experiments/network-a")
    result.add_argument("--settings", type=Path, help="JSON object of Settings overrides")
    result.add_argument("--seed", type=int)
    result.add_argument("--weeks", type=int)
    result.add_argument("--concurrency", type=int)
    result.add_argument("--model")
    result.add_argument("--validate-only", action="store_true", help="Check inputs without API calls or outputs")
    result.add_argument("--show-plan", action="store_true", help="Print how the engine read the decisions, then exit")
    result.add_argument("--print-menu", action="store_true", help="Print supported action/level identifiers and exit")
    return result


def read_surprises(path):
    if path is None:
        return []
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    events = []
    for file in files:
        data = load_json(file)
        events.extend(data if isinstance(data, list) else [data])
    return events


async def execute(args):
    settings_data = load_json(args.settings) if args.settings else {}
    if not isinstance(settings_data, dict):
        raise ValueError("Settings file must be an object")
    for name in ("seed", "weeks", "concurrency", "model"):
        if getattr(args, name) is not None:
            settings_data[name] = getattr(args, name)
    settings = Settings(**settings_data)
    people = load_personas(args.personas)
    network = Network([p["id"] for p in people], load_json(args.network) if args.network else {})
    decisions = load_json(args.decisions) if args.decisions else []
    plan = DecisionPlan(decisions, people,
                        targets=load_json(args.targets) if args.targets else {},
                        action_aliases=load_json(args.action_aliases) if args.action_aliases else {},
                        seed=settings.seed)
    world = World(load_json(args.world), plan, surprises=read_surprises(args.surprises),
                  decisions_enabled=bool(decisions), surprises_enabled=not args.no_surprises,
                  seed=settings.seed)
    # Preflight every information set without consuming a model call or touching source files.
    from .prompt import build_prompt

    for week in range(1, settings.weeks + 1):
        for person in people:
            build_prompt(persona=person, week=week, round_number=1,
                         prior_state=person.get("initial_state"), ledger=[], world=world,
                         network=network, inbox=[])
    if args.probe:
        from .probe import build_probe_prompt, require_profiles

        require_profiles(people)
        for person in people:
            build_probe_prompt(person, "start", world=world)
    if args.show_plan:
        print(plan.describe() if decisions else "No decisions supplied (business as usual).")
        return
    if args.validate_only:
        print(f"Inputs valid: {len(people)} external personas, {settings.weeks} weeks, "
              f"{len(decisions)} decisions, ${plan.total_cost:,} menu cost"
              f"{', check-in probe on' if args.probe else ''}. No model calls made.")
        return
    if args.out.exists() and any(args.out.iterdir()):
        raise ValueError("Output directory must be empty")
    transport = VertexTransport(timeout_seconds=settings.timeout_seconds)
    try:
        engine = SimulationEngine(personas=people, network=network, world=world,
                                  settings=settings, transport=transport)
        await engine.run(args.out, persona_source=args.personas, probe=args.probe,
                         on_week=lambda week, first, second: print(
                             f"Week {week}: {first} first-round, {second} second-round calls", file=sys.stderr))
        print(f"Engine run complete: {args.out}")
    finally:
        await transport.close()


def main():
    command = parser()
    args = command.parse_args()
    if args.print_menu:
        print(json.dumps({action: list(levels) for action, levels in MENU.items()}, indent=2))
        return 0
    if args.personas is None or (not args.validate_only and not args.show_plan and args.out is None):
        command.error("--personas is required; --out is required unless --validate-only is set")
    try:
        asyncio.run(execute(args))
    except (ValueError, TypeError, OSError, RuntimeError, ImportError) as error:
        # Avoid printing raw SDK exceptions, which may contain credentials.
        if isinstance(error, ImportError):
            print("Install code/requirements.txt before using the Vertex transport.", file=sys.stderr)
        else:
            print(f"Engine stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
