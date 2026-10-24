# Roadmap — today, Oct 24 (written at 11:10)

Goal: a working end-to-end simulation **before 13:00**, experiments while the calendar runs, both
decisions locked in time, and a hand-in that passes `check.py` **by 17:50**.

## Hard deadlines

| Clock | Deadline |
|---|---|
| 13:00 | Calendar starts (week 1). Pipeline should already run end to end |
| W start | A decision for week W must be locked **before** that week starts (table below) |
| 17:30 | Last moment to lock or replace any decision; week 10 may bring a last announcement |
| 18:00 | ZIP uploaded. **Our target: 17:50** |
| 18:30 | Board presentation |

| Decision for week | 1 | 2 | 3 | 4 | 5 | **6 (migration)** | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Lock before | 13:00 | 13:30 | 14:00 | 14:30 | 15:00 | **15:30** | 16:00 | 16:30 | 17:00 | 17:30 |

**Rule we use:** a locked decision can be replaced until its week starts. So we lock a reasonable
version of both decisions early (never miss a deadline) and replace them as the experiments improve.

---

## Phase 0 — Agree on contracts (11:10–11:30)

Everything else runs in parallel once these are fixed. One person / one agent, on
`agent/sim-skeleton`, merged fast.

- [ ] Pick the model (recommended: `gemini-3.5-flash-lite`)
- [ ] Pick the groups we simulate (recommended: all five, 6–8 personas each → 30–40 personas)
- [ ] `code/sim/` module layout with empty functions and docstrings
- [ ] Data contracts, written down in `code/sim/README.md`:
  - persona record (`id`, `group`, `weight_customers`, `balance`, attributes, narrative)
  - per-persona weekly state (`status`, `money`, memory, actions taken)
  - weekly LLM output (JSON: what they saw, how they feel, actions, `status`, `money`, last line `Status: ...`)
  - decision file = the `decisions` list from `run.json`
  - surprise file: `{id, week, text, update: {week, text}}`

## Phase 1 — Build in parallel (11:30–12:30)

One branch per workstream (see [`AGENTS.md`](../AGENTS.md)). Each can be one person or one agent.

| # | Workstream | Branch | Builds | Done when |
|---|---|---|---|---|
| A | LLM client | `agent/llm-client` | `sim/llm.py`: reads `TALP_KEY`, async parallel calls with a concurrency cap, `seed` + temperature, JSON schema output, retries, logs every call to `calls.jsonl` (`id`, `persona`, `week`, `prompt`, `response`, `model`) | 50 parallel calls finish and are logged |
| B | Personas | `agent/personas-v1` | `code/personas/spec.md` (attributes used / left out and why, distributions, data sources) + generator → frozen `personas.jsonl` with weights | ≥ 24 personas, ≥ 4 per group, weights add up to 2.1M customers and $6.0B deposits (5% hold half) |
| C | World engine | `agent/world-engine` | Weekly loop: what each persona sees (BAU messages, our decision message word for word if targeted and week ≥ decision week, crisis news, social feed, friends, support wait, rival offers), what they can do, how state carries to next week | One persona lives through 10 weeks with a coherent memory |
| D | Crises | `agent/crises-config` | Known migration crisis in config, surprise files in `code/config/surprises/`, a `--no-surprises` switch | `plan_nosurprises` prompts differ from `plan_1` |
| E | Decisions & budget | `agent/decisions-budget` | Validator for `plan.json`: menu actions and levels only, total ≤ $4M incl. SMS, ≤ 600 chars, 1–3 actions; candidate decision files | Over-budget or off-menu file is rejected |
| F | Metrics | `agent/metrics` | `weekly.jsonl` → `goal_1` (active %), `goal_2` (deposits %), `goal_3` (App Store rating), `goal_3b` (CFPB complaints/month) + `units` | A "nothing happens" run reads ≈ 100% / 100% / 4.6 / 120 |

## Phase 2 — Integrate and prove it end to end (12:30–13:00)

Branch `agent/runs-pipeline`.

- [ ] `run.py --type plan|nodecision|plan_nosurprises --seed N --out runs/<name>` writes all six files
- [ ] Probe: 8 check-in questions per persona at week 0 and week 11 in `plan_1` and `nodecision_1`
- [ ] `run_all.sh`: the five runs in parallel
- [ ] Smoke test: 8 personas × 3 weeks, then full size
- [ ] `code/scripts/make_submission.sh 07` → "Nothing to fix."
- [ ] **Measure the full five-run time.** Must be well under 15 minutes (weeks are sequential inside a run; personas and runs are parallel)

## Phase 3 — Calendar running: watch, experiment, lock decision 1 (13:00–15:30)

- [ ] **Dashboard watcher** (one person): at 13:00, 13:30, 14:00 … copy every announcement word for
  word into `docs/crisis-log.md` and a surprise file; write how we read it
- [ ] Experiments in `experiments/` (2 seeds each), logged in `docs/experiments.md`:
  no decision vs. candidate decisions at different weeks
- [ ] Sanity check: no crisis should make half the customers leave in a week; if it does, fix the sim
- [ ] Lock a first version of **both** decisions early; refine by replacing
- [ ] Decision aimed at the migration: final version locked **before 15:00 (week 5) or 15:30 (week 6)**

## Phase 4 — Migration and aftermath: decision 2, docs, demo (15:30–17:30)

- [ ] Keep the second decision flexible for surprises; final version before its week starts (≤ 17:30)
- [ ] Copy the exact locked text into `code/config/decisions/plan.json`
- [ ] Persona interview tool (`agent/tools-interview`): ask any persona a question live, with its memory
- [ ] Draft `TEAM_DOC.md` and `CLIENT_MEMO.md` (`agent/docs-memos`)
- [ ] **Dress rehearsal ~17:00:** full five runs + ZIP + `check.py`, time it

## Phase 5 — Final runs and hand-in (17:30–18:00)

- [ ] 17:30: log the week 10 announcement (if any) → surprise file
- [ ] Run all five (`agent/runs-final-1730`), recompute metrics, update memo numbers
- [ ] `code/scripts/make_submission.sh 07` → "Nothing to fix."
- [ ] **Upload `team-07_submission.zip` by 17:50**

## Phase 6 — Presentation prep (18:00–18:30)

5 minutes + 3 minutes of questions. The jury scores:
1. reasoning ("why" for every choice)
2. an idea of our own
3. how we compared approaches and what we learned (from `docs/experiments.md`)
4. a working example — the board picks a persona and asks it a question live → interview tool ready
5. what the simulation cannot tell yet, and what we would do next

---

Design choices borrowed from prior work (memory, social feed, game master, structured calls, what to
trust) are in [`prior-art.md`](prior-art.md).

## Open decisions for the team (now)

1. **Model** — recommended `gemini-3.5-flash-lite` (~1 s per call).
2. **Groups and persona count** — recommended all five groups, 30–40 personas.
3. **Our own idea** — candidates:
   - a social network between personas: what one posts or tells friends reaches others next week
   - rivals actively poaching during the migration weekend (they know the date)
   - deposit-weighted personas that mirror "5% hold half the deposits"
4. **Decision timing** — one decision before the migration and one held back for surprises, or both
   before the migration.

## Hypotheses worth testing in the experiments

- Paycheck customers paid on Friday, Dec 11, then frozen for 36+ hours: who feels it most, and what
  calms them?
- Large-balance savers drive goal 2: do they react more to the rate gap or to the migration risk?
- Card-reader businesses lose sales above the $100 offline limit: how much does that move complaints
  and reviews?
- Does silence (business as usual: email 7 days before) cost more trust than an early, honest message?
