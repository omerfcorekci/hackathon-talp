#!/usr/bin/env python3
"""Local, read-only web viewer for simulation runs, their LLM calls, config and docs.

    python3 code/scripts/viewer.py [--root PATH] [--port 8765] [--show-fake]

Binds 127.0.0.1 only. Stdlib only. Serves code/viewer/index.html and algorithms.html (from this checkout) and a small
JSON API that reads, on every request, from an allowlist under --root:
  <root>/runs/** and <root>/experiments/**   any folder with run.json (two-round engine layout:
                                              calls/weekly/messages/probe .jsonl, network.json, ...)
  <root>/code/config/**                       decisions (plan.json, candidates/), surprises
  <root>/docs/*.md
  <root>/experiments/sweeps/<sweep>/          sweep runs <variant>_s<seed>/ + decisions/<variant>.json
                                              (Karar önerisi: goals met, then total shortfall to the
                                              board targets, then cost; see api_sweep)
Runs whose run.json model starts with "fake:" are hidden everywhere unless --show-fake is given.
Goals are always recomputed from weekly.jsonl + personas.jsonl with the current
sim.metrics.compute_metrics; cost comes from sim.decisions.DecisionPlan(...).total_cost. The
"Loglar" page lists every attempt logged in each run's calls.jsonl (valid / attempt / error_type).
Nothing else is readable (no .env, no traversal). No LLM calls are made.

Endpoints: /api/sweeps, /api/sweep?name=, /api/runs, /api/run?id=, /api/call?run=&id=,
/api/raw?run=&file=, /api/logs, /api/log?run=, /api/config, /api/docs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import traceback
from collections import Counter, defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent          # code/scripts
CODE_DIR = HERE.parent                           # code/
INDEX_HTML = CODE_DIR / "viewer" / "index.html"
ALGORITHMS_HTML = CODE_DIR / "viewer" / "algorithms.html"
RUN_FILES = ["run.json", "personas.jsonl", "calls.jsonl", "weekly.jsonl", "metrics.json",
             "probe.jsonl", "messages.jsonl", "exposures.jsonl", "network.json", "world.json",
             "announcements.json", "decision_targets.json", "state.json"]
DOCS = ["decisions-log.md", "crisis-log.md", "experiments.md", "personas.md", "engine-review.md"]
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.\-]+$")
BUDGET_USD = 4_000_000
GOAL_KEYS = ("goal_1", "goal_2", "goal_3", "goal_3b")
DEFAULT_TARGETS = {"goal_1": ">= 98", "goal_2": ">= 97", "goal_3": ">= 4.3", "goal_3b": "<= 240"}

ROOT: Path = CODE_DIR.parent
SHOW_FAKE = False
SIM = {"metrics": None, "decisions": None, "error": None, "from": None}


# ---------------------------------------------------------------- sim import (optional)

def load_sim() -> None:
    """Import sim.metrics / sim.decisions from <root>/code, else from this checkout. Never fatal."""
    for base in [ROOT / "code", CODE_DIR]:
        if not (base / "sim" / "metrics.py").exists():
            continue
        sys.path.insert(0, str(base))
        try:
            for m in [k for k in sys.modules if k == "sim" or k.startswith("sim.")]:
                del sys.modules[m]
            import sim.decisions as decisions  # noqa: E402
            import sim.metrics as metrics  # noqa: E402
            SIM.update(metrics=metrics, decisions=decisions, error=None, **{"from": str(base)})
            return
        except Exception as e:  # degrade gracefully
            SIM["error"] = f"{base}: {e!r}"
        finally:
            sys.path.remove(str(base))


# ---------------------------------------------------------------- file helpers

def inside(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def read_jsonl(p: Path) -> list[dict]:
    out = []
    try:
        with p.open(encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return out


def count_lines(p: Path) -> int | None:
    try:
        with p.open("rb") as f:
            return sum(1 for line in f if line.strip())
    except FileNotFoundError:
        return None


def is_fake_run(p: Path) -> bool:
    if SHOW_FAKE:
        return False
    rj = read_json(p / "run.json", {}) or {}
    return str(rj.get("model", "")).startswith("fake:")


def discover_runs() -> dict[str, Path]:
    runs = {}
    for top in ("runs", "experiments"):
        base = ROOT / top
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
            if "run.json" in filenames:
                p = Path(dirpath)
                if not is_fake_run(p):
                    runs[p.relative_to(ROOT).as_posix()] = p
    return runs


def run_path(run_id: str) -> Path:
    runs = discover_runs()
    if run_id not in runs:
        raise LookupError(f"unknown run: {run_id}")
    return runs[run_id]


# ---------------------------------------------------------------- budget / metrics helpers

def action_aliases() -> dict:
    p = ROOT / "code" / "config" / "decisions" / "action-aliases.json"
    data = read_json(p, None) if p.is_file() else None
    return data if isinstance(data, dict) else {}


def budget_info(decisions: list[dict], personas: list[dict] | None = None) -> dict:
    """Cost via sim.decisions.DecisionPlan; on any failure total is None and the error is shown."""
    dm = SIM["decisions"]
    if dm is None:
        return {"available": False, "error": SIM["error"] or "sim.decisions not importable"}
    info = {"available": True, "limit": BUDGET_USD, "decisions": [], "total": None, "error": None}
    if not decisions:
        info["total"] = 0
        return info
    if personas is None:
        personas = read_jsonl(ROOT / "code" / "personas" / "personas.jsonl")
    try:
        plan = dm.DecisionPlan(decisions, personas, action_aliases=action_aliases())
        info["total"] = plan.total_cost
        for i, _ in enumerate(decisions, 1):
            resolved = getattr(plan, "resolved", {}).get(f"decision-{i}", [])
            sms = list(getattr(plan, "channels", {}).get(f"decision-{i}", [])).count("sms")
            acts = [cost for _, _, cost in resolved]
            info["decisions"].append({"actions": acts, "resolved": [[n, lv] for n, lv, _ in resolved],
                                      "sms_sends": sms,
                                      "total": sum(acts) + 25_000 * sms if acts else None})
    except Exception as e:
        info["error"] = str(e)
        info["decisions"] = [{"actions": [], "total": None, "sms_sends": 0} for _ in decisions]
    return info


def compute(personas: list[dict], weekly: list[dict]) -> dict:
    return SIM["metrics"].compute_metrics(personas, weekly)


def weekly_metrics(personas: list[dict], weekly: list[dict]) -> dict:
    """goal_1 / goal_2 / goal_3 / goal_3b as if the run had stopped after week w (w = 1..last)."""
    if SIM["metrics"] is None:
        return {"available": False, "error": SIM["error"] or "sim.metrics not importable", "weeks": []}
    ids = {p.get("id") for p in personas}
    rows = [r for r in weekly if r.get("persona") in ids]
    last = max((r.get("week", 0) for r in rows if isinstance(r.get("week"), int)), default=0)
    out = []
    try:
        for w in range(1, 11):
            if w > last:
                out.append({"week": w})
                continue
            m = compute(personas, [r for r in rows if isinstance(r.get("week"), int) and r["week"] <= w])
            out.append({"week": w, **{k: m.get(k) for k in GOAL_KEYS}})
        return {"available": True, "weeks": out, "targets": targets()}
    except Exception as e:
        return {"available": False, "error": repr(e), "weeks": out}


SECTION_RE = {
    "events": re.compile(r"=== THIS WEEK: week (\d+) of 10, ([^=]*?) ===\n(.*?)(?:\n\n|\Z)", re.S),
    "experience": re.compile(r"What happened to you this week:\n(.*?)(?:\n\n|\Z)", re.S),
    "news": re.compile(r"News about Cobalt you have heard:\n(.*?)(?:\n\n|\Z)", re.S),
    "official": re.compile(r"OFFICIAL BANK MESSAGE (decision-\d+)"),
}


def feed_by_week(calls_path: Path, weekly: list[dict]) -> list[dict]:
    """What reached personas each week, read back from the round-1 prompts (line -> #personas)."""
    first_calls = {r.get("round_1_call") or r.get("call") for r in weekly}
    weeks: dict[int, Counter] = defaultdict(Counter)
    titles: dict[int, str] = {}
    for c in read_jsonl(calls_path):
        w, prompt = c.get("week"), c.get("prompt") or ""
        if c.get("id") not in first_calls or not isinstance(w, int) or not 1 <= w <= 10:
            continue
        mt = SECTION_RE["events"].search(prompt)
        if mt:
            titles.setdefault(w, mt.group(2).strip())
            for line in mt.group(3).splitlines():
                if line.strip() and not line.startswith("Friday this week"):
                    weeks[w]["[olay] " + line.strip()] += 1
        for key in ("experience", "news"):
            mt = SECTION_RE[key].search(prompt)
            if mt:
                for line in mt.group(1).splitlines():
                    line = line.strip()
                    if line.startswith("- ") and (key == "experience" or f"week {w})" in line):
                        weeks[w][("" if key == "experience" else "[haber] ") + line[2:]] += 1
        for d in SECTION_RE["official"].findall(prompt):
            weeks[w][f"[karar] {d} mesajı gelen kutusunda"] += 1
    wom = Counter()
    for r in weekly:
        if isinstance(r.get("week"), int):
            wom[r["week"]] += len(r.get("received_messages") or [])
    return [{"week": w, "title": titles.get(w, ""), "word_of_mouth": wom.get(w, 0),
             "lines": [{"text": t, "personas": n} for t, n in weeks[w].most_common()]}
            for w in sorted(set(weeks) | set(wom))]


# ---------------------------------------------------------------- recomputed goals + sweeps

_GOALS_CACHE: dict[str, tuple] = {}


def run_goals(p: Path) -> dict | None:
    """Goals recomputed with the current sim.metrics, plus by-group goal_1 / goal_2. Cached by mtimes."""
    if SIM["metrics"] is None:
        return None
    try:
        key = tuple((p / f).stat().st_mtime for f in ("personas.jsonl", "weekly.jsonl"))
    except FileNotFoundError:
        return None
    hit = _GOALS_CACHE.get(str(p))
    if hit and hit[0] == key:
        return hit[1]
    personas = read_jsonl(p / "personas.jsonl")
    ids = {x.get("id") for x in personas}
    weekly = [r for r in read_jsonl(p / "weekly.jsonl") if r.get("persona") in ids]
    try:
        res = compute(personas, weekly)
        out = {k: res.get(k) for k in GOAL_KEYS}
        out["weeks_completed"] = res.get("weeks_completed")
        out["groups"] = {g: {"active": v.get("goal_1"), "deposits": v.get("goal_2"),
                             "customers": v.get("weight_customers"), "deposits_usd": v.get("weight_deposits_usd"),
                             "personas": v.get("personas")}
                         for g, v in (res.get("by_group") or {}).items()}
        out["full"] = res
    except Exception as e:
        out = {"error": repr(e)}
    _GOALS_CACHE[str(p)] = (key, out)
    return out


SWEEP_RUN = re.compile(r"^(?P<variant>.+)_s(?P<seed>\d+)$")
TIMING = re.compile(r"^(?P<plan>.+)_d(?P<k>\d)w(?P<week>\d+)$")


def sweeps_base() -> Path:
    return ROOT / "experiments" / "sweeps"


def sweep_runs(d: Path) -> dict[str, dict[int, Path]]:
    """variant -> seed -> run folder, real runs only."""
    out: dict[str, dict[int, Path]] = defaultdict(dict)
    for r in sorted(d.iterdir()):
        mt = SWEEP_RUN.match(r.name)
        if r.is_dir() and mt and (r / "run.json").is_file() and (r / "weekly.jsonl").is_file() and not is_fake_run(r):
            out[mt["variant"]][int(mt["seed"])] = r
    return dict(out)


def sweep_dir(name: str) -> Path:
    base = sweeps_base()
    if not name or not SAFE_NAME.match(name):
        raise LookupError("bad sweep")
    d = base / name
    if not d.is_dir() or not inside(d, base) or not sweep_runs(d):
        raise LookupError(f"unknown sweep: {name}")
    return d


def api_sweeps(q) -> dict:
    out = []
    base = sweeps_base()
    if base.is_dir():
        for d in base.iterdir():
            if not d.is_dir() or not SAFE_NAME.match(d.name):
                continue
            runs = sweep_runs(d)
            if not runs:
                continue
            folders = [p for seeds in runs.values() for p in seeds.values()]
            out.append({"name": d.name, "variants": len(runs), "runs": len(folders),
                        "baseline": "nodecision" in runs,
                        "timing": any(TIMING.match(v) for v in runs),
                        "mtime": max((p / "weekly.jsonl").stat().st_mtime for p in folders)})
    out.sort(key=lambda s: -s["mtime"])
    return {"sweeps": out, "default": out[0]["name"] if out else None}


def plan_label(stem: str) -> str:
    """a_inform_cheap -> 'Plan A (inform cheap)'; anything else -> spaces for underscores."""
    mt = re.match(r"^([a-z])_(.+)$", stem)
    if mt:
        return f"Plan {mt[1].upper()} ({mt[2].replace('_', ' ')})"
    return stem.replace("_", " ")


def stats(vals: list[float]) -> dict:
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"mean": None, "min": None, "max": None, "n": 0}
    return {"mean": round(sum(vals) / len(vals), 3), "min": min(vals), "max": max(vals), "n": len(vals)}


