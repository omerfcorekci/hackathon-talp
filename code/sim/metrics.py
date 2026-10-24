"""metrics.json: Cobalt's board goals from recorded weekly behavior and the personas' own weights.

Only model-recorded weekly fields are read (status, money, active_in_last_30_days, app_rating,
complaint) together with the external weights in personas.jsonl. Nothing here calls a model or
edits a persona's answer. Assumptions, written verbatim to metrics.json under "assumptions":

- goal_1 (% of Nov 2 30-day actives) = 100 × A_last / A_1, where A_w = Σ weight_customers over
  personas whose week-w row has active_derived == true (an app action in that week or the three
  before it, status not "left"; derived by the engine from the actions the model reported, falling
  back to the model's own active_in_last_30_days when absent) and status "main bank" or
  "second bank". Week 1 stands for the November 2 baseline. If A_1 is 0, goal_1 is written as 0
  and a note says so. Rounded to 2 decimals.
- goal_2 (% of Nov 2 deposits) = 100 × Σ weight_deposits_usd × f / Σ weight_deposits_usd over
  the final week's rows, with f = 1.0 for money "kept", 0.6 for "moved some", 0.1 for "moved most",
  and f = 0 when status is "left"; plus 0.1 when new_money is "some" and 0.3 when it is "a lot"
  (money brought into Cobalt from elsewhere, as a share of the persona's Nov 2 deposits), so
  new-money offers can show growth. The model-reported balance is not used. Rounded to 2 decimals.
- goal_3 (App Store rating) = (4.6 × 210,000 + Σ 0.02 × weight_customers × app_rating) /
  (210,000 + Σ 0.02 × weight_customers), summed over every persona-week (weeks 1-10) whose
  app_rating is not null. The existing review mass equals 10% of customers (210,000 reviews) at
  4.6; when a persona reviews, 2% of the customers it stands for leave that rating. Rounded to
  2 decimals.
- goal_3b (CFPB complaints per month, worst month) = 120 × (1 + 4 × S), where S is the maximum
  over the sliding 4-week windows (weeks 1-4, 2-5, ..., 7-10) of Σ weight_customers of personas
  with complaint == "cfpb" in any week of that window / 2,100,000. 25% of represented customers
  escalating to the CFPB in a month doubles the baseline of 120 a month. Rounded to 1 decimal.
  Board limit 240.
- Weights are the personas' own weight_customers (2.1 million in total) and weight_deposits_usd.
  A missing or invalid weight counts as 0 and is listed under notes.
- An incomplete run uses its last completed week in place of week 10 and only windows inside the
  completed weeks (fewer than 4 weeks: one window); weeks_completed says how many weeks it covers.
- by_group applies the same formulas to one dossier group's personas. goal_1 and goal_2 use the
  group's own week-1 actives and deposits as the baseline; goal_3 and goal_3b keep the bank-wide
  constants (210,000 reviews at 4.6; 2,100,000 customers; 120 a month), so they show the bank-wide
  number if only that group's personas had rated or escalated.

Recompute an existing run without model calls: PYTHONPATH=code python3 -m sim.metrics runs/plan_1
"""

import json
import math
import sys
from pathlib import Path

