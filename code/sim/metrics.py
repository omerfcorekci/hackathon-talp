import json
import math
import sys
from pathlib import Path

# Follow share: a persona stands for tens of thousands of customers; only a share f of them make
# the same move it makes in a week (Tarik's rule, ported from tarik/main code/sim/metrics.py).
FOLLOW_BASE = 0.25
FOLLOW_SECOND_BANK = 0.10      # cobalt_role == "second bank": easier to walk away
FOLLOW_PAYCHECK = -0.10        # paycheck_into_cobalt: moving a direct deposit takes effort
FOLLOW_PER_TRAIT_POINT = 0.03  # per point of rate sensitivity and of anxiety above/below 3
FOLLOW_MIN = 0.05
FOLLOW_MAX = 0.5
NEUTRAL_TRAIT = 3
RATE_SENSITIVITY = {True: 5, False: 2}           # from moves_money_for_rate
ANXIETY = {"low": 2, "medium": 3, "high": 4}     # from baseline_anxiety
INACTIVE_AT_START = ("dormant", "left")          # cobalt_role values that would mean not active on Nov 2

ASSUMPTIONS = [
    "Follow share: each persona stands for weight_customers real customers, but only a share f of "
    "them make the same move it makes. f = 0.25 + 0.10 if cobalt_role is \"second bank\" - 0.10 if "
    "paycheck_into_cobalt + 0.03 × (rate_sensitivity - 3) + 0.03 × (anxiety - 3), clamped to "
    "0.05-0.5, where rate_sensitivity = 5 if moves_money_for_rate is true and 2 if false, anxiety = "
    "2 / 3 / 4 for baseline_anxiety low / medium / high, and a missing field counts as neutral (3, "
    "or false). The constants are a modelling judgement, not fitted to data; follow_share lists f "
    "per persona. Statuses and answers are never changed; f only sets how personas are added up.",
    "goal_1 (% of Nov 2 30-day actives) = 100 × (B - L) / B, where B = Σ weight_customers of the "
    "personas active on Nov 2 (every persona unless its cobalt_role is \"dormant\" or \"left\") and "
    "L = Σ f × weight_customers over those personas whose final-week row is not active: status not "
    "\"main bank\" or \"second bank\", or active_derived false (an app action in that week or the three "
    "before it, status not \"left\"; derived by the engine from the actions the model reported, falling "
    "back to the model's own active_in_last_30_days when absent) after the persona had used the app in "
    "an earlier week. A persona that stays a customer but never reports an app action (only \"wait and "
    "see\") is a quiet user and is not counted as lost. The model's week-1 answer is not the "
    "baseline, so goal_1 is at most 100. A persona with no final-week row counts as unchanged. If B is "
    "0, goal_1 is written as 0 and a note says so. Rounded to 2 decimals.",
    "goal_2 (% of Nov 2 deposits) = 100 × (D + Σ f × weight_deposits_usd × (m + n - 1)) / D over the "
    "final week's rows, where D = Σ weight_deposits_usd of all personas, m = 1.0 for money \"kept\", "
    "0.6 for \"moved some\", 0.1 for \"moved most\" (the engine's balance_derived factor), n = 0.1 when "
    "new_money is \"some\" and 0.3 when it is \"a lot\" (money brought into Cobalt from elsewhere, as a "
    "share of the persona's Nov 2 deposits), and m + n = 0 when status is \"left\". The model-reported "
    "balance is not used. Rounded to 2 decimals.",
    "goal_3 (App Store rating) = (4.6 × 210,000 + Σ 0.02 × f × weight_customers × app_rating) / "
    "(210,000 + Σ 0.02 × f × weight_customers), summed over every persona-week (weeks 1-10) whose "
    "app_rating is not null. The existing review mass equals 10% of customers (210,000 reviews) at "
    "4.6; when a persona reviews, 2% of the customers who follow it (f × weight_customers) leave that "
    "rating. Rounded to 2 decimals.",
    "goal_3b (CFPB complaints per month, worst month) = 120 × (1 + 4 × S), where S is the maximum "
    "over the sliding 4-week windows (weeks 1-4, 2-5, ..., 7-10) of Σ f × weight_customers of personas "
    "with complaint == \"cfpb\" in any week of that window / 2,100,000. 25% of all customers escalating "
    "to the CFPB in a month doubles the baseline of 120 a month. Rounded to 1 decimal. Board limit 240.",
    "Weights are the personas' own weight_customers (2.1 million in total) and weight_deposits_usd. "
    "A missing or invalid weight counts as 0 and is listed under notes.",
    "An incomplete run uses its last completed week in place of week 10 and only windows inside the "
    "completed weeks (fewer than 4 weeks: one window); weeks_completed says how many weeks it covers. "
    "A run with no completed weeks writes goal_1 and goal_2 as 0 with a note.",
    "by_group applies the same formulas to one dossier group's personas. goal_1 and goal_2 use the "
    "group's own Nov 2 customers and deposits as the baseline; goal_3 and goal_3b keep the bank-wide "
    "constants (210,000 reviews at 4.6; 2,100,000 customers; 120 a month), so they show the bank-wide "
    "number if only that group's personas had rated or escalated.",
]