def target_of(key: str):
    """('>=', 98.0) from the board target string; None when unparseable."""
    mt = re.match(r"^(>=|<=)\s*([\d.]+)", targets().get(key, ""))
    return (mt[1], float(mt[2])) if mt else None


def met(key: str, v) -> bool | None:
    t = target_of(key)
    if v is None or t is None:
        return None
    return v >= t[1] if t[0] == ">=" else v <= t[1]


# One "point" of shortfall per goal, so the four goals add up in a common unit:
# 1 percentage point of actives or deposits, 0.1 of App Store rating, 24 CFPB complaints a month.
GAP_UNIT = {"goal_1": 1.0, "goal_2": 1.0, "goal_3": 0.1, "goal_3b": 24.0}


def shortfall(key: str, v) -> float | None:
    """How far below (or, for 3b, above) the board target this value is, in points; 0 when met."""
    t = target_of(key)
    if v is None or t is None:
        return None
    raw = (t[1] - v) if t[0] == ">=" else (v - t[1])
    return round(max(0.0, raw) / GAP_UNIT[key], 3)


def api_sweep(q) -> dict:
    """Rank a sweep's variants and recommend one. Three ranking keys, in order:
    1. goals met (of 4), on the mean over seeds;
    2. total shortfall: for each goal the distance below its target in common points
       (pp of actives/deposits, 0.1 rating, 24 complaints), summed; 0 when every goal is met;
    3. cost.
    Noise rule: variants that meet as many goals as the best and whose shortfall differs from it
    by less than the seed spread are "equivalent"; the cheapest equivalent is recommended.
    The per-goal change against the same seed's nodecision run is shown, not ranked on."""
    if SIM["metrics"] is None:
        raise LookupError(f"sim.metrics not importable: {SIM['error']}")
    d = sweep_dir(q.get("name", [""])[0])
    runs = sweep_runs(d)
    goals = {v: {s: run_goals(p) or {} for s, p in seeds.items()} for v, seeds in runs.items()}
    base = goals.get("nodecision")

    variants = []
    for v, seeds in runs.items():
        first = next(iter(seeds.values()))
        decs = read_json(d / "decisions" / f"{v}.json", None)
        if not isinstance(decs, list):
            decs = (read_json(first / "run.json", {}) or {}).get("decisions") or []
        b = budget_info(decs, read_jsonl(first / "personas.jsonl"))
        g = goals[v]
        row = {"variant": v, "baseline": v == "nodecision", "seeds": sorted(seeds),
               "runs": {s: p.relative_to(ROOT).as_posix() for s, p in seeds.items()},
               "decisions": decs, "cost": b.get("total") if b.get("available") else None,
               "cost_error": b.get("error"),
               "weeks": [x.get("week") for x in decs]}
        tm = TIMING.match(v)
        row["plan"] = tm["plan"] if tm else v
        row["label"] = "Kararsız (baz)" if v == "nodecision" else plan_label(row["plan"])
        row["varied"] = {"decision": int(tm["k"]), "week": int(tm["week"])} if tm else None
        row["goals"] = {k: stats([x.get(k) for x in g.values()]) for k in GOAL_KEYS}
        row["met"] = {k: met(k, row["goals"][k]["mean"]) for k in GOAL_KEYS}
        row["met_count"] = sum(1 for x in row["met"].values() if x)
        row["gap"] = {k: shortfall(k, row["goals"][k]["mean"]) for k in GOAL_KEYS}
        row["gap_total"] = round(sum(x for x in row["gap"].values() if x is not None), 3)
        per_seed = [sum(x for x in (shortfall(k, r.get(k)) for k in GOAL_KEYS) if x is not None) for r in g.values()]
        row["gap_spread"] = round(max(per_seed) - min(per_seed), 3) if len(per_seed) > 1 else None
        row["weeks_completed"] = sorted({x.get("weeks_completed") for x in g.values() if x.get("weeks_completed")})
        if base and not row["baseline"]:
            deltas = {k: [] for k in GOAL_KEYS}
            for s, x in g.items():
                bs = base.get(s)
                if not bs:
                    continue
                for k in GOAL_KEYS:
                    if x.get(k) is not None and bs.get(k) is not None:
                        deltas[k].append(x[k] - bs[k])
            row["delta"] = {k: stats(vals)["mean"] for k, vals in deltas.items()}
        grp: dict[str, dict] = {}
        for x in g.values():
            for name, gv in (x.get("groups") or {}).items():
                e = grp.setdefault(name, {"active": [], "deposits": [], "customers": gv.get("customers"),
                                          "deposits_usd": gv.get("deposits_usd"), "personas": gv.get("personas")})
                e["active"].append(gv.get("active"))
                e["deposits"].append(gv.get("deposits"))
        row["groups"] = {n: dict(e, active=stats(e["active"])["mean"], deposits=stats(e["deposits"])["mean"])
                         for n, e in grp.items()}
        variants.append(row)

    def key(r):
        return (-r["met_count"], r["gap_total"], r["cost"] if r["cost"] is not None else 1e18)

    ranked = sorted([r for r in variants if not r["baseline"]], key=key)
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    baseline = next((r for r in variants if r["baseline"]), None)

    rec = None
    if ranked:
        best = ranked[0]
        noise = max((r["gap_spread"] or 0) for r in ranked)
        equivalent = [r for r in ranked if r["met_count"] == best["met_count"]
                      and abs(r["gap_total"] - best["gap_total"]) <= noise]
        chosen = min(equivalent, key=lambda r: r["cost"] if r["cost"] is not None else 1e18)
        for r in ranked:
            r["equivalent"] = r in equivalent
        rec = {"variant": chosen["variant"], "best_by_score": best["variant"],
               "equivalent": [r["variant"] for r in equivalent], "noise": round(noise, 3),
               "seeds": len(chosen["seeds"]), "single_seed": any(len(r["seeds"]) < 2 for r in ranked)}
        if baseline:
            rec["no_gain"] = (chosen["met_count"], -chosen["gap_total"]) <= (baseline["met_count"], -baseline["gap_total"])

    matrix = None
    timed = [r for r in ranked if r["varied"]]
    if timed:
        plans = list(dict.fromkeys(f"{r['plan']}|{r['varied']['decision']}" for r in timed))
        weeks = sorted({r["varied"]["week"] for r in timed})
        rows = []
        for pk in plans:
            plan, k = pk.rsplit("|", 1)
            cells = {r["varied"]["week"]: {"variant": r["variant"], "gap_total": r["gap_total"],
                                           "spread": r["gap_spread"], "met_count": r["met_count"]}
                     for r in timed if r["plan"] == plan and r["varied"]["decision"] == int(k)}
            best_w = min(cells, key=lambda w: (-cells[w]["met_count"], cells[w]["gap_total"]), default=None)
            rows.append({"plan": plan, "label": plan_label(plan), "decision": int(k), "cells": cells, "best_week": best_w})
        matrix = {"weeks": weeks, "rows": rows}

    return {"name": d.name, "targets": targets(), "variants": ranked + ([baseline] if baseline else []),
            "baseline": baseline is not None, "recommendation": rec, "matrix": matrix,
            "score": "önce tutan hedef sayısı (4 üzerinden), sonra toplam hedef açığı "
                     "(1 puan = 1 yüzde puan aktif/mevduat, 0.1 App Store puanı, 24 CFPB şikayeti), sonra maliyet; "
                     "açık farkı seed oynamasından küçükse eşdeğer sayılır ve ucuz olan önerilir",
            "sim_from": SIM["from"]}


