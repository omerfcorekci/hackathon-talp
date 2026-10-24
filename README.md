# TALP Simulation Lab — Team Repo (Client: Cobalt Bank)

We are a **simulation lab**. Our client, **Cobalt Bank** (a fictional US digital bank), faces ten hard
weeks. We build its customers as **LLM personas**, live through the ten weeks with them, make
**exactly two decisions** on the bank's behalf, and present to the board at **18:30**.

> Source of truth: [`brief/02-challenge.md`](brief/02-challenge.md) (rules),
> [`brief/10-cobalt-bank.md`](brief/10-cobalt-bank.md) (our client),
> [`brief/03-audience-attributes.md`](brief/03-audience-attributes.md) (persona attributes),
> [`brief/check.py`](brief/check.py) (submission checker). If this README and the brief disagree, the brief wins.

**AI agents working in this repo: read [`AGENTS.md`](AGENTS.md) first. Every agent works on its own
branch — never on `main`.**

---

## 1. Today's timeline

| Time | What happens |
|---|---|
| 10:30 | Company draw (we got **Cobalt Bank**) |
| 13:00 | The company calendar starts in real time: **every 30 minutes = one week** |
| 13:00–18:00 | Weeks 1–10 run; surprise crises appear as dashboard announcements at the start of a week |
| **17:30** | Week 10 starts. **Last moment to lock any decision** |
| **18:00** | Hand-in deadline: `team-NN_submission.zip` uploaded on the dashboard |
| 18:30 | Board presentations (5 min talk + 3 min Q&A) |

| Week | Calendar dates | Starts at | Notes |
|---|---|---|---|
| 1 | Nov 2–8 | 13:00 | Baseline (Nov 2 numbers) |
| 2 | Nov 9–15 | 13:30 | |
| 3 | Nov 16–22 | 14:00 | |
| 4 | Nov 23–29 | 14:30 | Thanksgiving, Black Friday |
| 5 | Nov 30–Dec 6 | 15:00 | Migration email notice goes out 7 days before (business as usual) |
| **6** | **Dec 7–13** | **15:30** | **Core banking migration Sat Dec 12 00:00 → Sun Dec 13 12:00 CT**; many paid Fri Dec 11 |
| 7 | Dec 14–20 | 16:00 | |
| 8 | Dec 21–27 | 16:30 | Christmas |
| 9 | Dec 28–Jan 3 | 17:00 | New Year |
| 10 | Jan 4–10 | 17:30 (ends 18:00) | Board goals measured on Jan 10 |

**Implication:** a late announcement can arrive at 17:30, and all five runs must include every
announcement made before 18:00. **The full pipeline (5 runs + probes + zip) must finish in well under
30 minutes.** Design for speed and parallel LLM calls from the start.

---

## 2. Our client in one page: Cobalt Bank

- Digital bank, no branches, Austin TX, founded 2019. Promise: *"Banking with no surprises."*
- **CEO's ask (Elena Ruiz):** keep trust through a forced core-banking migration, keep deposits
  growing, don't buy loyalty with money we don't have, don't stay quiet. *"Tell me what to do, and when."*

**Baseline (Nov 2)**
- 2.1M customers; **1.0M active in the last 30 days**
- **Deposits $6.0B**; ~half belongs to the top 5% of customers
- 310k paycheck customers (no early pay today)
- 42k small businesses with a Cobalt card reader
- App Store rating **4.6**; ~1,800 complaints/month, **~120/month reach the CFPB**
- Savings rate is **0.5 points below** the top three online banks

**Customer groups we can simulate** (must use ≥3, with ≥4 personas each):
everyday customers · paycheck customers · savers with large balances · small business owners with a
Cobalt card reader · students.

**Board goals by January 10** → these become `metrics.json`

| Goal | Target | `metrics.json` key | Owner who cares most |
|---|---|---|---|
| 1. Active customers (30-day) | ≥ 98% of Nov 2 | `goal_1` | Marketing director |
| 2. Deposits | ≥ 97% of Nov 2 | `goal_2` | CFO |
| 3a. App Store rating | ≥ 4.3 | `goal_3` | Chief risk officer |
| 3b. CFPB complaints | ≤ 2× usual (≤ ~240/month) | `goal_3b` | Chief risk officer |
| 4. Budget | both decisions ≤ **$4M** total | (not in metrics) | CFO |

