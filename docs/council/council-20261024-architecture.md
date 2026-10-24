# Council — 2026-10-24 — Simulation architecture, persona communication, roadmap

Session run 11:43–12:02, Oct 24. Five advisors in parallel → anonymized peer review → chairman
synthesis. HTML report: [council-report-20261024-1200-architecture.html](council-report-20261024-1200-architecture.html).

## Raw question (user, verbatim)

> bu hackathon için nasıl sistemler kurulmalı personalar nasıl iletişime geçmeli ve genel roadmapimiz ne olmalı teknik ayrıntılarıyla çıkar

## Framed question

**The fork.** A small team (one human + AI coding agents on separate branches) has until 18:00 today to
build an LLM persona simulation for the TALP hackathon (client: Cobalt Bank) and must decide now the
architecture it commits to:

1. **Persona design and communication** — how personas are built, and whether/how they talk: (a) no
   interaction; (b) a one-week-lag social feed over a fixed network, zero extra calls; (c) a per-week
   "what's trending" digest call on top; (d) pairwise dialogues.
2. **World engine shape** — an LLM "game master" resolving actions vs. plain deterministic prompt assembly.
3. **LLM call structure** — one structured call per persona-week vs. several; rolling-summary vs.
   full-history memory; caching.
4. **Roadmap sequencing** — build order, cuts, lock timing, surviving a late announcement.

Context given to every advisor: the full task rules, clock (13:00 start, 30 min = 1 week, last lock
17:30, hand-in 18:00, live persona Q&A at 18:30), hand-in formats and every `check.py` rule, the known
week-6 migration crisis, the decision menu and $4M cap, board goals, persona rules (≥24, ≥3 groups,
≥4 each), model timings measured today, jury criteria, prior-art findings, and the draft roadmap
(noting Phase 0 was already late with no code at 11:43).

---

## Advisor responses

### The Executor (anonymized as A)

Commit now to the thing that runs: one JSON call per persona per week, option (b) feed with one-week lag, no LLM game master, no dialogues, no digest. Math: 30 personas × 12 calls (weeks 1–10 + two probes) × 5 runs = 1,800 calls on gemini-3.5-flash-lite at ~1s, concurrency 30, runs in parallel → the whole hand-in regenerates in ~3 minutes. That is your late-announcement insurance; nothing else is.

Next 20 minutes (11:45–12:05), human only: write `code/sim/schema.py` (persona record; weekly output JSON: `feel`, `actions[]`, `post` ≤140 chars, `status` ∈ the four literal strings, `money`, `memory` ≤3 lines) and `code/sim/prompt.md` (system = narrative + attributes; user = week N facts + decision message verbatim if targeted and week ≥ W + up to 4 neighbor posts from week N‑1 + own memory). Then launch three agents, not six: A `agent/core` builds `llm.py` (async google-genai, seed+temp, schema output, every call appended to `calls.jsonl`), `world.py` (`build_prompt`), `network.py` (seeded fixed graph, 4 neighbors, same-group bias), `run.py --type --seed --out`; B `agent/personas` writes 30 personas (6/group, weights summing to 2.1M/$6.0B, 5% holding half) as `personas.jsonl` plus a one-paragraph `spec.md`; C `agent/metrics` writes `metrics.py`, `run_all.sh`, and loops `check.py` on fixture output until clean.

12:05–12:35 merge, smoke 8×3. 12:35–13:00 full five runs, `make_submission.sh` → "Nothing to fix", and at 12:55 lock a placeholder decision (week 5, everyone, honest pre-migration message + offline limit $250) so no deadline is ever missed. 13:00–15:30 experiments by swapping `plan.json`, two seeds each. 15:30 `interview.py` = `build_prompt` + one call with the persona's week‑10 memory; that is the live demo. 17:00 dress rehearsal with a fake week‑10 surprise file to time the re-run. 17:32 final runs, 17:45 upload.

Cut: pairwise dialogues, trending call, LLM game master, full-history memory, caching layer, Census grounding beyond one sentence, any UI, more than 30 personas.

### The Contrarian (anonymized as B)