ASSUMPTIONS = [
    "goal_1 (% of Nov 2 30-day actives) = 100 × A_last / A_1, where A_w = Σ weight_customers over "
    "personas whose week-w row has active_derived == true (an app action in that week or the three "
    "before it, status not \"left\"; derived by the engine from the actions the model reported, falling "
    "back to the model's own active_in_last_30_days when absent) and status \"main bank\" or "
    "\"second bank\". Week 1 stands for the November 2 baseline. If A_1 is 0, goal_1 is written as 0 "
    "and a note says so. Rounded to 2 decimals.",
    "goal_2 (% of Nov 2 deposits) = 100 × Σ weight_deposits_usd × f / Σ weight_deposits_usd over "
    "the final week's rows, with f = 1.0 for money \"kept\", 0.6 for \"moved some\", 0.1 for \"moved most\", "
    "and f = 0 when status is \"left\"; plus 0.1 when new_money is \"some\" and 0.3 when it is \"a lot\" "
    "(money brought into Cobalt from elsewhere, as a share of the persona's Nov 2 deposits), so "
    "new-money offers can show growth. The model-reported balance is not used. Rounded to 2 decimals.",
    "goal_3 (App Store rating) = (4.6 × 210,000 + Σ 0.02 × weight_customers × app_rating) / "
    "(210,000 + Σ 0.02 × weight_customers), summed over every persona-week (weeks 1-10) whose "
    "app_rating is not null. The existing review mass equals 10% of customers (210,000 reviews) at "
    "4.6; when a persona reviews, 2% of the customers it stands for leave that rating. Rounded to "
    "2 decimals.",
    "goal_3b (CFPB complaints per month, worst month) = 120 × (1 + 4 × S), where S is the maximum "
    "over the sliding 4-week windows (weeks 1-4, 2-5, ..., 7-10) of Σ weight_customers of personas "
    "with complaint == \"cfpb\" in any week of that window / 2,100,000. 25% of represented customers "
    "escalating to the CFPB in a month doubles the baseline of 120 a month. Rounded to 1 decimal. "
    "Board limit 240.",
    "Weights are the personas' own weight_customers (2.1 million in total) and weight_deposits_usd. "
    "A missing or invalid weight counts as 0 and is listed under notes.",
    "An incomplete run uses its last completed week in place of week 10 and only windows inside the "
    "completed weeks (fewer than 4 weeks: one window); weeks_completed says how many weeks it covers.",
    "by_group applies the same formulas to one dossier group's personas. goal_1 and goal_2 use the "
    "group's own week-1 actives and deposits as the baseline; goal_3 and goal_3b keep the bank-wide "
    "constants (210,000 reviews at 4.6; 2,100,000 customers; 120 a month), so they show the bank-wide "
    "number if only that group's personas had rated or escalated.",
]

UNITS = {
    "goal_1": "% of Nov 2 30-day active customers (week 1 = baseline)",
    "goal_2": "% of Nov 2 deposits, money factor kept=1.0 / moved some=0.6 / moved most=0.1 / left=0",
    "goal_3": "App Store rating, 1-5",
    "goal_3b": "CFPB complaints per month, worst 4-week window (baseline 120, board limit 240)",
}
BOARD_TARGETS = {"goal_1": ">= 98", "goal_2": ">= 97", "goal_3": ">= 4.3", "goal_3b": "<= 240"}

ACTIVE_STATUSES = ("main bank", "second bank")
MONEY_FACTOR = {"kept": 1.0, "moved some": 0.6, "moved most": 0.1}
NEW_MONEY_FACTOR = {"none": 0.0, "some": 0.1, "a lot": 0.3}  # money brought into Cobalt, as a share of Nov 2 deposits
CUSTOMERS = 2_100_000
REVIEW_MASS = 210_000
BASE_RATING = 4.6
REVIEW_SHARE = 0.02
CFPB_BASELINE = 120
WINDOW = 4


def _weights(personas, key, notes):
    weights = {}
    for person in personas:
        value = person.get(key)
        if type(value) in (int, float) and math.isfinite(value) and value >= 0:
            weights[person["id"]] = float(value)
        else:
            weights[person["id"]] = 0.0
            notes.append(f"persona {person['id']}: no valid {key}; counted as 0")
    return weights


def _windows(last):
    if last < 1:
        return []
    return [(start, min(start + WINDOW - 1, last)) for start in range(1, max(1, last - WINDOW + 1) + 1)]


