#!/usr/bin/env python3
"""Offline end-to-end test: five fake runs (with the TEST FIXTURE surprise) -> ZIP -> brief/check.py.

    env -u TALP_KEY python3 code/tests/fake_end_to_end.py [--weeks N] [--keep DIR]

Runs code/scripts/run_all.sh --fake (FakeTransport: no key, no model calls) into a temporary
directory, never into runs/. The fixture surprise in code/tests/fixtures/surprises/ is needed
because check.py requires plan_1 and plan_nosurprises to send different prompts. The decisions are
a fixed copy of candidate A in code/tests/fixtures/decisions/. Also checks: fake model names, no
key-like string in the ZIP, decision messages never before their week or in nodecision runs, and
the two seeds give different answers. Exits non-zero on any failure.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
REPO = CODE.parent
FIXTURES = CODE / "tests" / "fixtures"
NAMES = ("plan_1", "plan_2", "nodecision_1", "nodecision_2", "plan_nosurprises")
KEY_LIKE = re.compile(rb"AQ\.[A-Za-z0-9_\-]{40,}")


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sanity(runs: Path) -> list[str]:
    problems = []
    decisions = json.loads((runs / "plan_1" / "run.json").read_text())["decisions"]
    for name in NAMES:
        meta = json.loads((runs / name / "run.json").read_text())
        calls = jsonl(runs / name / "calls.jsonl")
        if not str(meta.get("model", "")).startswith("fake:"):
            problems.append(f"{name}: run.json model {meta.get('model')!r} is not fake:...")
        if any(not str(c.get("model", "")).startswith("fake:") for c in calls):
            problems.append(f"{name}: calls.jsonl has a non-fake model name")
        invalid = sum(c.get("valid") is False for c in calls)
        if invalid:
            print(f"  {name}: {invalid} rejected fake answers (retried)")
        for i, d in enumerate(decisions, 1):
            hits = [c for c in calls if d["message"] in c["prompt"]]
            if name.startswith("nodecision"):
                if hits:
                    problems.append(f"{name}: decision {i} message appears in a nodecision run")
                continue
            early = [c for c in hits if c["week"] < d["week"]]
            if early:
                problems.append(f"{name}: decision {i} message appears before week {d['week']}")
            if not hits:
                problems.append(f"{name}: decision {i} message never shown")
            else:
                print(f"  {name}: decision {i} shown in weeks {sorted({c['week'] for c in hits})}, "
                      f"{len({c['persona'] for c in hits})} personas")
    statuses = {}
    for row in jsonl(runs / "plan_1" / "weekly.jsonl"):
        statuses[row["status"]] = statuses.get(row["status"], 0) + 1
    print(f"  plan_1 status mix: {statuses}")
    r1 = sorted(c["response"] for c in jsonl(runs / "plan_1" / "calls.jsonl") if 1 <= c["week"] <= 10)
    r2 = sorted(c["response"] for c in jsonl(runs / "plan_2" / "calls.jsonl") if 1 <= c["week"] <= 10)
    same = sum(a == b for a, b in zip(r1, r2))
    print(f"  plan_1 vs plan_2: {len(r1)} vs {len(r2)} responses, {same} identical after sorting")
    if r1 == r2:
        problems.append("plan_1 and plan_2 responses are identical")
    return problems


def build_zip(sub: Path, zpath: Path) -> list[str]:
    for doc in ("CLIENT_MEMO.md", "TEAM_DOC.md"):
        source = REPO / doc
        if source.is_file():
            shutil.copyfile(source, sub / doc)
        else:
            (sub / doc).write_text(f"# Placeholder {doc} for the fake end-to-end test\n", encoding="utf-8")
    # Same content rules as make_submission.sh: no caches, .DS_Store, .gitkeep or .env files.
    shutil.copytree(CODE, sub / "code", ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", ".DS_Store", ".gitkeep", "*.env"))
    problems = []
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as archive:
        for top in ("CLIENT_MEMO.md", "TEAM_DOC.md", "code", "runs"):
            path = sub / top
            files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
            for file in files:
                if KEY_LIKE.search(file.read_bytes()):
                    problems.append(f"key-like string in {file.relative_to(sub)}")
                archive.write(file, file.relative_to(sub).as_posix())
    return problems


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks", type=int, default=10)
    parser.add_argument("--keep", type=Path, help="also copy the built ZIP into this directory")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="talp_fake_") as tmp:
        tmp = Path(tmp)
        sub = tmp / "submission"
        started = time.monotonic()
        subprocess.run(["bash", str(CODE / "scripts" / "run_all.sh"), "--fake", "--weeks", str(args.weeks),
                        "--out-root", str(sub / "runs"),
                        "--plan", str(FIXTURES / "decisions" / "a_inform_cheap.json"),
                        "--surprises", str(FIXTURES / "surprises")], check=True)
        print(f"five fake runs: {time.monotonic() - started:.1f}s")
        leftovers = [p.name for p in (sub / "runs").iterdir() if p.name not in NAMES]
        print("sanity:")
        problems = sanity(sub / "runs")
        if leftovers:
            problems.append(f"unexpected entries in runs/: {leftovers}")
        zpath = tmp / "team-07_submission.zip"
        problems += build_zip(sub, zpath)
        check = subprocess.run([sys.executable, str(REPO / "brief" / "check.py"), str(zpath)])
        if args.keep:
            args.keep.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(zpath, args.keep / zpath.name)
    for problem in problems:
        print("SANITY FAIL:", problem)
    if check.returncode:
        print(f"check.py exited {check.returncode}")
    return 1 if problems or check.returncode else 0


if __name__ == "__main__":
    sys.exit(main())