What kills you is not persona design; it is that at 11:43 no code exists and the roadmap has six branches merging at 12:30. That merge will not happen. Build one vertical slice first in a single process — client, prompt builder, 24 stub personas, five runs, check.py green — then widen. And measure 24-wide parallel throughput on the key now: per-call latency was tested, concurrency quota was not. A crisis announced at 17:30 forces a cold five-run re-run inside 30 minutes; at a 60 RPM quota, ~1,500 calls take 25 minutes and the ZIP is late.

The checker bites in three places. One: any "realistic delivery" modeling (persona ignored the push) removes the message from a targeted prompt and fails word-for-word. The message always goes in verbatim; attention is a persona attribute. Two: a social feed whose posts quote the message makes check.py print "reaches 24 personas" on a targeted decision — cap posts at ~140 chars of the persona's own words. Three: a TinyTroupe-style cache keyed on prompt hash returns identical plan_1/plan_2 answers and fails the seed check; key on (run, seed, prompt) and isolate each run's memory by directory, or nodecision inherits the message.

Third: the feed is the contagion engine that produces "half leave in a week," which the organizers call a broken sim. Run nodecision in a quiet world first; if more than one persona leaves, your prompts are the crisis. Encode switching friction in the prompt (moving direct deposit takes a pay cycle). Skip (c) digest and (d) dialogues — identical text to all 24 homogenizes — and skip the game master; it hallucinates facts that contradict announcements.

Last: 24 personas cannot resolve a 2% goal; one persona is 4%. Weight personas by segment, report deltas versus nodecision, and admit it under "what the sim cannot tell." Keep decision two as an unlocked reserve. Use full own-history, not a rolling summary, and inject the persona's own weekly.jsonl rows as hard facts — the live board question will expose any contradiction.

### The Outsider (anonymized as C)

Read the brief as a stranger and one thing jumps out: the deliverable is two decisions, a five-minute talk, and one persona answering a board member live. Nothing in the jury list says "feed topology" or "game master". The insiders are arguing about plumbing nobody will see.

What a board member wants the simulation to show is embarrassingly simple: a picture of ten weeks, two lines (with our plan, without it), four colours (main, second, dormant, left), and a finger on week 6 saying "this is the migration weekend, this is what we did, this is the gap it bought." Then one face: "This is Rosa, a nurse paid Friday Dec 11, rent due Saturday, app read-only. Ask her what happened." If Rosa cannot describe her own December 12 in concrete words, the whole thing collapses on stage. So the one piece of memory that must exist is a short per-persona diary she carries into every week and into the live Q&A. Build that before anything else.

On talking to each other: any normal person knows the neighbour says "the bank app is down" before the bank does. That is option (b), and it explains itself in one sentence: "each week, every persona sees three things people they know said last week." Dialogues (d) are invisible to a jury and unexplainable in five minutes; the trending digest (c) is a feature you add at 15:00 if bored. Cut them now.

The "game master" sounds mysterious; what it actually means is "someone must say what happened to each person this week: paycheck landed, migration overran." That is a table of facts per week, not another LLM.

Missing: write the three-line "why" for both decisions by week 3 and keep improving it; do not leave the story for 17:50. And the organizers already told you the answer shape: small movements. Show differences between options, not dramatic numbers.

### The Expansionist (anonymized as D)

Build the information network. It is the only part of this task that can become "an idea of our own," and it costs zero extra LLM calls. Each persona's weekly JSON call already has to return status and money; add two fields: `post` (optional, ≤280 chars) and `diary` (three self-written sentences, the rolling memory). Route posts over a fixed graph built at persona-creation time: dense cliques for students, hub-and-spoke for small-business owners, sparse ties for savers, plus three or four deliberate bridge nodes. Next week's prompt carries the neighbors' posts and the persona's own diary. That turns a questionnaire into a contagion model: the board watches the migration rumor reach people who never open the app.

Add two cheap null-persona calls per week: a "trending" digest (one call turning all posts into three headlines everyone sees) and a game master that converts aggregate outputs into next week's world facts: support wait rising from 4 to 11 minutes when 30% say they called, a rival's "switch before Dec 12" post injected in week 5 because rivals know the date. Eleven extra calls per run. Nothing.

