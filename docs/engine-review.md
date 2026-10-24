# Engine review — `omer/world-engine` @ 5390d5f (Oct 24, 13:05)

Two reads (mine and an independent Opus review), the unit tests, and four live smoke runs against
Vertex with the 24 real personas: 2, 6 and 7 weeks without decisions, and 7 weeks with a test plan.
Outputs are in `experiments/smoke-*` (git-ignored). The organizers' `check.py` was run on the
7-week plan and no-decision outputs.

## Verdict in one paragraph

The plumbing is solid and checker-safe: every call logged, status traceable, decision messages
delivered word for word to the right people from the right week and nowhere else, seeds reproducible,
budget and menu validated, 24-wide concurrency works (168 calls in ~15 s, 0 invalid, 0 rate limits).
But the **simulation is inert**: across 7 weeks, plan and no-decision runs are nearly identical
(20 main / 4 second bank every week, 0 complaints, 0 reviews, 0 posts, 0 second-round calls). Nobody
talks because the persona network is never loaded, and nobody reacts to the migration because the
world never tells a persona what happened to *them* — so the model invents "it went fine". Two
required hand-in files (`probe.jsonl`, `metrics.json`) are not produced at all.

## What the smoke runs showed

| Run | Calls | Invalid | Wall time | Messages | Round-2 calls | Plan vs nodecision difference |
|---|---|---|---|---|---|---|
| 2 weeks, no decisions | 48 | 0 | 34 s (one 24 s straggler) | 0 | 0 | – |
| 6 weeks, no decisions | 144 | 0 | 15 s | 0 | 0 | – |
| 7 weeks, no decisions | 168 | 0 | ~18 s | 0 | 0 | week 7: 22 kept / 1 some / 1 most |
| 7 weeks, test plan (wk 5 + wk 7) | 168 | 0 | ~18 s | 0 | 0 | week 7: 22 kept / 1 some / 1 most — same |

`check.py` on the plan run: "decision 1: message reaches 24 personas word for word from week 5",
"decision 2: message reaches 6 personas from week 7", "every weekly status comes from a model
answer", same personas across runs, same decisions across plan runs. All FIX lines were only the
missing probe/metrics/weeks. **Same seed → byte-identical responses** across two runs (144/144), so
the seed mechanism is real; the second-seed runs must use a different `--seed`.

Sample week-7 reasoning after the migration, with no world feedback: B4 "my Sunday stylist payouts
went through just fine once the system opened back up"; P1 "rent autopay went through fine". The
model is asked not to invent outcomes, then given none, so it invents the kindest one.

## What is good (keep)

- **Paired comparisons by design.** Exposure draws are seeded hashes independent of async order;
  Gemini honors the seed; plan and nodecision runs are identical until the decision week. This is
  exactly what makes `plan − nodecision` a clean delta.
- **Leak protection in three layers:** prompt guard (message outside its week/audience raises),
  6-gram quote filter on peer messages, BAU notices checked against the locked message.
- **Honest logging:** every attempt logged including failures, key redaction on write, no scripted
  status ever substituted.
- **Menu/budget validation** incl. SMS cost, recipient caps, durations; `run.json` carries the locked
  list unchanged.
- **Bounded spread:** two rounds per week with an inbox cap — the same-week interaction we wanted,
  without cascades.
- **Speed:** ~1.7 s per call average; a 10-week run is ~30 s. Five runs fit in minutes.

## Findings, ranked

### A. Blocks the hand-in

1. **No `probe.jsonl`, no `metrics.json`.** `check.py` stops checking a run when a file is missing,
   so every run shows FIX and hides everything else. Need `sim/probe.py` (8 questions × 2, weeks 0
   and 11, `plan_1` and `nodecision_1` only, raw scores) and `sim/metrics.py` (`goal_1..goal_3`,
   `goal_3b`, `units`).
2. **No five-run driver.** Default seed is 42 everywhere; without a driver that fixes seeds (plan_1 =
   nodecision_1 = 1, plan_2 = nodecision_2 = 2) and requires `--surprises`, the checker's
   "identical answers between seeds" and "plan_1 and plan_nosurprises send the same prompts" lines
   are one forgotten flag away. `code/config/surprises/` is empty today.
3. **Abort-on-DM risk.** The persona JSON (with `neighbors: ["P2", …]`) goes into the prompt, but the
   engine's contact list comes only from `--network`, which we never pass. If the model messages
   "P2", `schema.py:84` rejects it, three attempts fail, `engine.py` aborts the whole run, and the
   output folder cannot be resumed. It did not happen in the quiet smoke runs; it will in a crisis
   week.

### B. Makes the simulation say nothing

4. **The network is not wired.** `neighbors`, `wave`, `influence` from `personas.jsonl` are ignored;
   `contacts: []` in every prompt. Zero peer messages in 528 calls. The "idea of our own" does not
   exist in the runs yet. Need a converter `personas.jsonl → network.json` (in-group edges → follows
   both ways, bridges → close_friends, 3–4 WhatsApp groups: family chat P1/P5/E4, vendors B1/B5/B3,
   salon B4 + stylists…).
5. **No consequences.** The world states the schedule but never resolves what happened to each
   persona: did Rosa's Sunday rent autopay execute, did Karen's Sunday P2P payouts fail, did Jamal's
   $300 ticket bounce on a $100 limit, did the overrun happen. A deterministic per-persona
   "what happened to you this week" block (from persona attributes × world facts × active effects)
   is the missing game-master-as-table. Without it, decision effects cannot differ from BAU because
   nobody experiences either.