# ---------------------------------------------------------------- API handlers

def targets() -> dict:
    m = SIM["metrics"]
    return getattr(m, "BOARD_TARGETS", None) or getattr(m, "TARGETS", None) or DEFAULT_TARGETS


def call_stats(p: Path) -> dict:
    rows = read_jsonl(p / "calls.jsonl")
    return {"calls": len(rows), "failed": sum(1 for r in rows if r.get("valid") is False),
            "retries": sum(1 for r in rows if (r.get("attempt") or 1) > 1)}


def api_runs(q) -> dict:
    out = []
    for rid, p in discover_runs().items():
        rj = read_json(p / "run.json", {}) or {}
        mt = run_goals(p) or read_json(p / "metrics.json", None)
        mtimes = [f.stat().st_mtime for f in p.iterdir() if f.is_file()]
        out.append({
            "id": rid, "name": rj.get("name") or p.name, "type": rj.get("type"), "seed": rj.get("seed"),
            "model": rj.get("model"), "fake": str(rj.get("model", "")).startswith("fake:"),
            "surprises": rj.get("type") != "plan_nosurprises",
            "complete": rj.get("complete"), "completed_weeks": rj.get("completed_weeks"),
            "decisions": len(rj.get("decisions") or []),
            "personas": count_lines(p / "personas.jsonl"), "calls": count_lines(p / "calls.jsonl"),
            "mtime": max(mtimes) if mtimes else None,
            "metrics": {k: mt.get(k) for k in GOAL_KEYS} if isinstance(mt, dict) else None,
        })
    out.sort(key=lambda r: r["id"])
    return {"root": str(ROOT), "runs": out, "targets": targets()}