The real ceiling is using the sim before locking. At 13:30 run four candidate decision bundles as extra runs (flash-lite, 32 personas, concurrency 24, about 90 s per run, disk-cached by prompt hash) plus a no-network ablation, and show the board the comparison table. That is "approaches compared" and "what we learned" in one artifact: "with the feed, 41% hear about the outage before the bank's email; the personal reassurance message with a concrete commitment cuts movers by X points." Then the live Q&A: an interview tool that loads the persona's week-10 diary and the posts it saw, so when asked why it moved money it names the neighbor who told it.

Roadmap: feed in the core by 12:30, digest and game master by 13:00, decision experiments 13:30–15:00, interview tool and contagion map by 16:00.

### The First Principles Thinker (anonymized as E)

Strip the framing: architecture is not scored. check.py scores the ZIP; the board scores a five-minute argument plus one live persona. So the real decision is: what is the smallest function f(persona, week facts, seed) → {status, money, post, memory} that passes check.py, yields a plan-minus-nodecision delta we can defend, and answers a live question with the same prompt? Everything else is decoration bought with the one scarce resource — minutes before 13:00. Compute is free: 24×10×5 = 1,200 calls at ~1 s, 24-wide parallel, one barrier per week, roughly 3 minutes for all five runs.

Therefore: one JSON-schema call per persona-week on gemini-3.6-flash with thinking off (fallback 3.5-flash-lite), fields status, money, post ≤140 chars, reason, memory ≤3 lines. Memory is the persona's own output carried forward — no summarizer call, no full history (which homogenizes). The world engine is deterministic bookkeeping, not an LLM game master: a per-week dict (rate, support wait with/without +150, offline card limit, migration state including overrun, rival emails) rendered into the prompt. Interaction is option (b) only: a fixed small-world graph, k≈4 within group plus one cross-group edge, last week's neighbor posts pasted in. Zero extra calls — and it is the idea of our own: trust depends on who told you first, bank, rival, or friend. Dialogues and digests cost calls and earn nothing.

Attributes by mechanism, not catalog: only three couple to this crisis — balance above the FDIC limit, paid Friday Dec 11, has a second bank. The rest is one generated narrative paragraph. Report deltas, never levels.

Roadmap: 11:45–12:30 vertical slice, check.py green on one run. 12:30–13:00 five timed runs plus a feed-on/off ablation — that is the "approaches compared" criterion. Lock a week-5 targeted message and week-6 offline limit plus support early, replace freely. The interview tool is the runner with a question appended; done by 15:00. Cut digest, dialogues, more than 30 personas, slides.

---

## Anonymization mapping used in peer review

A = Executor · B = Contrarian · C = Outsider · D = Expansionist · E = First Principles

## Peer reviews (reviewers saw letters only)

### Reviewer 1
**Strongest: B.** The only response that tests the consensus design against the brief's failure modes: three check.py traps (verbatim delivery, feed posts rebroadcasting the message, prompt-hash cache breaking the plan_1/plan_2 seed check), the untested concurrency quota behind a 17:30 cold re-run, the organizers' "half leave = broken" warning, and 24-persona resolution as "what the sim cannot tell." E and A execute better; B is what keeps them from failing.
**Biggest blind spot: D.** It builds for the jury story and straight into the checker: a disk cache keyed on prompt hash (identical seeds), a digest rebroadcasting post text to everyone, an LLM game master inventing world facts that can contradict dashboard announcements — all due by 13:00 from zero code. C also ignores the checker, but its minimal plan cannot fail it.
**All five missed:** metrics.json requires goal_3 (App Store) and goal_3b (CFPB complaints); no proposed schema has a rating or complaint field. Nobody defines the business-as-usual baseline (migration email seven days prior, holding statement) that nodecision must still contain — the real delta is plan-vs-BAU, and BAU wording must not collide with the decision message. Nobody prices a bundle against the ≤$4M joint cap, and "left" personas still need weekly lines through week 10.

### Reviewer 2
**Strongest: E.** It builds from what is scored: one schema call per persona-week, deterministic world dict (covers the overrun update), feed-only interaction as "idea of our own", feed-on/off ablation as "approaches compared", deltas not levels, same prompt reused live. Its flaws (five runs plus ablation by 13:00 from zero code, no decision in reserve) are fixed by borrowing A's clock discipline (placeholder lock 12:55, 17:00 cold re-run rehearsal, final runs 17:32) and B's checker traps.
**Biggest blind spot: D.** "Disk-cached by prompt hash" makes plan_1 and plan_2 identical and fails the seed check; LLM game master plus everyone-sees digest is the homogenizing contagion engine that yields the "half leave in a week" sim organizers call broken. D never mentions check.py or the 30-minute re-run.
**All five missed:** (a) metrics.json needs goal_3/goal_3b, yet no proposed schema has a reviewed/complained field — two of four board goals have no LLM-produced source; (b) no policy for invalid or failed calls, though the checker needs the status literally in a response and prior art warns defaults bias results; (c) nodecision is not silence — BAU sends the week-5 migration email, so the plan delta is message quality versus BAU.