**Red lines** — a decision that crosses any of these is invalid:
- No false or misleading statement to customers.
- The migration date cannot move.
- Rates and fees only at the levels in the menu.
- No layoffs, no closing products.

**Business as usual** (what happens outside our two decisions): 4-minute support wait; card disputes
get provisional credit within 10 business days (investigation up to 45 days); a holding statement on
social media within 24h after any incident; migration email 7 days before.

**Decision menu** (CFO cost estimates — use as given)

| Action | Levels → cost |
|---|---|
| Savings rate boost, 4 weeks, balances ≤ $50k | +0.25pt $0.8M · +0.5pt $1.6M · +0.75pt $2.4M |
| Same boost, new money only | half of the above |
| Instant dispute credit (≤ $100/customer, 8 weeks) | $0.4M |
| Free instant transfers to other banks | 2 weeks $0.1M · 4 weeks $0.2M |
| Debit cash back, 4 weeks | 1% (≤ $5) $1.2M · 2% (≤ $10) $2.2M |
| Goodwill credit to a group (≤ 100k customers) | $5 each $0.5M · $10 each $1M |
| Early pay (≤ 2 days early, permanent, from a chosen week) | $0.5M |
| Zero-interest advance ≤ $500 (≤ 20k customers) | $0.4M |
| Extra support staff, 4 weeks | +50 $0.25M · +150 $0.7M |
| Security pack (free new card + alert on every card payment) | $0.3M |
| Higher offline card limit during migration ($100 → $250) | $0.1M |
| Messages | push / email / in-app free · **SMS to all = $25k per send** · CEO video free (costs credibility) |

**The known crisis (week 6):** for 36 hours the app is read-only (balances visible; no transfers, no
P2P, no new cards). Card payments work offline up to $100 each. The switch may overrun by
"some hours" — nobody knows how many. Rivals know the date.

**Weekly persona status** (`weekly.jsonl`):
- `status`: `main bank` · `second bank` · `dormant` · `left`
- `money` (our own field): `kept` · `moved some` · `moved most`

---

## 3. The two decisions — rules

- Exactly **two** decisions, in any weeks (both in the same week is allowed).
- Locked on the dashboard; takes effect at the **start** of the named week and must be locked
  **before** that week starts. Locking late pushes it to the next unstarted week. Nothing can be
  locked after 17:30.
- A decision can be replaced until its week starts; the last version counts.
- Each decision has:
  - `week`
  - `target`: everyone, or a group we describe
  - `actions`: 1–3 menu actions, each at a listed level (`"level": "on"` if it has no levels)
  - `message`: the exact words (≤ 600 characters) and its `channels`
  - `why`: three lines
- Total cost of both decisions, paid messages included, ≤ **$4M**.
- Must be something a real board would approve: inside the menu, the budget, and the red lines.
- A crisis announced at the start of week N is already happening in week N; the earliest decision
  that can respond is week N+1.

---

## 4. What we must build

1. **Personas** — at least **24**, covering at least **3** dossier groups, at least **4** per group used.
   Choose attributes from the catalog + the dossier's sector attributes; decide values, distributions
   and form (fixed field, narrative line, memory, or changing state). Ground them in public data if we
   can (e.g. Census ACS) and say which. Avoid stereotypes; sensitive traits need a justification.
2. **A world over ten weeks** — what personas see (company messages, news, social media, friends,
   support), what they can do (complain, post, ask a friend, call support, switch, wait…), and how the
   world state changes week to week.
3. **Crises and decisions as inputs** — the same code with a different decision file, or with surprises
   switched off, must produce a different run. Personas read our message **word for word**, only from
   its week on, and only if they are in the decision's target.
4. **Metrics** — how persona behavior maps to the board goals, and how many real customers each
   persona represents (weights).
5. **Experiments** — which decisions we tried, in which weeks, how many times.

**The LLM must produce what personas say, do and decide.** A script that writes the outcome is not a
simulation, and the checks will detect it (every weekly status must trace back to a model response).

**Sanity rule from the organizers:** crises are serious but survivable. If the simulation says half the
customers leave in a week, check the simulation.

### Check-in questions (the "probe")

Ask **every persona** these 8 questions **before week 1 (week 0)** and **after week 10 (week 11)**, in
runs `plan_1` and `nodecision_1`. Scores are integers 1–5, stored exactly as given (2b and 4b are
reverse-worded on purpose). One call per persona for all eight is allowed.