def api_run(q) -> dict:
    rid = q.get("id", [""])[0]
    p = run_path(rid)
    rj = read_json(p / "run.json", {}) or {}
    personas = read_jsonl(p / "personas.jsonl")
    weekly = read_jsonl(p / "weekly.jsonl")
    files = []
    for f in RUN_FILES:
        fp = p / f
        if fp.exists():
            files.append({"name": f, "size": fp.stat().st_size, "lines": count_lines(fp) if f.endswith(".jsonl") else None})
    goals = run_goals(p) or {}
    stored = read_json(p / "metrics.json", None)
    metrics = dict(goals.get("full") or stored or {})
    probe = read_jsonl(p / "probe.jsonl")
    return {
        "id": rid, "run": rj, "personas": personas, "weekly": weekly,
        "metrics": metrics or None, "metrics_stored": stored,
        "probe": probe or None,
        "messages": read_jsonl(p / "messages.jsonl"),
        "announcements": read_json(p / "announcements.json", None),
        "decision_targets": read_json(p / "decision_targets.json", None),
        "call_stats": call_stats(p),
        "files": files, "budget": budget_info(rj.get("decisions") or [], personas),
        "weekly_metrics": weekly_metrics(personas, weekly),
        "feed": feed_by_week(p / "calls.jsonl", weekly),
        "targets": targets(),
        "fake": str(rj.get("model", "")).startswith("fake:"),
    }


