#!/usr/bin/env python3
"""Compare candidate decisions and their timing: many engine runs in parallel, one table.

    # The three candidate plans, two seeds, plus the no-decision baseline:
    python3 code/scripts/sweep.py --name plans --seeds 1,2 --baseline \\
        --decisions code/config/decisions/candidates/a_inform_cheap.json \\
                    code/config/decisions/candidates/b_protect_paycheck.json \\
                    code/config/decisions/candidates/c_defend_deposits.json

    # One plan, decision 1 moved to weeks 4..7:
    python3 code/scripts/sweep.py --name timing_a --seeds 1,2 --vary 1 --weeks 4,5,6,7 \\
        --decisions code/config/decisions/candidates/a_inform_cheap.json

Each variant runs `python3 -m sim ... --out experiments/sweeps/<name>/<variant>_s<seed>/` as its
own subprocess (type plan, no probe; the baseline runs with no --decisions), with the same inputs
as code/scripts/run_all.sh: personas, network, settings, surprises, targets, action aliases. The
variant's decision file is copied to experiments/sweeps/<name>/decisions/<variant>.json. Afterwards
each run's metrics.json is read; the mean (and min-max over seeds) is printed and appended as one
row per variant to docs/experiments.md. experiments/ is git-ignored; runs/ is never touched.

Real runs call the model. --fake passes --fake to the engine (no model calls); --dry-run only
validates every variant (`--validate-only`) and prints the commands. TALP_KEY is read from the
environment or .env and never printed.
"""
import argparse
import asyncio
import copy
import json
import os
import shlex
import sys
import time
from datetime import datetime
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
REPO = CODE.parent
sys.path.insert(0, str(CODE))

from sim.decisions import DecisionPlan  # noqa: E402

GOALS = ("goal_1", "goal_2", "goal_3", "goal_3b")
EXPERIMENTS_MD = REPO / "docs" / "experiments.md"
DEFAULTS = {
    "personas": CODE / "personas" / "personas.jsonl",
    "network": CODE / "personas" / "network.json",
    "settings": CODE / "config" / "engine.json",
    "surprises": CODE / "config" / "surprises",
    "targets": CODE / "config" / "decisions" / "targets.json",
    "aliases": CODE / "config" / "decisions" / "action-aliases.json",
}


def ints(text: str) -> list[int]:
    return [int(x) for x in text.split(",") if x.strip()]


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_dotenv() -> None:
    """Put TALP_KEY (and other .env entries) into the environment, like run_all.sh's `source .env`."""
    env = REPO / ".env"
    if not env.is_file():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.removeprefix("export ").split("=", 1)
        value = value.strip().strip("'\"")
        os.environ.setdefault(key.strip(), value)


def short(decisions: list[dict]) -> str:
    return "; ".join(f"w{d['week']}: " + " + ".join(f"{a['action']} ({a['level']})" for a in d["actions"])
                     for d in decisions) or "none"


def variants(a) -> list[tuple[str, list[dict]]]:
    out = []
    for path in a.decisions:
        decs = load_json(path)
        stem = Path(path).stem
        if a.vary:
            if len(decs) < a.vary:
                sys.exit(f"{path}: has no decision {a.vary} to vary")
            for w in a.weeks:
                v = copy.deepcopy(decs)
                v[a.vary - 1]["week"] = w
                out.append((f"{stem}_d{a.vary}w{w}", v))
        else:
            out.append((stem, decs))
    return out


def base_args(a, seed: int) -> list[str]:
    args = ["--personas", str(a.personas), "--settings", str(a.settings), "--seed", str(seed)]
    if a.network and Path(a.network).is_file():
        args += ["--network", str(a.network)]
    if a.no_surprises:
        args += ["--no-surprises"]
    else:
        args += ["--surprises", str(a.surprises)]
    if a.weeks_run:
        args += ["--weeks", str(a.weeks_run)]
    if a.model:
        args += ["--model", a.model]
    if a.concurrency:
        args += ["--concurrency", str(a.concurrency)]
    return args