| | Wording a | Wording b |
|---|---|---|
| 1 Trust | How much do you trust Cobalt Bank? | "I can count on Cobalt Bank to treat me right." |
| 2 Staying | How likely are you to keep using Cobalt Bank over the next three months? | "I am thinking about leaving Cobalt Bank." |
| 3 Recommending | How likely are you to recommend Cobalt Bank to a friend or colleague? | If a friend asked you about Cobalt Bank today, what would you tell them? |
| 4 Fairness | How fairly has Cobalt Bank treated you? | "Cobalt Bank takes advantage of people like me." |

Full scale wording is in [`brief/02-challenge.md`](brief/02-challenge.md#the-check-in-questions).

---

## 5. What we hand in (by 18:00)

One ZIP, `team-NN_submission.zip`:

```
team-NN_submission.zip
  CLIENT_MEMO.md        one page for the board
  TEAM_DOC.md           how we built it
  code/                 our code
  runs/
    plan_1/  plan_2/  nodecision_1/  nodecision_2/  plan_nosurprises/
      run.json  personas.jsonl  calls.jsonl  weekly.jsonl  metrics.json
      probe.jsonl       (plan_1 and nodecision_1 only)
```

| Run | Decisions | Surprises | Seed |
|---|---|---|---|
| `plan_1` | our two locked decisions | on | seed A |
| `plan_2` | our two locked decisions | on | seed B |
| `nodecision_1` | none (business as usual) | on | seed A |
| `nodecision_2` | none (business as usual) | on | seed B |
| `plan_nosurprises` | our two locked decisions | **off** (known migration crisis stays) | one seed |

All five runs: the **same personas**, every announcement made before 18:00, and the **Vertex AI key**
we were given.

### File formats (UTF-8; `.jsonl` = one JSON object per line)

- **`run.json`** — `company: "cobalt"`, `type` (`plan` | `nodecision` | `plan_nosurprises`), `seed`,
  `model`, `decisions` (exactly as locked; `[]` in `nodecision` runs). Each decision: `week`, `target`,
  `actions` (`[{action, level}]`), `message`, `channels`, `why`.
- **`personas.jsonl`** — one line per persona: `id`, `group` (a dossier group), plus anything else we
  use. Identical file in all five runs.
- **`calls.jsonl`** — every LLM call: `id`, `persona` (id or `null`), `week` (0 = before week 1,
  1–10, 11 = after week 10), `prompt` (full text sent), `response` (full text received), `model`.
- **`weekly.jsonl`** — one line per persona per week 1–10: `persona`, `week`, `status`
  (`main bank` | `second bank` | `dormant` | `left`), `call` (id of the call whose response contains
  that status, e.g. last line `Status: second bank`), plus `money` and anything else.
- **`metrics.json`** — `goal_1`, `goal_2`, `goal_3`, `goal_3b` and `units`, e.g.
  `{"units": {"goal_1": "% of Nov 2 30-day active customers", ...}}`.
- **`probe.jsonl`** — one line per answer: `persona`, `when` (`start` | `end`), `question`
  (`1a`…`4b`), `score` (1–5), `call` (a call in week 0 for `start`, week 11 for `end`).

### The two documents

- **`CLIENT_MEMO.md`** (one page, for the board): what we decided and why · what the simulation says ·
  what it cannot tell · what the company should watch next.
- **`TEAM_DOC.md`**: personas and why those attributes (used / left out) · the world · how we read each
  crisis · experiments · problems we hit and how we solved them · what we would do with more time.

### Always validate before uploading

```bash
python3 brief/check.py team-NN_submission.zip
```

`code/scripts/make_submission.sh NN` builds the ZIP from `CLIENT_MEMO.md`, `TEAM_DOC.md`, `code/` and
`runs/`, then runs the checker.

---

## 6. Vertex AI usage

```bash
pip install -r code/requirements.txt
export TALP_KEY=<our key>          # never in code, never in git, never in the ZIP
export SSL_CERT_FILE=/etc/ssl/cert.pem   # macOS python.org Python, if CERTIFICATE_VERIFY_FAILED
```

- `genai.Client(vertexai=True, api_key=os.environ["TALP_KEY"])` — **no** project, **no** location
  (setting `us-central1` gives a 404; 2.5 models give a 404 too).
- Fast, no-thinking models for persona calls: `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite` (~1s/call).
  Thinking models (`gemini-3.5-flash`, …) take 3–5s; the slowest take 5–20s.
- Pass the run's `seed` and `temperature > 0` on every call so the two seeds really differ.
- Get parseable output: a final `Status: ...` line, or JSON via `response_mime_type="application/json"`
  + `response_schema`.
- Run calls **in parallel** (threads or `client.aio`); sequential calls will not finish in time.
- `check.py` flags anything that looks like the key (`AQ.` + 40 chars) anywhere in the ZIP.

---

## 7. How we are judged

The simulated outcome is **not** what is scored, and there is no right answer. The jury scores:

1. Our **reasoning**
2. An **idea of our own**
3. How we **compared approaches** and what we learned
4. A **working example** — the board will pick one of our personas and **ask it a question live**
5. What the simulation **cannot tell yet**, and what we would do next

Model brand, persona count and slide polish earn no extra points.

---

## 8. Repository structure

```
hackathon-talp/
├── README.md                  this file: what the hackathon asks + how we work
├── AGENTS.md                  rules for AI agents (branch-per-task workflow)
├── CLAUDE.md                  points Claude Code to AGENTS.md
├── .env.example               TALP_KEY placeholder (copy to .env, never commit .env)
├── brief/                     organizer material — read-only
│   ├── 02-challenge.md
│   ├── 03-audience-attributes.md
│   ├── 10-cobalt-bank.md
│   └── check.py
├── docs/                      working notes that feed TEAM_DOC.md and CLIENT_MEMO.md
│   ├── crisis-log.md          every dashboard announcement + how we read it
│   ├── decisions-log.md       candidate decisions, budget math, what we locked and when
│   └── experiments.md         experiment log (decision × week × seeds × results)
├── code/                      → zipped as code/
│   ├── requirements.txt
│   ├── sim/                   simulation package: LLM client, personas, world, metrics, writers
│   ├── config/
│   │   ├── decisions/         plan.example.json (schema only), plan.json (our two locked
│   │   │                      decisions, created when we lock), nodecision.json ([])
│   │   └── surprises/         one JSON file per dashboard announcement, as it arrives
│   ├── personas/              persona spec + generated personas.jsonl (same in every run)
│   └── scripts/               run / package helpers (make_submission.sh)
├── runs/                      → zipped as runs/ — ONLY the five official runs
│   ├── plan_1/  plan_2/  nodecision_1/  nodecision_2/  plan_nosurprises/
├── experiments/               scratch runs for comparing decisions — NOT zipped, not committed
├── CLIENT_MEMO.md             → zipped
└── TEAM_DOC.md                → zipped
```

The repo root mirrors the ZIP root, so packaging is just "zip these four things".

---

## 9. How we work: one branch per agent task

- `main` is always in a working state. **Nobody — human or agent — commits directly to `main`.**
- Every AI agent task runs on **its own branch** (`agent/<area>-<short-task>`, e.g.
  `agent/personas-generate-v1`), ideally in its own git worktree so parallel agents don't collide.
- When the task is done, the agent pushes the branch and opens a pull request; a human reviews and
  squash-merges into `main`.
- History stays clean: one logical change per commit, `<area>: <summary>` messages, rebase instead of
  merge, no "wip" commits, never rewrite `main`.
- Official runs in `runs/` are regenerated only on a dedicated `agent/runs-...` branch.
- Full rules: [`AGENTS.md`](AGENTS.md).

---

## 10. Pre-hand-in checklist

- [ ] ≥ 24 personas, ≥ 3 groups, ≥ 4 per group; same `personas.jsonl` in all five runs
- [ ] Both decisions locked on the dashboard **and** copied word for word into `code/config/decisions/plan.json`
- [ ] Total cost of both decisions (incl. SMS sends) ≤ $4M; inside menu and red lines
- [ ] Decision messages appear word for word in targeted personas' prompts from their week on — never before, never in `nodecision` runs
- [ ] Every surprise announced before 18:00 is in `code/config/surprises/` and in the runs
- [ ] `plan_nosurprises` keeps the migration crisis but drops all surprises
- [ ] Two seeds give different model answers
- [ ] Every weekly status traceable to a model response; probes in `plan_1` and `nodecision_1` (week 0 and 11)
- [ ] `metrics.json` has `goal_1`, `goal_2`, `goal_3`, `goal_3b` and `units`
- [ ] `CLIENT_MEMO.md` (one page) and `TEAM_DOC.md` written
- [ ] No API key anywhere in the ZIP
- [ ] `python3 brief/check.py team-NN_submission.zip` prints "Nothing to fix."
- [ ] A script to interview any persona live for the board Q&A