__doc__ = (
    "metrics.json: Cobalt's board goals from recorded weekly behavior and the personas' own weights.\n\n"
    "Only model-recorded weekly fields are read (status, money, new_money, active_derived /\n"
    "active_in_last_30_days, app_rating, complaint) together with the external weights and profile\n"
    "fields in personas.jsonl. Nothing here calls a model or edits a persona's answer. Assumptions,\n"
    "written verbatim to metrics.json under \"assumptions\":\n\n"
    + "\n".join("- " + item for item in ASSUMPTIONS)
    + "\n\nRecompute an existing run without model calls: PYTHONPATH=code python3 -m sim.metrics runs/plan_1\n"
)

UNITS = {
    "goal_1": "% of Nov 2 30-day active customers (Nov 2 base = 100; follow share f per persona)",
    "goal_2": "% of Nov 2 deposits (follow share f; money kept=1.0 / moved some=0.6 / moved most=0.1 / "
              "left=0, plus new money some=0.1 / a lot=0.3)",
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


def follow_share(person):
    """Share of the customers a persona stands for who make the same move it makes."""
    rate = RATE_SENSITIVITY.get(person.get("moves_money_for_rate"), NEUTRAL_TRAIT)
    anxiety = ANXIETY.get(person.get("baseline_anxiety"), NEUTRAL_TRAIT)
    f = (FOLLOW_BASE
         + (FOLLOW_SECOND_BANK if person.get("cobalt_role") == "second bank" else 0.0)
         + (FOLLOW_PAYCHECK if person.get("paycheck_into_cobalt") is True else 0.0)
         + FOLLOW_PER_TRAIT_POINT * (rate - NEUTRAL_TRAIT)
         + FOLLOW_PER_TRAIT_POINT * (anxiety - NEUTRAL_TRAIT))
    return round(min(FOLLOW_MAX, max(FOLLOW_MIN, f)), 4)


def _active_at_start(person):
    return person.get("cobalt_role") not in INACTIVE_AT_START


def _used_app(row):
    return row.get("active_derived", row.get("active_in_last_30_days")) is True


def _is_active(row, used_app_before=True):
    # A persona that never reports an app action (e.g. only "wait and see") but stays a customer is a
    # quiet user, not a lost one: active_derived only counts against it once it has used the app.
    if row.get("status") not in ACTIVE_STATUSES:
        return False
    return _used_app(row) or not used_app_before


def _deposit_factor(row):
    if row["status"] == "left":
        return 0.0
    return MONEY_FACTOR[row["money"]] + NEW_MONEY_FACTOR.get(row.get("new_money", "none"), 0.0)


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


def _goals(ids, rows, last, customers, deposits, follow, start_ids, notes, label):
    base_active = sum(customers[pid] for pid in ids if pid in start_ids)
    base_deposits = sum(deposits[pid] for pid in ids)

    def used_app_before(pid, week):
        return any(_used_app(rows[(pid, w)]) for w in range(1, week) if (pid, w) in rows)

    def active(week):
        lost = sum(follow[pid] * customers[pid] for pid in ids
                   if pid in start_ids and (row := rows.get((pid, week)))
                   and not _is_active(row, used_app_before(pid, week)))
        return base_active - lost

    def deposits_at(week):
        change = sum(follow[pid] * deposits[pid] * (_deposit_factor(row) - 1.0) for pid in ids
                     if (row := rows.get((pid, week))))
        return base_deposits + change

    series = {week: active(week) for week in range(1, last + 1)}
    deposit_series = {week: deposits_at(week) for week in range(1, last + 1)}
    if last == 0:
        goal_1 = goal_2 = 0.0
    else:
        if base_active > 0:
            goal_1 = round(100 * series[last] / base_active, 2)
        else:
            goal_1 = 0.0
            notes.append(f"{label}: no weighted Nov 2 actives (B = 0); goal_1 written as 0")
        if base_deposits > 0:
            goal_2 = round(100 * deposit_series[last] / base_deposits, 2)
        else:
            goal_2 = 0.0
            notes.append(f"{label}: no weighted Nov 2 deposits; goal_2 written as 0")
        missing = sorted(pid for pid in ids if (pid, last) not in rows)
        if missing:
            notes.append(f"{label}: no week-{last} row for {', '.join(missing)}; counted as unchanged")

    rated = [(pid, row["app_rating"]) for (pid, week), row in rows.items()
             if pid in ids and 1 <= week <= last and row.get("app_rating") is not None]
    mass = sum(REVIEW_SHARE * follow[pid] * customers[pid] for pid, _ in rated)
    score = sum(REVIEW_SHARE * follow[pid] * customers[pid] * rating for pid, rating in rated)
    goal_3 = round((BASE_RATING * REVIEW_MASS + score) / (REVIEW_MASS + mass), 2)

    shares = {}
    for start, end in _windows(last):
        escalated = [pid for pid in ids
                     if any(rows.get((pid, week), {}).get("complaint") == "cfpb" for week in range(start, end + 1))]
        shares[f"{start}-{end}"] = sum(follow[pid] * customers[pid] for pid in escalated) / CUSTOMERS
    worst = max(shares.values(), default=0.0)
    goal_3b = round(CFPB_BASELINE * (1 + 4 * worst), 1)

    goals = {"goal_1": goal_1, "goal_2": goal_2, "goal_3": goal_3, "goal_3b": goal_3b}
    detail = {"active_customers_weighted": {str(week): round(value, 1) for week, value in series.items()},
              "deposits_weighted_usd": {str(week): round(value, 1) for week, value in deposit_series.items()},
              "goal_1_by_week": {str(week): round(100 * value / base_active, 2) if base_active else 0.0
                                 for week, value in series.items()},
              "goal_2_by_week": {str(week): round(100 * value / base_deposits, 2) if base_deposits else 0.0
                                 for week, value in deposit_series.items()},
              "cfpb_share_by_window": {key: round(value, 6) for key, value in shares.items()},
              "rated_persona_weeks": len(rated)}
    return goals, detail


def compute_metrics(personas, weekly_rows):
    """Pure function: external personas (with weights) and weekly.jsonl rows -> metrics.json dict."""
    notes = []
    customers = _weights(personas, "weight_customers", notes)
    deposits = _weights(personas, "weight_deposits_usd", notes)
    follow = {p["id"]: follow_share(p) for p in personas}
    start_ids = {p["id"] for p in personas if _active_at_start(p)}
    rows = {(row["persona"], row["week"]): row for row in weekly_rows
            if type(row.get("week")) is int and 1 <= row["week"] <= 10}
    last = max((week for _, week in rows), default=0)
    if last == 0:
        notes.append("no completed weeks; goal_1 and goal_2 written as 0")
    all_ids = {p["id"] for p in personas}
    goals, detail = _goals(all_ids, rows, last, customers, deposits, follow, start_ids, notes, "all")
    by_group = {}
    for group in sorted({p["group"] for p in personas}):
        ids = {p["id"] for p in personas if p["group"] == group}
        group_goals, _ = _goals(ids, rows, last, customers, deposits, follow, start_ids, notes, group)
        by_group[group] = {**group_goals, "personas": len(ids),
                           "weight_customers": sum(customers[pid] for pid in ids),
                           "weight_deposits_usd": sum(deposits[pid] for pid in ids)}
    return {**goals, "units": UNITS, "board_targets": BOARD_TARGETS, "weeks_completed": last,
            "assumptions": ASSUMPTIONS, "follow_share": follow, "by_group": by_group, "series": detail,
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