def decision_args(a, dec_file: Path) -> list[str]:
    args = ["--decisions", str(dec_file)]
    if a.targets and Path(a.targets).is_file():
        args += ["--targets", str(a.targets)]
    if a.aliases and Path(a.aliases).is_file():
        args += ["--action-aliases", str(a.aliases)]
    return args


async def run_one(cmd: list[str], log: Path, env: dict, sem: asyncio.Semaphore) -> tuple[int, float]:
    async with sem:
        t0 = time.time()
        with open(log, "w", encoding="utf-8") as fh:
            proc = await asyncio.create_subprocess_exec(*cmd, cwd=REPO, env=env, stdout=fh,
                                                        stderr=asyncio.subprocess.STDOUT)
            code = await proc.wait()
        return code, time.time() - t0


async def main(a) -> int:
    t0 = time.time()
    root = REPO / "experiments" / "sweeps" / a.name
    personas = [json.loads(line) for line in Path(a.personas).read_text(encoding="utf-8").splitlines()
                if line.strip()]
    targets = load_json(a.targets) if a.targets and Path(a.targets).is_file() else {}
    aliases = load_json(a.aliases) if a.aliases and Path(a.aliases).is_file() else {}
    venv_py = REPO / ".venv" / "bin" / "python"  # same interpreter choice as run_all.sh
    py = [str(venv_py) if venv_py.is_file() else sys.executable, "-m", "sim"]

    jobs = []  # (variant label, decisions, cost, seed, run dir, command)
    for label, decs in variants(a):
        try:
            cost = DecisionPlan(decs, personas, targets=targets, action_aliases=aliases).total_cost
        except ValueError as error:
            sys.exit(f"{label}: invalid decisions: {error}")
        dec_file = root / "decisions" / f"{label}.json"
        dec_file.parent.mkdir(parents=True, exist_ok=True)
        dec_file.write_text(json.dumps(decs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for s in a.seeds:
            out = root / f"{label}_s{s}"
            jobs.append((label, decs, cost, s, out, py + base_args(a, s) + decision_args(a, dec_file)))
    if a.baseline:
        for s in a.seeds:
            out = root / f"nodecision_s{s}"
            jobs.append(("nodecision", [], 0, s, out, py + base_args(a, s)))

    env = dict(os.environ, PYTHONPATH=str(CODE), PYTHONUNBUFFERED="1")
    if a.dry_run:
        print(f"{len(jobs)} runs (dry run: --validate-only, no outputs) -> {root}")
        bad = 0
        for label, _, cost, s, out, cmd in jobs:
            shown = cmd + (["--fake"] if a.fake else []) + ["--out", str(out.relative_to(REPO))]
            print(f"\n[{label}_s{s}] ${cost / 1e6:.2f}M\n  {shlex.join(shown)}")
            proc = await asyncio.create_subprocess_exec(*cmd, "--validate-only", cwd=REPO, env=env,
                                                        stdout=asyncio.subprocess.PIPE,
                                                        stderr=asyncio.subprocess.STDOUT)
            text = (await proc.communicate())[0].decode().strip()
            bad += proc.returncode != 0
            print(f"  -> {text}")
        return 1 if bad else 0

    if a.fake:
        jobs = [(*j[:5], j[5] + ["--fake"]) for j in jobs]
    else:
        load_dotenv()
        env = dict(os.environ, PYTHONPATH=str(CODE), PYTHONUNBUFFERED="1")
        if not env.get("TALP_KEY"):
            sys.exit("TALP_KEY is empty: export it or put it in .env (never in code). Nothing was run.")
        if not env.get("SSL_CERT_FILE") and Path("/etc/ssl/cert.pem").is_file():
            env["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"

    for *_, out, _ in jobs:
        if out.exists() and any(out.iterdir()):
            sys.exit(f"{out} is not empty; pick another --name (nothing was run)")
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    print(f"{len(jobs)} runs, {a.parallel} at a time{' [FAKE]' if a.fake else ''} -> {root}")
    sem = asyncio.Semaphore(a.parallel)
    results = await asyncio.gather(*(run_one(cmd + ["--out", str(out)], logs / f"{out.name}.log", env, sem)
                                     for *_, out, cmd in jobs))

    table: dict[str, dict] = {}
    failed = 0
    for (label, decs, cost, s, out, _), (code, secs) in zip(jobs, results):
        metrics_file = out / "metrics.json"
        if code != 0 or not metrics_file.is_file():
            failed += 1
            tail = (logs / f"{out.name}.log").read_text(encoding="utf-8").splitlines()[-5:]
            print(f" FAIL  {out.name} (exit {code}, {secs:.0f}s), log {logs / (out.name + '.log')}:")
            print("\n".join("        " + t for t in tail))
            continue
        print(f"  ok   {out.name} ({secs:.0f}s)")
        row = table.setdefault(label, {"decs": decs, "cost": cost, "seeds": [], "m": []})
        row["seeds"].append(s)
        row["m"].append(load_json(metrics_file))

    def cell(ms, g):
        vals = [m[g] for m in ms]
        mean = sum(vals) / len(vals)
        return f"{mean:.2f}" + (f" ({min(vals):.2f}-{max(vals):.2f})" if len(vals) > 1 else "")

    print(f"\n{'variant':<28} " + " ".join(f"{g:>22}" for g in GOALS) + f" {'cost':>8}")
    for label, row in table.items():
        print(f"{label:<28} " + " ".join(f"{cell(row['m'], g):>22}" for g in GOALS) + f" ${row['cost'] / 1e6:.2f}M")

    if table and not a.no_log:
        stamp = datetime.now().strftime("%H:%M")
        model = a.model or "engine default"
        model = f"fake:{model}" if a.fake else model
        surprises = "off" if a.no_surprises else "on"
        weeks = f", {a.weeks_run} weeks" if a.weeks_run else ""
        lines = [f"| {a.name}/{label} ({stamp}) | {short(row['decs'])} | {surprises}{weeks} | "
                 f"{','.join(map(str, row['seeds']))} | {model} | "
                 + " | ".join(cell(row['m'], g) for g in GOALS) + f" | ${row['cost'] / 1e6:.2f}M | |"
                 for label, row in table.items()]
        with open(EXPERIMENTS_MD, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"\nappended {len(lines)} rows to {EXPERIMENTS_MD}")
    print(f"done in {time.time() - t0:.1f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="sweep name (folder under experiments/sweeps/)")
    ap.add_argument("--decisions", nargs="+", required=True, type=Path,
                    help="one or more decision files (2 decisions each)")
    ap.add_argument("--vary", type=int, choices=(1, 2), help="move this decision across --weeks")
    ap.add_argument("--weeks", type=ints, default=[4, 5, 6, 7], help="weeks for --vary (default 4,5,6,7)")
    ap.add_argument("--weeks-run", type=int, help="weeks per run (default: settings file, 10); for quick tests")
    ap.add_argument("--seeds", type=ints, default=[1], help="comma-separated seeds (default 1)")
    ap.add_argument("--baseline", action="store_true", help="also run nodecision for each seed")
    ap.add_argument("--no-surprises", action="store_true", help="run without dashboard surprises")
    ap.add_argument("--parallel", type=int, default=4, help="engine runs at the same time (default 4)")
    ap.add_argument("--concurrency", type=int, help="model calls per run (default: settings file)")
    ap.add_argument("--model", help="model override (default: engine default)")
    ap.add_argument("--fake", action="store_true", help="pass --fake to the engine: no model calls")
    ap.add_argument("--dry-run", action="store_true", help="validate every variant and print the commands")
    ap.add_argument("--no-log", action="store_true", help="do not append to docs/experiments.md")
    ap.add_argument("--personas", type=Path, default=DEFAULTS["personas"])
    ap.add_argument("--network", type=Path, default=DEFAULTS["network"])
    ap.add_argument("--settings", type=Path, default=DEFAULTS["settings"])
    ap.add_argument("--surprises", type=Path, default=DEFAULTS["surprises"])
    ap.add_argument("--targets", type=Path, default=DEFAULTS["targets"],
                    help="decision-N -> persona IDs, used if the file exists")
    ap.add_argument("--aliases", type=Path, default=DEFAULTS["aliases"],
                    help="dashboard action name -> engine menu id, used if the file exists")
    raise SystemExit(asyncio.run(main(ap.parse_args())))