def api_call(q) -> dict:
    p = run_path(q.get("run", [""])[0])
    cid = q.get("id", [""])[0]
    rows = read_jsonl(p / "calls.jsonl")
    c = next((r for r in rows if r.get("id") == cid), None)
    if c is None:
        raise LookupError(f"call not found: {cid}")
    # Failed attempts for the same persona / week / round (the retry chain before this answer).
    chain = [{k: r.get(k) for k in ("id", "attempt", "valid", "error_type", "error_stage", "model", "elapsed_seconds")}
             for r in rows if r.get("persona") == c.get("persona") and r.get("week") == c.get("week")
             and r.get("round") == c.get("round") and r.get("valid") is False]
    return dict(c, failed_attempts=chain)


def api_raw(q) -> dict | tuple:
    p = run_path(q.get("run", [""])[0])
    name = q.get("file", [""])[0]
    if name not in RUN_FILES:
        raise PermissionError("file not allowed")
    fp = p / name
    if not fp.exists():
        raise LookupError("missing file")
    return ("text", fp.read_text(encoding="utf-8"))


def api_logs(q) -> dict:
    """One row per run: attempt counts from calls.jsonl (the engine logs every attempt there)."""
    out = []
    for rid, p in discover_runs().items():
        rows = read_jsonl(p / "calls.jsonl")
        if not rows:
            continue
        rj = read_json(p / "run.json", {}) or {}
        el = [r.get("elapsed_seconds") for r in rows if isinstance(r.get("elapsed_seconds"), (int, float))]
        out.append({"run": rid, "type": rj.get("type"), "seed": rj.get("seed"), "model": rj.get("model"),
                    "complete": rj.get("complete"), "failure_type": rj.get("failure_type"),
                    "calls": len(rows), "failed": sum(1 for r in rows if r.get("valid") is False),
                    "retries": sum(1 for r in rows if (r.get("attempt") or 1) > 1),
                    "avg_ms": round(1000 * sum(el) / len(el)) if el else None,
                    "errors": dict(Counter(str(r.get("error_type")) for r in rows if r.get("valid") is False)),
                    "models": sorted({str(r.get("model")) for r in rows}),
                    "mtime": (p / "calls.jsonl").stat().st_mtime})
    out.sort(key=lambda r: -r["mtime"])
    return {"runs": out}