### Reviewer 3
**Strongest: A.** The only complete, clock-shaped plan: counts probe calls (12/persona), ~3-minute full regeneration as late-announcement insurance, placeholder lock at 12:55, fake-surprise rehearsal at 17:00, 17:32 final runs, no cache, literal status strings. Graft in B's three checker traps and B's untested concurrency quota, the one risk that makes the ZIP late.
**Biggest blind spot: D.** "Disk-cached by prompt hash" returns identical plan_1/plan_2 answers and fails the seed check outright; an LLM game master authoring world facts makes plan-vs-nodecision deltas unattributable and can contradict announcements; and it schedules digest plus game master for 13:00 when nothing exists at 11:43.
**All five missed:** metrics.json requires goal_3/goal_3b, yet no proposed weekly schema has a review/complaint field, so those numbers would be scripted. Nobody designs probe.jsonl (8 questions, weeks 0/11, plan_1 and nodecision_1 only), validates the $4M cap and menu levels, or notes that a "reserve" second decision still must be locked before 17:30.

### Reviewer 4
**Strongest: E.** It derives the architecture from what is actually scored: one schema call per persona-week on the fastest tested model, memory as the persona's own carried-forward output, a deterministic world dict instead of an LLM game master, a zero-call lagged feed framed as the "idea of our own", attributes chosen by crisis mechanism (FDIC limit, Friday payday, second bank), deltas not levels, and a feed-on/off ablation that satisfies "approaches compared". A is the best execution plan and should supply E's timeline.
**Biggest blind spot: D.** Its prompt-hash disk cache returns identical answers for plan_1/plan_2 and fails the seed check; an LLM game master invents world facts that can contradict dashboard announcements; 280-char posts can carry the verbatim message into non-targeted prompts; and digest+GM are scheduled by 13:00 with no check.py-green milestone when no code exists.
**All five missed** metrics.json goal_3/goal_3b: no proposed JSON schema asks whether the persona would rate the app or file a (CFPB) complaint, so those figures would be scripted. Nobody designs probe.jsonl's eight week-0/week-11 questions either (E's call math omits them).

### Reviewer 5
**Strongest: A.** Same zero-extra-call architecture as E, but A alone closes the clock end to end: three agents not six, placeholder decision locked 12:55, probes counted in the call budget, no cache, a 17:00 rehearsal of the week-10 surprise re-run, final runs 17:32. Bolt on B's quota test and verbatim-message rule, plus E's deltas-not-levels and feed ablation.
**Biggest blind spot: D.** "Disk-cached by prompt hash" returns identical answers to identical prompts (week-0 probes, all of week 1), failing the plan_1/plan_2 seed check, and D never mentions check.py. Its LLM game master and digest push the same invented facts to every persona; "eleven extra calls" is really twenty. Runner-up: E locks both decisions on weeks 5–6, leaving nothing for a surprise in weeks 6–9.
**All five missed:** metrics.json requires goal_3 and goal_3b, yet every proposed weekly schema emits only status/money/post/memory, no review or complaint intent, so two of four board goals would be scripted, not simulated. Also nobody keeps the business-as-usual migration email in nodecision, so the plan-minus-nodecision delta is inflated.

---

## Chairman synthesis

### Where the council agrees

Four of five advisors (A, B, C, E) and all five reviewers converge on the same core, and it is correct: one JSON-schema call per persona per week; interaction is option (b) only, a fixed seeded graph with a one-week post lag and zero extra calls; the world engine is a deterministic per-week facts table, not an LLM; memory is the persona's own short diary carried forward; no dialogues, no digest; gemini-3.5-flash-lite or 3.6-flash-thinking-off, 30-wide parallel, so all five runs regenerate in minutes; report deltas versus nodecision, never levels; the live interview is `build_prompt` plus a question, not a separate system; lock early, replace freely; cut UI, slides, Census, and persona counts above 30. The lagged feed is the "idea of our own": who told you first, bank, rival, or friend. This is high-confidence.