6. **Prompt pushes inertia.** `prompt.py:11-12` ("An inconvenience does not automatically cause
   switching… doing nothing and being satisfied are valid") plus a long list of "do not" rules.
   Combined with 5, the model picks "wait and see" 23/24 times even in week 7.
7. **Everyone reads every announcement** (`world.py:59,71`): all 24 see every surprise verbatim.
   "Who hears about it" is supposed to be our simulation's job. Fix: announcements reach a persona
   via their channels (bank email → everyone with `checks_app_daily`/reads email; social → by
   `news_sources`; otherwise only through peers).
8. **No calendar.** Prompt has `"week": 6` only; P1 assumed a Friday paycheck in week 2. Add
   week → dates, and per-persona "your payday this week is …".
9. **Persona JSON dumped whole** (~3.3 KB): `weight_customers`, `weight_deposits_usd` ($144M for
   Rosa), `wave`, `neighbors`, `actions_available`, and the bank's internal KPIs (`baseline`: CFPB
   120/month, 1.0M actives) all land in the customer's information set. Render a first-person
   profile (narrative + voice + the ~15 crisis-coupled attributes) and drop the rest.
10. **Raw effect dicts in the prompt** (`{"extra_support_staff": 150}`, `recipient_cap`). Render
    as customer experience: "support answered in about 2 minutes this week", "your card worked up
    to $250 at checkout during the migration".
11. **No rival action.** Dossier: "rivals know the date". Nothing in `world.json`. Add a week-5/6
    event: a rival's higher-rate "switch before Dec 12" offer, visible through `news_sources`.
12. **Model-owned numbers.** `balance` and `active_in_last_30_days` are self-reported; the model
    already moved S1 from $350k to $250k on its own. Metrics must not use `balance`; use `money` ×
    `weight_deposits_usd`.

### C. Fragile mechanics

13. **Round-2 action strings must be an exact superset** (`schema.py:87`): a rephrase ("logged in
    and checked balance") fails validation and can abort. Merge lists instead.
14. **One failure kills the run; no resume.** SDK retries disabled, backoff 1–2 s, 3 attempts; a
    429 burst at 24-wide can exhaust a persona. Raise attempts to 5, backoff to 2–8 s, allow
    `--resume` from `state.json`.
15. **Recipient caps use full persona weights** (`decisions.py:132`): the 20k advance cap excludes
    every paycheck persona (40–60k each); goodwill to "paycheck customers" (310k) is rejected. The
    menu says "a group you define, up to 100,000": need partial reach — a seeded per-persona draw
    "you were / were not among the N customers who received it", and metrics scaled by cap/group.
16. **Channel and level spelling must match the engine** (`"in-app"`, `"+150"`); dashboard wording
    may differ. Extend `--action-aliases` to channels and levels so the locked text is never edited.
17. **Metrics scale is coarse:** E1 alone is 19% of customers; S4 and S5 are 10% of deposits each.
    One flip swings a goal by more than its tolerance. Report deltas with both seeds, say so in the
    memo, and never map `complaint: cfpb` × weight to a count (one E1 complaint = 400k complaints
    vs a 240 limit): calibrate complaint intent to the 120/month base rate.
18. `heard_from` and `actions` are free strings → hard to aggregate. Enums (bank / friend / rival /
    news / none; a fixed action list — personas already carry `actions_available`).
19. Statuses unconstrained week to week (`left` → `main bank`, `left` + `money: kept`). Add a
    prompt line and a soft check.

## Recommended order (clock: 13:05; decision 1 locks before 15:00)

| # | Change | Files | Why first |
|---|---|---|---|
| 1 | `probe.py` + `metrics.py`, hooked into `run()`; `run_all.sh` with fixed seeds and required `--surprises` | `sim/probe.py`, `sim/metrics.py`, `sim/engine.py`, `code/scripts/run_all.sh` | Without these every run is a FIX; everything else is invisible to the checker |
| 2 | Network converter + prompt renderer (strip weights/neighbors/KPIs, add contacts by name, calendar dates, per-persona payday) | `code/personas/export_network.py`, `sim/prompt.py`, `config/world.json` | Removes the abort-on-DM risk and turns on the feed and round 2 |
| 3 | Per-persona weekly consequences block + rendered effects + rival event + announcement reach by channel | `sim/world.py`, `sim/prompt.py`, `config/world.json` | This is what makes plan ≠ nodecision; needed before any experiment means anything |
| 4 | Soften inertia instructions; enums for `heard_from`/`actions`; merge round-2 actions | `sim/prompt.py`, `sim/schema.py` | Cheap; unblocks reactions and aggregation |
| 5 | Retries/backoff/resume; partial reach for capped offers; alias channels/levels | `sim/llm.py`, `sim/settings.py`, `sim/decisions.py` | Survivability for the 17:30 re-run |

Items 1–2 are ~40 minutes; 3 is the real modeling work (~45 minutes) and should run as its own branch
while 1–2 land. Experiments before 3 lands will show nothing, so lock a *placeholder* decision 1
by 14:30 regardless, and replace it once 3 is in.

## What to tell the board (unchanged by this review, sharpened)

- Deltas, not levels; two seeds; 24 personas cannot resolve a 2% goal (one persona ≈ 4–19%).
- Complaint and rating numbers are stated intent calibrated to the base rate, not counts.
- Network topology and exposure probabilities (5/35/65/80%) are assumptions; the feed-off ablation
  shows how much they matter.