def _goals(ids, rows, last, customers, deposits, notes, label):
    def active(week):
        return sum(customers[pid] for pid in ids if (row := rows.get((pid, week)))
                   and row.get("active_derived", row.get("active_in_last_30_days")) is True
                   and row.get("status") in ACTIVE_STATUSES)

    series = {week: active(week) for week in range(1, last + 1)}
    baseline = series.get(1, 0.0)
    if baseline > 0:
        goal_1 = round(100 * series[last] / baseline, 2)
    else:
        goal_1 = 0.0
        notes.append(f"{label}: no weighted week-1 actives (A_1 = 0); goal_1 written as 0")

    final = [(pid, rows[(pid, last)]) for pid in ids if (pid, last) in rows]
    total = sum(deposits[pid] for pid, _ in final)
    if total > 0:
        kept = sum(deposits[pid] * (0.0 if row["status"] == "left"
                                    else MONEY_FACTOR[row["money"]] + NEW_MONEY_FACTOR.get(row.get("new_money", "none"), 0.0))
                   for pid, row in final)
        goal_2 = round(100 * kept / total, 2)
    else:
        goal_2 = 0.0
        notes.append(f"{label}: no weighted deposits in the final week; goal_2 written as 0")

    rated = [(pid, row["app_rating"]) for (pid, week), row in rows.items()
             if pid in ids and 1 <= week <= last and row.get("app_rating") is not None]
    mass = sum(REVIEW_SHARE * customers[pid] for pid, _ in rated)
    score = sum(REVIEW_SHARE * customers[pid] * rating for pid, rating in rated)
    goal_3 = round((BASE_RATING * REVIEW_MASS + score) / (REVIEW_MASS + mass), 2)

    shares = {}
    for start, end in _windows(last):
        escalated = [pid for pid in ids
                     if any(rows.get((pid, week), {}).get("complaint") == "cfpb" for week in range(start, end + 1))]
        shares[f"{start}-{end}"] = sum(customers[pid] for pid in escalated) / CUSTOMERS
    worst = max(shares.values(), default=0.0)
    goal_3b = round(CFPB_BASELINE * (1 + 4 * worst), 1)

    goals = {"goal_1": goal_1, "goal_2": goal_2, "goal_3": goal_3, "goal_3b": goal_3b}
    detail = {"active_customers_weighted": {str(week): value for week, value in series.items()},
              "cfpb_share_by_window": {key: round(value, 6) for key, value in shares.items()},
              "rated_persona_weeks": len(rated)}
    return goals, detail


def compute_metrics(personas, weekly_rows):
    """Pure function: external personas (with weights) and weekly.jsonl rows -> metrics.json dict."""
    notes = []
    customers = _weights(personas, "weight_customers", notes)
    deposits = _weights(personas, "weight_deposits_usd", notes)
    rows = {(row["persona"], row["week"]): row for row in weekly_rows
            if type(row.get("week")) is int and 1 <= row["week"] <= 10}
    last = max((week for _, week in rows), default=0)
    if last == 0:
        notes.append("no completed weeks; goals computed from no rows")
    all_ids = {p["id"] for p in personas}
    goals, detail = _goals(all_ids, rows, last, customers, deposits, notes, "all")
    by_group = {}
    for group in sorted({p["group"] for p in personas}):
        ids = {p["id"] for p in personas if p["group"] == group}
        group_goals, _ = _goals(ids, rows, last, customers, deposits, notes, group)
        by_group[group] = {**group_goals, "personas": len(ids),
                           "weight_customers": sum(customers[pid] for pid in ids),
                           "weight_deposits_usd": sum(deposits[pid] for pid in ids)}
    return {**goals, "units": UNITS, "board_targets": BOARD_TARGETS, "weeks_completed": last,
            "assumptions": ASSUMPTIONS, "by_group": by_group, "series": detail,
            "notes": list(dict.fromkeys(notes))}


def write_metrics(writer, personas, weekly_rows):
    data = compute_metrics(personas, weekly_rows)
    writer.write("metrics.json", data)
    return data


def main(argv):
    """Recompute metrics.json for a finished run directory from its personas.jsonl and weekly.jsonl."""
    from .io import load_personas

    if len(argv) != 2:
        print("usage: PYTHONPATH=code python3 -m sim.metrics RUN_DIR", file=sys.stderr)
        return 2
    run = Path(argv[1])
    personas = load_personas(run / "personas.jsonl")
    weekly = [json.loads(line) for line in (run / "weekly.jsonl").read_text(encoding="utf-8").split("\n")
              if line.strip()]
    data = compute_metrics(personas, weekly)
    (run / "metrics.json").write_text(json.dumps(data, ensure_ascii=False, allow_nan=False) + "\n",
                                      encoding="utf-8")
    print(json.dumps({key: data[key] for key in ("goal_1", "goal_2", "goal_3", "goal_3b", "weeks_completed")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