### Where the council clashes

1. **D versus everyone on the digest and LLM game master.** D's instinct is right (support wait should respond to load; the rumor should visibly spread) but the mechanism is wrong: an LLM authoring world facts can contradict dashboard announcements, makes plan-minus-nodecision unattributable, and a digest everyone reads is the homogenizing contagion engine that produces "half leave in a week". Resolution: keep D's feedback loop as deterministic bookkeeping (next week's support wait is a function of how many personas reported calling support), keep D's `heard_from` idea as a schema field.
2. **Memory: B's full own-history versus the diary.** B's reason is the best one anyone gave: the board question will expose a persona contradicting its own week-6 status. The others are right that full transcripts homogenize and bloat. Resolution: a three-sentence LLM diary plus a deterministic ledger of the persona's own prior (week, status, money) rows injected as hard facts. Hybrid, and cheap.
3. **Cache.** D wants a prompt-hash disk cache; it fails the plan_1/plan_2 seed check outright. No cache on the hot path; a three-minute re-run is cheaper than a correct cache.
4. **Lock both early (E, A) versus a reserve (B).** B wins with Reviewer 3's correction: a reserve is still a decision that must be locked before its week starts, and nothing locks after 17:30.
5. **Six branches versus three agents versus one vertical slice.** B and E are right that a six-way merge at 12:30 from zero code will not happen. A's three-agent split is the widening step, after the slice exists.

### Blind spots the council caught

Things all five advisors missed, each with the fix:

1. **goal_3 and goal_3b have no LLM source.** Every proposed schema emits status/money/post/memory; App Store rating and CFPB complaints would be scripted, which organizers call "not a simulation". Fix: add `app_rating` (1–5 or null when the persona would not rate this week) and `complaint` ∈ {none, bank, cfpb} to the weekly schema; metrics compute goal_3 as the weight-averaged rating of raters and goal_3b as the ratio of weighted CFPB intent in the plan run to the quiet-week (weeks 1–4) nodecision rate, times the 120/month baseline.
2. **nodecision is not silence.** Business as usual sends the migration email seven days before (week 5) and a holding statement within 24h; without them the plan delta is inflated and dishonest. Fix: `world/weeks.json` carries `bau_notices` per week, present in every run with fixed wording; `validate.py` refuses any decision message that is a substring of a BAU notice (otherwise nodecision prompts contain the message and the checker fails).
3. **No invalid-call policy.** The checker needs the status literal inside a response; prior art says defaults bias results. Fix below, under failure policy: retries and model fallback, never a scripted default.
4. **Nobody validates the $4M joint cap, menu levels, SMS per-send cost, the 100k/20k recipient caps.** Fix: `validate.py` with the menu table; a lock file that fails validation does not get uploaded.
5. **probe.jsonl is undesigned** and E's call math omits it. Fix: the organizers' eight fixed questions (1a–4b: trust, staying, recommending, fairness, each in two wordings), one schema call `{q1a..q4b}` at week 0 and week 11, plan_1 and nodecision_1 only. Report week-11-minus-week-0, plan minus nodecision.
6. **"Left" personas still need weekly rows through week 10.** Fix: everyone is called every week; a left persona still posts and can still answer.
7. **Posts rebroadcasting the decision message** (B's catch, confirmed by reviewers): cap posts at 140 chars, instruct "your own words, don't quote the bank", and drop any post containing six consecutive words of a decision message.

### The recommendation

Build E's function with A's clock, B's traps, C's diary-first, and D's `heard_from`.

**Modules** in `code/sim/`: `llm.py` (async google-genai, semaphore 30, JSON schema output, seed plus temperature 0.8, appends every attempt to `calls.jsonl` with id, run, persona_id or null, week, model, prompt, response); `network.py` (seeded graph, k=4 in-group plus one cross-group edge, three bridge nodes, stored as `neighbors[]` inside `personas.jsonl` so it is identical in all runs); `world/weeks.json` plus `apply_decisions()` (deterministic overlay: rate boost, support wait with and without extra support, offline limit, migration state including the overrun update, rival email in week 5, surprises appended from the dashboard); `prompt.py`; `engine.py` (week loop with one barrier per week); `probe.py`; `metrics.py`; `validate.py`; `run_all.sh` (five runs, check.py, zip); `interview.py` (week-10 state plus the board's question, same model).

**Personas:** 30, six per group, all five groups. Each: id, group, `weight_customers`, `weight_deposits` (sum to 2.1M and $6.0B, top 5% holding half), one narrative paragraph, and the attributes that couple to this crisis: paid Friday Dec 11, balance band and above-FDIC flag, second bank, checks app daily, info sources, reaction to bank SMS, financial literacy, P2P use, fraud victim. Prompt encodes friction: moving direct deposit takes a pay cycle.

**Per-persona-week schema:**
```json
{ "status": "main bank|second bank|dormant|left",
  "money": "kept|moved some|moved most",
  "actions": ["logged_in","called_support","moved_direct_deposit","opened_rival_account","withdrew_cash","nothing"],
  "heard_from": "bank|friend|rival|news|none",
  "app_rating": "1-5 or null",
  "complaint": "none|bank|cfpb",
  "feel": "<=20 words", "reason": "1 sentence",
  "post": "<=140 chars or null",
  "diary": "<=3 sentences, first person" }
```
**Prompt:** system = narrative plus attributes plus "small movements, this is one week". User = week facts, BAU notices, decision message verbatim in its own block if targeted and week ≥ W, up to four neighbor posts from week-1, own diary, own ledger of prior (week, status, money) rows, schema. Attention is an attribute, delivery is always verbatim.

**Failure policy:** schema-enforced; accept only if the raw text contains the status literal; retry up to three times with seed+attempt, then fall back to 3.1-flash-lite; every attempt logged; if still failing the run aborts and re-runs. No defaults, ever. **Caching:** none; per-run output directories so nodecision cannot inherit anything. **Concurrency:** 30 per run; call budget 30×10×5 + 30×2×2 = 1,620 calls, roughly three minutes if the quota allows 30-wide, five runs sequential if it does not.

**Roadmap (now 11:58):** 11:58–12:15 human writes `llm.py`, the quota test, `schema.py`, `prompt.md`. 12:15–12:50 one agent builds the vertical slice (engine, prompt, network, world, run.py) in one process while agent two writes 30 personas plus `spec.md` and agent three writes validate/metrics/probe/run_all and loops check.py on fixtures. 12:50–13:20 merge, smoke 8×3, quiet-world test: nodecision weeks 1–4, if more than one persona leaves, the prompt is the crisis. 13:20–13:45 five timed runs, check.py clean, placeholder decision 1 locked (week 5, everyone, honest migration message, offline limit $250, support +50). 13:45–15:00 four candidate bundles × two seeds plus feed-off ablation; final decision 1 locked by 14:50 (week 5 starts 15:00). 15:00–16:00 `interview.py`, deltas table, contagion summary from `heard_from`, both three-line whys drafted. 16:00–16:30 dress rehearsal with a fake surprise file, cold re-run timed. Decision 2 drafted by 15:30 as a week-8 response to the migration weekend (dispute credit, goodwill to affected paycheck customers), locked by 16:25, replaced only if a surprise justifies it, last possible replacement 17:29 for week 10. 17:32 final runs, 17:45 upload. 18:00 the talk: two lines, four colours, a finger on week 6, and Rosa.

**Cut:** dialogues, digest, LLM game master, full-history memory, cache, more than 30 personas, UI, slides beyond one chart.

**Tell the board the sim cannot tell:** levels (LLM personas over-predict by ~20 points; only deltas and rankings are defensible); resolution (30 personas cannot resolve a 2% goal); network topology is assumed, not measured; ratings and complaints are stated intent, not behavior; rivals are scripted; two seeds give variance, not confidence. Next: calibrate against the bank's real churn and complaint data, more seeds, then a real A/B before scaling any decision.

### The one thing to do first

Write `llm.py` as a 40-line async client and fire 30 identical schema calls in parallel at gemini-3.5-flash-lite with seed set, logging wall time and any 429s. If 30-wide works, the whole plan holds; if the quota is 60 RPM, every clock time above is wrong and you need to know by 12:10, not 17:30.