LIGHT = ["id", "persona", "week", "round", "attempt", "valid", "error_type", "error_stage", "model",
         "elapsed_seconds"]


def api_log(q) -> dict:
    rid = q.get("run", [""])[0]
    p = run_path(rid)
    text = q.get("q", [""])[0].lower().strip()
    calls = []
    for i, r in enumerate(read_jsonl(p / "calls.jsonl")):
        if text and text not in ((r.get("prompt") or "") + "\n" + (r.get("response") or "")).lower():
            continue
        row = {k: r.get(k) for k in LIGHT}
        row["line"] = i
        calls.append(row)
    return {"run": rid, "meta": read_json(p / "run.json", {}), "calls": calls, "q": text}


def api_config(q) -> dict:
    cfg = ROOT / "code" / "config"
    personas = read_jsonl(ROOT / "code" / "personas" / "personas.jsonl")
    plan = read_json(cfg / "decisions" / "plan.json", None)
    surprises = []
    sdir = cfg / "surprises"
    if sdir.is_dir():
        for f in sorted(sdir.glob("*.json")):
            surprises.append({"file": f.name, "data": read_json(f, None)})
    candidates = []
    cdir = cfg / "decisions" / "candidates"
    if cdir.is_dir():
        for f in sorted(cdir.glob("*.json")):
            d = read_json(f, None)
            candidates.append({"file": f.name, "data": d,
                               "budget": budget_info(d, personas) if isinstance(d, list) else None})
    return {"plan": plan, "plan_budget": budget_info(plan, personas) if isinstance(plan, list) else None,
            "nodecision": read_json(cfg / "decisions" / "nodecision.json", None),
            "candidates": candidates, "surprises": surprises,
            "sim_from": SIM["from"], "sim_error": SIM["error"]}


def api_docs(q) -> dict:
    out = {}
    for name in DOCS:
        fp = ROOT / "docs" / name
        out[name] = fp.read_text(encoding="utf-8") if fp.is_file() else None
    return {"docs": out}


ROUTES = {"/api/runs": api_runs, "/api/run": api_run, "/api/call": api_call, "/api/raw": api_raw,
          "/api/logs": api_logs, "/api/log": api_log,
          "/api/config": api_config, "/api/docs": api_docs,
          "/api/sweeps": api_sweeps, "/api/sweep": api_sweep}


class Handler(BaseHTTPRequestHandler):
    server_version = "talp-viewer"

    def log_message(self, fmt, *args):  # quieter
        sys.stderr.write("%s %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, code: int, obj) -> None:
        self.send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        path = u.path
        page = {"/": INDEX_HTML, "/index.html": INDEX_HTML, "/algorithms.html": ALGORITHMS_HTML}.get(path)
        if page is not None:
            try:
                return self.send(200, page.read_bytes(), "text/html; charset=utf-8")
            except FileNotFoundError:
                return self.send_json(500, {"error": f"missing {page}"})
        fn = ROUTES.get(path)
        if fn is None:
            return self.send_json(404, {"error": "not found"})
        try:
            res = fn(parse_qs(u.query))
            if isinstance(res, tuple) and res[0] == "text":
                return self.send(200, res[1].encode("utf-8"), "text/plain; charset=utf-8")
            return self.send_json(200, res)
        except PermissionError as e:
            return self.send_json(403, {"error": str(e)})
        except (LookupError, ValueError) as e:
            return self.send_json(404, {"error": str(e)})
        except Exception as e:
            traceback.print_exc()
            return self.send_json(500, {"error": repr(e)})


def main() -> None:
    global ROOT, SHOW_FAKE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(CODE_DIR.parent), help="repo root to read data from")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--show-fake", action="store_true", help="also list runs whose model starts with fake:")
    a = ap.parse_args()
    ROOT = Path(a.root).expanduser().resolve()
    SHOW_FAKE = a.show_fake
    if not ROOT.is_dir():
        sys.exit(f"--root is not a directory: {ROOT}")
    load_sim()
    if SIM["metrics"] is None:
        print(f"warning: sim.metrics/sim.decisions not importable ({SIM['error']}); budget and metrics off")
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"viewer: http://127.0.0.1:{a.port}/   root: {ROOT}   sim from: {SIM['from']}"
          f"{'   (fake runs shown)' if SHOW_FAKE else ''}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
